"""Frozen embedding sensitivity on legacy data; no classifier experiment."""

import hashlib
import importlib.metadata
import json
from pathlib import Path

import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

from injection_lab.curation import SEEDS, collapse, split_rows
from injection_lab.data import file_sha256, read_rows, write_json, write_jsonl

THRESHOLDS = (0.85, 0.90, 0.95)  # Prespecified sensitivity grid; not selected from outcomes.


def embed(rows, directory):
    tokenizer = Tokenizer.from_file(str(directory / "tokenizer.json"))
    tokenizer.enable_truncation(max_length=256, stride=32)
    tokenizer.enable_padding(pad_id=0, pad_token="[PAD]")
    options = ort.SessionOptions()
    options.intra_op_num_threads = 4
    options.inter_op_num_threads = 1
    session = ort.InferenceSession(
        str(directory / "model.onnx"), options, providers=["CPUExecutionProvider"]
    )
    vectors, chunk_counts = [], []
    for start in range(0, len(rows), 16):
        encoded = tokenizer.encode_batch([r["text"] for r in rows[start : start + 16]])
        for item in encoded:
            chunks = [item, *item.overflowing]
            pooled = []
            weights = []
            for chunk in chunks:
                inputs = {
                    "input_ids": np.array([chunk.ids], dtype=np.int64),
                    "attention_mask": np.array([chunk.attention_mask], dtype=np.int64),
                    "token_type_ids": np.array([chunk.type_ids], dtype=np.int64),
                }
                token_vectors = session.run(None, inputs)[0][0]
                mask = np.asarray(chunk.attention_mask, dtype=np.float32)
                pooled.append((token_vectors * mask[:, None]).sum(0) / mask.sum())
                weights.append(mask.sum())
            doc = np.average(np.stack(pooled), axis=0, weights=weights)
            vectors.append(doc / np.linalg.norm(doc))
            chunk_counts.append(len(chunks))
        print(f"Embedded {min(start + 16, len(rows))}/{len(rows)}", flush=True)
    return np.stack(vectors), chunk_counts


def main():
    output = Path("results/semantic")
    output.mkdir(parents=True, exist_ok=True)
    if (output / "sensitivity.json").exists():
        raise ValueError("Refusing to overwrite completed sensitivity results")
    path = Path("data/processed/repaired/seed-42.jsonl")
    rows = sorted(read_rows(path), key=lambda r: r["id"])
    model_dir = Path("artifacts/semantic_model")
    vectors, chunk_counts = embed(rows, model_dir)
    np.save(model_dir / "legacy_embeddings.npy", vectors)
    similarities = vectors @ vectors.T
    summaries = []
    for cutoff in THRESHOLDS:
        ixs, jxs = np.where(np.triu(similarities >= cutoff, 1))
        edges = set(zip(ixs.tolist(), jxs.tolist()))
        retained, components, quarantine = collapse(rows, edges)
        label = f"{cutoff:.2f}"
        for r in retained:
            r["group_id"] = "semantic-" + label + ":" + r["group_id"]
        comparisons = []
        for seed in SEEDS:
            old = read_rows(f"data/processed/repaired/seed-{seed}.jsonl")
            old_split = {r["id"]: r["split"] for r in old}
            new = split_rows(retained, seed)
            new_ids = {r["id"] for r in new}
            comparisons.append(
                {
                    "seed": seed,
                    "cross_split_candidate_edges_before": sum(
                        old_split[rows[i]["id"]] != old_split[rows[j]["id"]] for i, j in edges
                    ),
                    "old_test_ids_removed": sum(
                        r["split"] == "test" and r["id"] not in new_ids for r in old
                    ),
                    "retained_ids_changing_partition": sum(
                        old_split[r["id"]] != r["split"] for r in new
                    ),
                    "new_test_ids_shared_with_old_test": sum(
                        r["split"] == "test" and old_split[r["id"]] == "test" for r in new
                    ),
                    "new_counts": {
                        split: {
                            "n": sum(r["split"] == split for r in new),
                            "positive": sum(r["split"] == split and r["label"] == 1 for r in new),
                        }
                        for split in ("train", "validation", "test")
                    },
                }
            )
            write_jsonl(f"artifacts/semantic_splits/cosine-{label}/seed-{seed}.jsonl", new)
        candidate_pairs = [
            {
                "left_id": rows[i]["id"],
                "right_id": rows[j]["id"],
                "cosine": float(similarities[i, j]),
                "label_conflict": rows[i]["label"] != rows[j]["label"],
            }
            for i, j in sorted(edges)
        ]
        write_json(output / f"candidates-{label}.json", candidate_pairs)
        write_json(output / f"components-{label}.json", components)
        summaries.append(
            {
                "cutoff": cutoff,
                "candidate_pairs": len(edges),
                "retained": len(retained),
                "quarantined": len(quarantine),
                "redundant_removed": len(rows) - len(retained) - len(quarantine),
                "splits": comparisons,
            }
        )
    write_json(
        output / "sensitivity.json",
        {
            "status": "CANDIDATE sensitivity, not human-confirmed semantic deduplication",
            "model_manifest": json.loads((model_dir / "manifest.json").read_text()),
            "input_sha256": file_sha256(path),
            "script_sha256": file_sha256(__file__),
            "embedding_sha256": file_sha256(model_dir / "legacy_embeddings.npy"),
            "record_order_sha256": hashlib.sha256(
                "\n".join(r["id"] for r in rows).encode()
            ).hexdigest(),
            "seeds": list(SEEDS),
            "embedding_seed": None,
            "embedding_reason": "Frozen deterministic CPU ONNX inference, no fitting/sampling",
            "input_n": len(rows),
            "multi_chunk_records": sum(n > 1 for n in chunk_counts),
            "pooling": "attention-masked token mean; token-count-weighted chunk mean; L2 norm",
            "chunking": "256 wordpieces with 32-token overlap; no tail discarded",
            "versions": {
                x: importlib.metadata.version(x) for x in ("onnxruntime", "tokenizers", "numpy")
            },
            "thresholds": summaries,
            "limitations": [
                "High similarity may mean common topic, not equivalent instruction",
                "No human duplicate-pair precision/recall is measured",
                "Long-document pooling can dilute short repeated instructions",
                "Sensitivity splits are not promoted to primary data or used for detector fitting",
                "Counts are a census of this fixed corpus, not estimated population metrics",
                "This audit covers legacy 627 rows only, not the larger candidate pools",
            ],
        },
    )
    print(json.dumps(summaries, indent=2))


if __name__ == "__main__":
    main()
