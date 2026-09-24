"""Data-only audit: overlap between the InjecGuard training/validation release and its own
evaluation files, plus within-source template concentration. No model is involved.

Containment of an evaluation item in a training row = share of the evaluation item's word
5-gram shingles present in that single row (whole normalized text if shorter than 5 words).
"""

import json
from collections import Counter
from pathlib import Path

import numpy as np

from injection_lab.curation import components, normalized
from injection_lab.data import file_sha256, write_json
from injection_lab.pools import (
    CONTAINMENT_CUTOFF,
    INJECGUARD_REVISION,
    containment_edges,
    shingle_matrix,
)

ROOT = Path("data/raw/injecguard/datasets")
OUT = Path("results/audit/benchmark_overlap.json")
LEVELS = (0.5, 0.8, 1.0)


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def eval_sets():
    sets = {"WildGuard (benign)": [r["prompt"] for r in load("wildguard.json")]}
    for name in ("BIPIA_text", "BIPIA_code"):
        sets[f"{name} (injection)"] = [t for v in load(f"{name}.json").values() for t in v]
    for part in ("one", "two", "three"):
        sets[f"NotInject_{part} (benign)"] = [r["prompt"] for r in load(f"NotInject_{part}.json")]
    return sets


def containment(queries, reference):
    """Per query: max containment in any single reference row, and exact-match flag."""
    matrix = shingle_matrix(queries + reference)
    q, r = matrix[: len(queries)], matrix[len(queries) :].T.tocsr()
    sizes = np.asarray(q.sum(axis=1)).ravel()
    best = np.zeros(len(queries))
    for start in range(0, len(queries), 200):
        shared = (q[start : start + 200] @ r).tocsr()
        for i in range(shared.shape[0]):
            row = shared.getrow(i)
            if row.nnz:
                best[start + i] = row.data.max() / sizes[start + i]
    reference_texts = {normalized(t) for t in reference}
    exact = np.array([normalized(t) in reference_texts for t in queries])
    return best, exact


def summarize(best, exact):
    return {
        "items": int(len(best)),
        "exact_normalized_match": int(exact.sum()),
        **{f"containment_ge_{level}": int((best >= level - 1e-12).sum()) for level in LEVELS},
    }


def template_concentration(rows):
    edges = containment_edges([r["prompt"] for r in rows])
    groups = components(len(rows), edges)
    group_of = {}
    for g, members in enumerate(groups):
        for i in members:
            group_of[i] = g
    table = {}
    for source in sorted({r["source"] for r in rows}):
        for label in (0, 1):
            idx = [i for i, r in enumerate(rows) if r["source"] == source and r["label"] == label]
            if not idx:
                continue
            sizes = Counter(group_of[i] for i in idx)
            largest = sizes.most_common(1)[0][1]
            table[f"{source}|{label}"] = {
                "rows": len(idx),
                "groups": len(sizes),
                "largest_group_rows": largest,
                "largest_group_share": largest / len(idx),
            }
    return table


def main():
    if OUT.exists():
        raise ValueError("Refusing to overwrite audit output")
    train = load("train.json")
    valid = load("valid.json")
    train_texts = [r["prompt"] for r in train]
    valid_texts = [r["prompt"] for r in valid]
    report = {
        "status": "fixed-corpus data audit; no model fitted or scored",
        "injecguard_revision": INJECGUARD_REVISION,
        "input_sha256": {p.name: file_sha256(p) for p in sorted(ROOT.glob("*.json"))},
        "method": "word 5-gram shingle containment of each evaluation item within a single row",
        "grouping_cutoff": CONTAINMENT_CUTOFF,
        "not_audited": "PINT.json is private (Lakera) and absent from the release",
        "eval_vs_train": {},
        "eval_vs_valid": {},
        "valid_sources": dict(Counter(r.get("source", "unknown") for r in valid)),
    }
    for name, texts in eval_sets().items():
        best, exact = containment(texts, train_texts)
        report["eval_vs_train"][name] = summarize(best, exact)
        best, exact = containment(texts, valid_texts)
        report["eval_vs_valid"][name] = summarize(best, exact)
    report["template_concentration_train"] = template_concentration(train)
    write_json(OUT, report)
    print(json.dumps({k: report[k] for k in ("eval_vs_train", "eval_vs_valid")}, indent=1))


if __name__ == "__main__":
    main()
