"""Repair the starter data before rerunning any detector. No model is fitted."""

import shutil
from pathlib import Path

from injection_lab.curation import SEEDS, cross_split_edges, curate
from injection_lab.data import file_sha256, read_rows, write_json, write_jsonl


def main():
    original = Path("data/processed/deepset.jsonl")
    archived = Path("data/archive/deepset.pre-repair.jsonl")
    out = Path("data/processed/repaired")
    if archived.exists() or out.exists():
        raise ValueError("Repair already has outputs; do not overwrite the audit")
    rows = read_rows(original)
    original_hash = file_sha256(original)
    # Frozen before fitting: five split seeds, lexical cutoffs, one representative/component.
    splits, audit, quarantine = curate(rows)
    audit["original_sha256"] = original_hash
    audit["original_cross_split_cosine_pairs"] = list(cross_split_edges(rows))
    audit["split_counts"] = {}
    audit["output_sha256"] = {}
    audit["split_method"] = "One row per homogeneous component; stratified 436:110:116 proportions"
    for seed, split in splits.items():
        path = out / f"seed-{seed}.jsonl"
        write_jsonl(path, split)
        audit["output_sha256"][str(seed)] = file_sha256(path)
        audit["split_counts"][str(seed)] = {
            name: {
                "n": sum(r["split"] == name for r in split),
                "positive": sum(r["split"] == name and r["label"] == 1 for r in split),
                "negative": sum(r["split"] == name and r["label"] == 0 for r in split),
            }
            for name in ("train", "validation", "test")
        }
    write_jsonl(out / "quarantined.jsonl", quarantine)
    audit["code_sha256"] = {
        str(path): file_sha256(path)
        for path in (Path(__file__), Path("src/injection_lab/curation.py"))
    }
    write_json("results/repair/deduplication-audit.json", audit)
    archived.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(original, archived)
    if file_sha256(archived) != original_hash:
        raise AssertionError("Archive does not match the original data")
    old_manifest = original.with_suffix(".manifest.json")
    shutil.copyfile(old_manifest, archived.with_suffix(".manifest.json"))
    shutil.copyfile(out / "seed-42.jsonl", original)
    write_json(
        old_manifest,
        {
            "status": "repaired lexical-deduplicated development corpus",
            "seed": 42,
            "all_split_seeds": list(SEEDS),
            "processed_sha256": file_sha256(original),
            "original_sha256": original_hash,
            "audit": "results/repair/deduplication-audit.json",
            "original_manifest": str(archived.with_suffix(".manifest.json")),
        },
    )
    print(
        {
            key: audit[key]
            for key in (
                "input_rows",
                "retained_rows",
                "exact_redundant_rows",
                "quarantined_rows",
                "redundant_rows_removed",
                "closure_iterations",
            )
        }
    )
    print("All prescribed raw/normalized cosine checks and group disjointness checks passed.")


if __name__ == "__main__":
    main()
