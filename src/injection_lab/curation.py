"""Deterministic lexical deduplication, used before any model fitting.

This establishes disjointness under declared lexical rules, not semantic independence.
"""

import hashlib
import unicodedata
from collections import defaultdict
from difflib import SequenceMatcher

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import train_test_split

from .data import fingerprint

SEEDS = (17, 29, 42, 71, 101)
COSINE_CUTOFF = 0.90
EDIT_CUTOFF = 0.90


def normalized(text):
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def components(n, edges):
    parent = list(range(n))

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i, j in edges:
        a, b = root(i), root(j)
        parent[max(a, b)] = min(a, b)
    groups = defaultdict(list)
    for i in range(n):
        groups[root(i)].append(i)
    return sorted(groups.values(), key=lambda group: group[0])


def group_id(rows, indices):
    content = "\n".join(sorted(fingerprint(rows[i]["text"]) for i in indices))
    return "lexical:" + hashlib.sha256(content.encode()).hexdigest()


def collapse(rows, edges):
    retained, ledger, quarantined = [], [], []
    for members in components(len(rows), edges):
        gid = group_id(rows, members)
        # Representative choice uses content hash only, never label, split, or score.
        representative = min(members, key=lambda i: (fingerprint(rows[i]["text"]), rows[i]["id"]))
        conflict = len({rows[i]["label"] for i in members}) > 1
        entry = {
            "group_id": gid,
            "member_ids": [rows[i]["id"] for i in members],
            "size": len(members),
            "label_conflict": conflict,
            "representative_id": None if conflict else rows[representative]["id"],
        }
        ledger.append(entry)
        if conflict:
            quarantined.extend(dict(rows[i], group_id=gid) for i in members)
        else:
            retained.append(dict(rows[representative], group_id=gid))
    retained.sort(key=lambda r: (fingerprint(r["text"]), r["id"]))
    return retained, ledger, quarantined


def split_rows(rows, seed):
    # Match the previous split proportions, not the old test membership.
    development, test = train_test_split(
        rows, test_size=116 / 662, random_state=seed, stratify=[r["label"] for r in rows]
    )
    training, validation = train_test_split(
        development,
        test_size=110 / 546,
        random_state=seed,
        stratify=[r["label"] for r in development],
    )
    return [
        dict(r, split=name)
        for name, subset in (("train", training), ("validation", validation), ("test", test))
        for r in subset
    ]


def cosine_edges(reference, query=None, normalize=False):
    def text(row):
        return normalized(row["text"]) if normalize else row["text"]

    vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), max_features=50000)
    matrix = vectorizer.fit_transform([text(r) for r in reference])
    query_matrix = matrix if query is None else vectorizer.transform([text(r) for r in query])
    values = cosine_similarity(query_matrix, matrix)
    for i, j in zip(*np.where(values >= COSINE_CUTOFF)):
        if query is not None or i < j:
            yield int(i), int(j), float(values[i, j])


def cross_split_edges(rows):
    """Reproduce vocabulary-dependent train/validation/test cosine checks."""
    train = [r for r in rows if r["split"] == "train"]
    validation = [r for r in rows if r["split"] == "validation"]
    test = [r for r in rows if r["split"] == "test"]
    for reference, query in ((train, validation), (train + validation, test)):
        for normalize in (False, True):
            for i, j, value in cosine_edges(reference, query, normalize):
                yield query[i]["id"], reference[j]["id"], value


def curate(rows, seeds=SEEDS):
    if len({r["id"] for r in rows}) != len(rows):
        raise ValueError("IDs must be unique")
    edges, reasons = set(), []

    def add(i, j, method, score):
        key = tuple(sorted((i, j)))
        if key not in edges:
            edges.add(key)
            reasons.append(
                {
                    "left": rows[key[0]]["id"],
                    "right": rows[key[1]]["id"],
                    "method": method,
                    "similarity": score,
                }
            )

    texts = [normalized(r["text"]) for r in rows]
    exact = defaultdict(list)
    for i, text in enumerate(texts):
        exact[text].append(i)
    for members in exact.values():
        for i in members[1:]:
            add(members[0], i, "normalized_exact", 1.0)
    for normalize in (False, True):
        for i, j, value in cosine_edges(rows, normalize=normalize):
            add(i, j, f"global_char_tfidf_normalize_{normalize}", value)
    # Exact all-pairs lexical pass is feasible for this small starter dataset.
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            a, b = texts[i], texts[j]
            if 2 * min(len(a), len(b)) / (len(a) + len(b)) < EDIT_CUTOFF:
                continue
            matcher = SequenceMatcher(None, a, b, autojunk=False)
            if matcher.quick_ratio() < EDIT_CUTOFF:
                continue
            score = max(matcher.ratio(), SequenceMatcher(None, b, a, autojunk=False).ratio())
            if score >= EDIT_CUTOFF:
                add(i, j, "sequence_match", score)
    lookup = {r["id"]: i for i, r in enumerate(rows)}
    # Similarity depends on the reference vocabulary. Close the graph under each
    # prespecified split's audit before training; only text and split IDs are used.
    for iteration in range(len(rows)):
        retained, ledger, quarantined = collapse(rows, edges)
        count_before = len(edges)
        for seed in seeds:
            split = split_rows(retained, seed)
            for a, b, value in cross_split_edges(split):
                add(lookup[a], lookup[b], f"split_vocabulary_seed_{seed}", value)
        if len(edges) == count_before:
            break
    else:
        raise RuntimeError("Deduplication did not converge")
    splits = {seed: split_rows(retained, seed) for seed in seeds}
    for seed, split in splits.items():
        if list(cross_split_edges(split)):
            raise AssertionError(f"Residual cross-split similarity for seed {seed}")
        assignments = defaultdict(set)
        for row in split:
            assignments[row["group_id"]].add(row["split"])
        if any(len(names) != 1 for names in assignments.values()):
            raise AssertionError("A duplicate group spans partitions")
    audit = {
        "normalization": "NFKC + casefold + whitespace collapse (dedup only)",
        "cosine_cutoff": COSINE_CUTOFF,
        "sequence_match_cutoff": EDIT_CUTOFF,
        "seeds": list(seeds),
        "closure_iterations": iteration + 1,
        "input_rows": len(rows),
        "retained_rows": len(retained),
        "exact_redundant_rows": sum(len(v) - 1 for v in exact.values()),
        "quarantined_rows": len(quarantined),
        "redundant_rows_removed": len(rows) - len(retained) - len(quarantined),
        "components": ledger,
        "edges": reasons,
        "limitations": [
            "Lexical checks do not establish semantic independence.",
            "Connected-component transitivity can over-group distinct examples.",
            "Mixed-label components are quarantined pending human adjudication.",
            "Cleanup used text previously seen during exploratory testing.",
        ],
    }
    return splits, audit, quarantined
