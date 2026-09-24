"""Build grouped S/T/U pools from the pinned InjecGuard release. No model is involved."""

import csv
import gzip
import io
import subprocess
from pathlib import Path

from injection_lab.data import file_sha256, write_json, write_jsonl
from injection_lab.pools import (
    COMPONENTS,
    EXCLUDED_REASON,
    INJECGUARD_REVISION,
    build_pools,
    load_injecguard,
)

CLONE = Path("data/raw/injecguard")
POOLS = Path("data/processed/study/pools.jsonl")
LEDGER = Path("results/study/pool_ledger.json")
MANIFEST = Path("results/study/pool_manifest.csv.gz")
INPUTS = ("train.json", "NotInject_one.json", "NotInject_two.json", "NotInject_three.json")
INPUTS += ("wildguard.json",)


def main():
    if LEDGER.exists() or POOLS.exists():
        raise ValueError("Refusing to overwrite frozen study pools")
    head = subprocess.run(
        ["git", "-C", str(CLONE), "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()
    if head != INJECGUARD_REVISION:
        raise AssertionError(f"InjecGuard clone is at {head}, expected {INJECGUARD_REVISION}")
    rows, excluded = load_injecguard(CLONE)
    kept, ledger, removed = build_pools(rows)
    kept.sort(key=lambda r: r["id"])
    write_jsonl(POOLS, kept)
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["id", "text_sha256", "source", "domain", "label", "group", "partition"])
    for r in kept:
        writer.writerow(
            [r["id"], r["sha"], r["source"], r["domain"], r["label"], r["group"], r["partition"]]
        )
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST, "wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as gz:
        gz.write(buffer.getvalue().encode("utf-8"))
    ledger.update(
        {
            "status": "fixed-corpus counts; no model was fitted or scored to build these pools",
            "input_sha256": {name: file_sha256(CLONE / "datasets" / name) for name in INPUTS},
            "admitted_components": {
                k: {"domain": d, "license": lic} for k, (d, lic) in COMPONENTS.items()
            },
            "excluded_components_rows": excluded,
            "excluded_reason": EXCLUDED_REASON,
            "removed_ids": removed,
            "pools_sha256": file_sha256(POOLS),
            "manifest_sha256": file_sha256(MANIFEST),
            "code_sha256": {p: file_sha256(p) for p in ("src/injection_lab/pools.py", __file__)},
        }
    )
    write_json(LEDGER, ledger)
    print(f"{len(kept)} rows; pools sha256 {ledger['pools_sha256']}")


if __name__ == "__main__":
    main()
