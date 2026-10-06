"""Export second-annotator (IAA) files for the four owner-labelled audits.

Data only: no detector is loaded and no score is read. For each audit, 50 rows are drawn
uniformly at random (fixed seed) and written WITHOUT the owner's labels or notes to
iaa_<audit>_blind.csv next to the original, in the owner's private Drive folders. The
second annotator labels them with docs/AUDIT_RUBRIC.md without seeing the owner's labels.
Agreement is computed later by the Study 6 analysis, which joins on audit_id.

Usage (Colab, Drive mounted):
    python scripts/export_iaa.py --drive /content/drive/MyDrive
"""

import argparse
import csv
from pathlib import Path

import numpy as np

IAA_SEED = 20261006
IAA_N = 50
# (key, private folder under the Drive root, audit file, label column, text columns)
AUDITS = (
    (
        "S3",
        "study3/private_lmsys_text_do_not_share",
        "audit_A2_blind.csv",
        "is_benign (1/0)",
        ("text",),
    ),
    (
        "S4",
        "study4/private_lmsys_text_do_not_share",
        "audit_B1_blind.csv",
        "is_benign (1/0)",
        ("text",),
    ),
    (
        "W",
        "study5/private_restricted_text_do_not_share",
        "audit_W_blind.csv",
        "is_benign (1/0)",
        ("text",),
    ),
    (
        "Opara",
        "study5/private_restricted_text_do_not_share",
        "audit_Opara_blind.csv",
        "same_meaning_and_benign (1/0)",
        ("original", "paraphrase"),
    ),
)


def read_rows(path):
    import zipfile

    if zipfile.is_zipfile(path):  # an Excel workbook saved under a .csv name
        import pandas as pd

        return pd.read_excel(path, dtype=str).fillna("").to_dict("records")
    with open(path, encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def draw(n_rows, key):
    """Seeded uniform draw of IAA_N row positions, independent of labels and text."""
    rng = np.random.default_rng([IAA_SEED, sum(map(ord, key))])
    return sorted(rng.permutation(n_rows)[: min(IAA_N, n_rows)].tolist())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--drive", required=True)
    args = parser.parse_args()
    root = Path(args.drive)
    for key, folder, name, label, text_cols in AUDITS:
        src = root / folder / name
        rows = read_rows(src)
        picked = [rows[i] for i in draw(len(rows), key)]
        out = root / folder / f"iaa_{name.removeprefix('audit_')}"
        if out.exists():
            print(f"{key}: {out.name} already exists; not overwritten")
            continue
        with open(out, "w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["audit_id", *text_cols, label, "notes"])
            for r in picked:
                writer.writerow([r["audit_id"], *(r[c] for c in text_cols), "", ""])
        print(f"{key}: {len(picked)} of {len(rows)} rows -> {out}")


if __name__ == "__main__":
    main()
