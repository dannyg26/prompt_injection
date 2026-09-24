"""Count/provenance audit of pinned files; no detector training or scoring."""

import json
from collections import Counter, defaultdict
from pathlib import Path

from injection_lab.data import file_sha256, fingerprint


def main():
    root = Path("artifacts/research_audit")
    ig_path = root / "injec_train.json"
    ig = json.loads(ig_path.read_text(encoding="utf-8"))
    lookup = defaultdict(list)
    for index, row in enumerate(ig):
        lookup[fingerprint(row["prompt"])].append((index, row["label"], row["source"]))
    report = {
        "status": "fixed-corpus audit counts, no performance estimates",
        "normalization": "NFKC + casefold + whitespace collapse + SHA256",
        "code_sha256": file_sha256(__file__),
        "input_sha256": {str(ig_path): file_sha256(ig_path)},
        "injec_counts_by_source_label": {},
        "promptshield_splits": [],
    }
    for source in sorted({r["source"] for r in ig}):
        report["injec_counts_by_source_label"][source] = dict(
            Counter(str(r["label"]) for r in ig if r["source"] == source)
        )
    for split in ("train", "validation", "test"):
        path = root / f"promptshield_{split}.json"
        report["input_sha256"][str(path)] = file_sha256(path)
        rows = json.loads(path.read_text(encoding="utf-8"))
        overlaps = [
            (i, fingerprint(r["prompt"]), r["label"])
            for i, r in enumerate(rows)
            if fingerprint(r["prompt"]) in lookup
        ]
        report["promptshield_splits"].append(
            {
                "split": split,
                "n": len(rows),
                "normalized_unique": len({fingerprint(r["prompt"]) for r in rows}),
                "overlapping_rows_with_injec_train": len(overlaps),
                "distinct_overlap_texts": len({h for _, h, _ in overlaps}),
                "label_conflict_rows": sum(
                    any(int(label) != int(other) for _, other, _ in lookup[h])
                    for _, h, label in overlaps
                ),
                "injec_sources": dict(
                    Counter(source for _, h, _ in overlaps for _, _, source in lookup[h])
                ),
            }
        )
    path = Path("results/planning/provenance_counts.json")
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("Updated provenance ledger with reproducible script and input hashes.")


if __name__ == "__main__":
    main()
