"""Download a pinned data snapshot, never executable dataset code."""

import io
import json
import urllib.request
from pathlib import Path

import pyarrow.parquet as pq
from sklearn.model_selection import train_test_split

from .data import file_sha256, fingerprint, write_json, write_jsonl

REPO = "deepset/prompt-injections"


def download(url):
    request = urllib.request.Request(url, headers={"User-Agent": "injection-lab/0.1"})
    with urllib.request.urlopen(request, timeout=90) as response:
        return response.read()


def fetch_deepset(out, raw, seed=42, revision="main"):
    out, raw = Path(out), Path(raw)
    if out.exists():
        raise ValueError(f"Refusing to overwrite {out}; choose a new output path")
    info = json.loads(download(f"https://huggingface.co/api/datasets/{REPO}/revision/{revision}"))
    sha = info["sha"]
    raw = raw / sha
    raw.mkdir(parents=True, exist_ok=True)
    base = f"https://huggingface.co/datasets/{REPO}/resolve/{sha}"
    records, files = [], []
    for entry in info["siblings"]:
        name = entry["rfilename"]
        if not name.endswith(".parquet"):
            continue
        split = Path(name).name.split("-")[0]
        if split not in ("train", "test"):
            continue
        body = download(f"{base}/{name}")
        local = raw / Path(name).name
        local.write_bytes(body)
        files.append({"file": name, "sha256": file_sha256(local)})
        for i, item in enumerate(pq.read_table(io.BytesIO(body)).to_pylist()):
            records.append(
                {
                    "id": f"deepset:{Path(name).stem}:{i}",
                    "text": item["text"],
                    "label": int(item["label"]),
                    "source": REPO,
                    "split": split,
                    "revision": sha,
                }
            )
    if not records or {r["split"] for r in records} != {"train", "test"}:
        raise ValueError("Expected upstream train and test Parquet files")
    # Keep the official test copy when train/test duplicates exist. Never silently resolve labels.
    seen, unique, removed = {}, [], 0
    for row in sorted(records, key=lambda r: r["split"] != "test"):
        key = fingerprint(row["text"])
        if key in seen:
            if seen[key] != row["label"]:
                raise ValueError("Conflicting labels for normalized duplicate text")
            removed += 1
            continue
        seen[key] = row["label"]
        unique.append(row)
    pool = [r for r in unique if r["split"] == "train"]
    train, validation = train_test_split(
        pool, test_size=0.2, random_state=seed, stratify=[r["label"] for r in pool]
    )
    for row in validation:
        row["split"] = "validation"
    test = [r for r in unique if r["split"] == "test"]
    card = download(f"{base}/README.md")
    (raw / "README.md").write_bytes(card)
    write_jsonl(out, train + validation + test)
    manifest = {
        "dataset": REPO,
        "revision": sha,
        "seed": seed,
        "license_on_card": "apache-2.0 (verify upstream card)",
        "files": files,
        "dataset_card_sha256": file_sha256(raw / "README.md"),
        "normalized_duplicates_removed": removed,
        "split_counts": {"train": len(train), "validation": len(validation), "test": len(test)},
        "processed_sha256": file_sha256(out),
    }
    write_json(out.with_suffix(".manifest.json"), manifest)
    return manifest
