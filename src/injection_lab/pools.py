"""Grouped source/target/untouched pools for the adaptation study.

Built from the pinned InjecGuard GitHub release. Pool construction uses text, labels,
source strings and a fixed seed only; it never uses a model score.
"""

import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy import sparse

from .curation import components, normalized

INJECGUARD_REVISION = "cb1531f36bffb38b6493438217b36cda8875da8a"
PARTITION_SEED = 20260924
SHINGLE = 5
CONTAINMENT_CUTOFF = 0.5
MIN_SHARED = 3
TARGET_BANK_BENIGN = 1000

# Tier A: the component's own card or repository declares a license. Nested upstream terms
# may still be unresolved; see docs/COMPONENT_PROVENANCE_AUDIT.md. Research use only; raw
# text is never committed. Everything not listed here is excluded from the study.
COMPONENTS = {
    "Alpaca": ("S", "CC-BY-NC-4.0 (Stanford Alpaca DATA_LICENSE)"),
    "chatbot_instruction_prompts": ("S", "Apache-2.0 declared; nested parents unresolved"),
    "open-instruct": ("S", "CC-BY-3.0 declared; mixed component terms"),
    "no_robots": ("S", "CC-BY-NC-4.0 (HuggingFaceH4 card)"),
    "ultrachat_200k": ("S", "MIT (HuggingFaceH4 card)"),
    "grok-conversation-harmless": ("S", "Apache-2.0 (HuggingFaceH4 card)"),
    "awesome-chatgpt-prompts": ("S", "CC0-1.0 (fka card)"),
    "hackaprompt-dataset": ("S", "MIT declared; gated access"),
    "jailbreak-classification": ("S", "Apache-2.0 declared; nested parents unresolved"),
    "TaskTracker": ("T", "MIT (microsoft/TaskTracker); SQuAD-derived text CC-BY-SA-4.0"),
    "BIPIA": ("U", "MIT with explicit CC-BY-SA-4.0 component exceptions"),
    "NotInject": ("U", "MIT (leolee99/NotInject card)"),
    "WildGuard": ("U", "ODC-BY declared; gated upstream; benign subset as redistributed"),
}
EXCLUDED_REASON = "no component-level license declaration verified, legacy, or construct mismatch"


def text_sha(text):
    return hashlib.sha256(normalized(text).encode("utf-8")).hexdigest()


def load_injecguard(root):
    """Return (admitted rows, per-source exclusion counts) from a pinned clone."""
    root = Path(root) / "datasets"
    rows, excluded = [], Counter()

    def admit(row_id, text, label, source):
        domain = COMPONENTS[source][0]
        rows.append(
            {
                "id": row_id,
                "text": text,
                "label": int(label),
                "source": source,
                "domain": domain,
                "sha": text_sha(text),
            }
        )

    for i, item in enumerate(json.loads((root / "train.json").read_text(encoding="utf-8"))):
        if item["source"] in COMPONENTS:
            admit(f"injecguard:train:{i}", item["prompt"], item["label"], item["source"])
        else:
            excluded[item["source"]] += 1
    for part in ("one", "two", "three"):
        name = f"NotInject_{part}"
        for i, item in enumerate(json.loads((root / f"{name}.json").read_text(encoding="utf-8"))):
            admit(f"injecguard:{name}:{i}", item["prompt"], 0, "NotInject")
    for i, item in enumerate(json.loads((root / "wildguard.json").read_text(encoding="utf-8"))):
        admit(f"injecguard:wildguard:{i}", item["prompt"], item["label"], "WildGuard")
    return rows, dict(sorted(excluded.items()))


def shingle_matrix(texts, size=SHINGLE):
    vocabulary, indptr, indices = {}, [0], []
    for text in texts:
        tokens = re.findall(r"\w+", normalized(text))
        grams = {" ".join(tokens[i : i + size]) for i in range(len(tokens) - size + 1)}
        if not grams:
            grams = {" ".join(tokens) or normalized(text)}
        indices.extend(sorted(vocabulary.setdefault(g, len(vocabulary)) for g in grams))
        indptr.append(len(indices))
    data = np.ones(len(indices), dtype=np.int32)
    return sparse.csr_matrix((data, indices, indptr), shape=(len(texts), len(vocabulary)))


def containment_edges(texts, cutoff=CONTAINMENT_CUTOFF, min_shared=MIN_SHARED, chunk=400):
    """Pairs whose shared word shingles cover >= cutoff of the smaller shingle set.

    Catches near-duplicates, a clean paragraph inside its poisoned copy, and a payload or
    template reused inside a longer text. Exhaustive: every co-occurring pair is scored.
    """
    matrix = shingle_matrix(texts)
    sizes = np.asarray(matrix.sum(axis=1)).ravel()
    transposed = matrix.T.tocsr()
    edges = set()
    for start in range(0, matrix.shape[0], chunk):
        shared = (matrix[start : start + chunk] @ transposed).tocoo()
        left = shared.row + start
        keep = shared.col > left
        left, right, count = left[keep], shared.col[keep], shared.data[keep]
        smaller = np.minimum(sizes[left], sizes[right])
        ok = (count >= np.minimum(min_shared, smaller)) & (count >= cutoff * smaller)
        edges.update(zip(left[ok].tolist(), right[ok].tolist()))
    return edges


def deduplicate(rows):
    """Collapse same-label exact duplicates; drop every row of a label-conflicting text."""
    by_sha = defaultdict(list)
    for row in rows:
        by_sha[row["sha"]].append(row)
    kept, conflicts, redundant = [], [], 0
    for sha in sorted(by_sha):
        members = sorted(by_sha[sha], key=lambda r: r["id"])
        if len({r["label"] for r in members}) > 1:
            conflicts.extend(r["id"] for r in members)
            continue
        kept.append(members[0])
        redundant += len(members) - 1
    return kept, {"exact_redundant_removed": redundant, "label_conflict_ids": conflicts}


def _group_id(rows, members):
    content = "\n".join(sorted(rows[i]["sha"] for i in members))
    return "g:" + hashlib.sha256(content.encode()).hexdigest()[:20]


def allocate(groups, fractions, rng):
    """Assign whole groups to named partitions, stratified by whether a group has a positive.

    Largest groups are placed first (random tie order) into the partition with the largest
    row deficit, so large template groups cannot unbalance the split.
    """
    names = list(fractions)
    assignment = {}
    for has_positive in (True, False):
        subset = sorted(g for g, pos in groups.items() if pos[0] == has_positive)
        tie = rng.permutation(len(subset))
        order = sorted(range(len(subset)), key=lambda i: (-groups[subset[i]][1], tie[i]))
        total = sum(groups[g][1] for g in subset)
        filled = Counter()
        for index in order:
            gid = subset[index]
            deficits = [fractions[n] * total - filled[n] for n in names]
            name = names[int(np.argmax(deficits))]
            assignment[gid] = name
            filled[name] += groups[gid][1]
    return assignment


def build_pools(rows, seed=PARTITION_SEED, bank_benign=TARGET_BANK_BENIGN):
    rows, dedup = deduplicate(rows)
    edges = containment_edges([r["text"] for r in rows])
    members_list = components(len(rows), edges)
    cross_domain, kept = [], []
    for members in members_list:
        gid = _group_id(rows, members)
        domains = {rows[i]["domain"] for i in members}
        for i in members:
            rows[i]["group"] = gid
            # Evaluation-domain rows sharing a group with another domain are removed; source
            # rows stay in the source domain. This keeps T/U evaluation text out of S.
            if len(domains) > 1 and rows[i]["domain"] != "S":
                cross_domain.append(rows[i]["id"])
            else:
                kept.append(rows[i])
    rng = np.random.default_rng(seed)
    partition = {}

    def summary(domain):
        info = {}
        for row in kept:
            if row["domain"] == domain:
                has_pos, size = info.get(row["group"], (False, 0))
                info[row["group"]] = (has_pos or row["label"] == 1, size + 1)
        return info

    source_groups = summary("S")
    partition.update(
        allocate(
            source_groups,
            {"S-train": 0.55, "S-cal": 0.25, "S-generic-bank": 0.05, "S-test": 0.15},
            rng,
        )
    )
    target_groups = summary("T")
    benign_by_group = Counter(r["group"] for r in kept if r["domain"] == "T" and r["label"] == 0)
    ordered = sorted(target_groups)
    filled = 0
    for index in rng.permutation(len(ordered)):
        gid = ordered[index]
        if filled < bank_benign and benign_by_group[gid]:
            partition[gid] = "T-bank"
            filled += benign_by_group[gid]
        else:
            partition[gid] = "T-eval"
    for gid in summary("U"):
        partition[gid] = "U-eval"
    for row in kept:
        row["partition"] = partition[row["group"]]
        # Only benign rows of the target bank may be revealed; bank positives are discarded.
        if row["partition"] == "T-bank" and row["label"] == 1:
            row["partition"] = "T-bank-discarded-positive"
    ledger = {
        "injecguard_revision": INJECGUARD_REVISION,
        "partition_seed": seed,
        "grouping": {
            "normalization": "NFKC + casefold + whitespace collapse",
            "shingles": f"word {SHINGLE}-grams (whole text if shorter)",
            "edge_rule": (
                f"shared >= min({MIN_SHARED}, smaller set) and "
                f"shared/smaller >= {CONTAINMENT_CUTOFF}; exhaustive sparse co-occurrence"
            ),
            "components": "transitive connected components",
            "edge_count": len(edges),
        },
        "dedup": {
            "exact_redundant_removed": dedup["exact_redundant_removed"],
            "label_conflict_rows_removed": len(dedup["label_conflict_ids"]),
        },
        "cross_domain_rows_removed": len(cross_domain),
        "counts": counts(kept),
        "largest_groups": largest_groups(kept),
    }
    return kept, ledger, {"label_conflict": dedup["label_conflict_ids"], "cross": cross_domain}


def counts(rows):
    table = defaultdict(lambda: {"rows_benign": 0, "rows_positive": 0, "groups": set()})
    for row in rows:
        for key in (row["partition"], f"{row['partition']}|{row['source']}"):
            entry = table[key]
            entry["rows_positive" if row["label"] else "rows_benign"] += 1
            entry["groups"].add(row["group"])
    return {
        key: {
            "rows_benign": v["rows_benign"],
            "rows_positive": v["rows_positive"],
            "groups": len(v["groups"]),
        }
        for key, v in sorted(table.items())
    }


def largest_groups(rows, top=10):
    size = Counter(r["group"] for r in rows)
    result = []
    for gid, n in size.most_common(top):
        members = [r for r in rows if r["group"] == gid]
        result.append(
            {
                "group": gid,
                "rows": n,
                "partition": members[0]["partition"],
                "labels": dict(Counter(str(r["label"]) for r in members)),
                "sources": dict(Counter(r["source"] for r in members)),
            }
        )
    return result


def rows_from_manifest(clone_root, manifest_path):
    """Rebuild frozen pool rows from the committed manifest plus the pinned raw release.

    Uses no grouping computation, so the result is byte-identical across Python versions.
    """
    import csv
    import gzip

    loaded, _ = load_injecguard(clone_root)
    by_id = {r["id"]: r for r in loaded}
    rows = []
    with gzip.open(manifest_path, "rt", encoding="utf-8", newline="") as handle:
        for entry in csv.DictReader(handle):
            base = by_id[entry["id"]]
            if base["sha"] != entry["text_sha256"]:
                raise AssertionError(f"Text hash mismatch for {entry['id']}")
            rows.append(
                {
                    "id": entry["id"],
                    "text": base["text"],
                    "label": int(entry["label"]),
                    "source": entry["source"],
                    "domain": entry["domain"],
                    "sha": entry["text_sha256"],
                    "group": entry["group"],
                    "partition": entry["partition"],
                }
            )
    rows.sort(key=lambda r: r["id"])
    return rows
