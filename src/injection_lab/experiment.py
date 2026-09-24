import importlib.metadata
import json
import platform
from datetime import UTC, datetime
from pathlib import Path

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.pipeline import FeatureUnion, Pipeline

from .data import (
    assert_disjoint,
    file_sha256,
    fingerprint,
    read_rows,
    validate_partition,
    write_json,
    write_jsonl,
)


def build_model(seed, features="combined"):
    available = {
        "word": TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, max_features=30000),
        "char": TfidfVectorizer(
            analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True, max_features=50000
        ),
    }
    if features not in ("word", "char", "combined"):
        raise ValueError("features must be word, char, or combined")
    selected = list(available) if features == "combined" else [features]
    return Pipeline(
        [
            ("features", FeatureUnion([(name, available[name]) for name in selected])),
            (
                "classifier",
                LogisticRegression(class_weight="balanced", max_iter=1000, random_state=seed),
            ),
        ]
    )


def select_threshold(labels, scores, max_fpr):
    if not 0 <= max_fpr <= 1:
        raise ValueError("max-fpr must be between 0 and 1")
    labels, scores = np.asarray(labels), np.asarray(scores)
    if set(labels) != {0, 1}:
        raise ValueError("Validation must include both labels")
    # Include a no-alert operating point; ties favor lower FPR then higher threshold.
    candidates = np.r_[np.nextafter(scores.max(), np.inf), np.unique(scores)]
    choices = []
    for threshold in candidates:
        pred = scores >= threshold
        fpr = float(pred[labels == 0].mean())
        recall = float(pred[labels == 1].mean())
        if fpr <= max_fpr:
            choices.append((recall, -fpr, threshold))
    return float(max(choices)[2])


def wilson(successes, total):
    if not total:
        return None
    z = 1.959963984540054
    p = successes / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    half = z * np.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return [float(center - half), float(center + half)]


def metrics(labels, scores, threshold):
    labels, scores = np.asarray(labels), np.asarray(scores)
    pred = scores >= threshold
    tn, fp, fn, tp = [int(n) for n in confusion_matrix(labels, pred, labels=[0, 1]).ravel()]
    both = len(set(labels)) == 2
    return {
        "n": len(labels),
        "positives": int(labels.sum()),
        "threshold": threshold,
        "confusion_matrix": {"tn": tn, "fp": fp, "fn": fn, "tp": tp},
        "precision": float(precision_score(labels, pred, zero_division=0)),
        "recall": float(recall_score(labels, pred, zero_division=0)),
        "f1": float(f1_score(labels, pred, zero_division=0)),
        "false_positive_rate": fp / (fp + tn) if fp + tn else None,
        "recall_wilson_95": wilson(tp, tp + fn),
        "fpr_wilson_95": wilson(fp, fp + tn),
        "average_precision": float(average_precision_score(labels, scores)) if both else None,
        "roc_auc": float(roc_auc_score(labels, scores)) if both else None,
    }


def similarity_audit(reference, query, cutoff=0.9):
    # Separate audit representation, never fed back into training or threshold selection.
    vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), max_features=50000)
    ref = vectorizer.fit_transform([r["text"] for r in reference])
    hits = []
    for start in range(0, len(query), 128):
        batch = query[start : start + 128]
        similarity = cosine_similarity(vectorizer.transform([r["text"] for r in batch]), ref)
        for row, values in zip(batch, similarity):
            i = int(values.argmax())
            if values[i] >= cutoff:
                hits.append(
                    {
                        "query_id": row["id"],
                        "reference_id": reference[i]["id"],
                        "cosine_similarity": float(values[i]),
                    }
                )
    return {
        "method": "char TF-IDF cosine; reference-only vocabulary",
        "cutoff": cutoff,
        "flagged_count": len(hits),
        "pairs": hits,
    }


def score_partition(model, rows, threshold):
    scores = model.predict_proba([r["text"] for r in rows])[:, 1]
    result = metrics([r["label"] for r in rows], scores, threshold)
    result["all_benign_reference"] = metrics([r["label"] for r in rows], np.zeros(len(rows)), 0.5)
    result["slices"] = {}
    for key in ("source", "family"):
        for value in sorted({r.get(key, "unknown") for r in rows}):
            indices = [i for i, r in enumerate(rows) if r.get(key, "unknown") == value]
            result["slices"][f"{key}:{value}"] = metrics(
                [rows[i]["label"] for i in indices], scores[indices], threshold
            )
    predictions = [
        {
            "id": r["id"],
            "label": r["label"],
            "score": float(s),
            "prediction": int(s >= threshold),
            "source": r["source"],
        }
        for r, s in zip(rows, scores)
    ]
    return result, predictions


def fresh_directory(path):
    path = Path(path)
    if path.exists() and any(path.iterdir()):
        raise ValueError(f"Output directory must be empty: {path}")
    path.mkdir(parents=True, exist_ok=True)
    return path


def train(data, out, seed=42, max_fpr=0.05, features="combined"):
    if not 0 <= max_fpr <= 1:
        raise ValueError("max-fpr must be between 0 and 1")
    rows = read_rows(data)
    splits = {s: [r for r in rows if r["split"] == s] for s in ("train", "validation", "test")}
    for name, subset in splits.items():
        validate_partition(subset, name)
    for a, b in (("train", "validation"), ("train", "test"), ("validation", "test")):
        assert_disjoint(splits[a], splits[b], f"{a}/{b}")
    out = fresh_directory(out)
    model = build_model(seed, features)
    model.fit([r["text"] for r in splits["train"]], [r["label"] for r in splits["train"]])
    val_scores = model.predict_proba([r["text"] for r in splits["validation"]])[:, 1]
    threshold = select_threshold([r["label"] for r in splits["validation"]], val_scores, max_fpr)
    development = splits["train"] + splits["validation"]
    metadata = {
        "created_utc": datetime.now(UTC).isoformat(),
        "seed": seed,
        "python": platform.python_version(),
        "versions": {
            p: importlib.metadata.version(p) for p in ("scikit-learn", "numpy", "joblib", "pyarrow")
        },
        "dataset_sha256": file_sha256(data),
        "threshold": threshold,
        "features": features,
        "code_sha256": {p.name: file_sha256(p) for p in sorted(Path(__file__).parent.glob("*.py"))},
        "validation_fpr_budget": max_fpr,
        "development_sources": sorted({r["source"] for r in development}),
        "development_hashes": sorted({fingerprint(r["text"]) for r in development}),
        "development_groups": sorted({r["group_id"] for r in development if r.get("group_id")}),
    }
    report = {
        "metadata": metadata,
        "evaluation_kind": "provided held-out test split",
        "limitations": [
            "Text classification is not agent attack-success measurement.",
            "Validation FPR budget is not a test or production guarantee.",
            "Near duplicates and shared source templates may inflate results.",
            "Wilson intervals assume independent examples; templates may violate this.",
        ],
    }
    for name in ("validation", "test"):
        result, predictions = score_partition(model, splits[name], threshold)
        result["similarity_audit"] = similarity_audit(
            splits["train"] if name == "validation" else development, splits[name]
        )
        report[name] = result
        write_jsonl(out / f"{name}_predictions.jsonl", predictions)
    joblib.dump(
        {"model": model, "metadata": metadata, "development_rows": development},
        out / "model.joblib",
    )
    write_json(out / "report.json", report)
    write_json(out / "metadata.json", metadata)
    return report


def evaluate(model_path, data, out, require_new_source=False, require_new_families=False):
    # joblib uses pickle. Only load artifacts you created or otherwise trust.
    bundle = joblib.load(model_path)
    rows = read_rows(data)
    if any(r["split"] != "test" for r in rows):
        raise ValueError("External evaluation accepts only test rows")
    validate_partition(rows, "external test")
    assert_disjoint(bundle["development_rows"], rows, "development/external test")
    metadata = bundle["metadata"]
    shared = sorted(set(metadata["development_sources"]) & {r["source"] for r in rows})
    if require_new_source and shared:
        raise ValueError(f"Source overlap with development data: {shared}")
    if require_new_families:
        development_positive = [r for r in bundle["development_rows"] if r["label"] == 1]
        test_positive = [r for r in rows if r["label"] == 1]
        if any(
            r.get("family", "unknown") == "unknown" for r in development_positive + test_positive
        ):
            raise ValueError("Family holdout requires family annotations for all positive rows")
        shared_families = {r["family"] for r in development_positive} & {
            r["family"] for r in test_positive
        }
        if shared_families:
            raise ValueError(f"Positive family overlap: {sorted(shared_families)}")
    out = fresh_directory(out)
    result, predictions = score_partition(bundle["model"], rows, metadata["threshold"])
    result.update(
        {
            "evaluation_kind": "source-held-out" if not shared else "same-source external",
            "shared_sources": shared,
            "family_holdout_checked": require_new_families,
            "model_sha256": file_sha256(model_path),
            "dataset_sha256": file_sha256(data),
            "similarity_audit": similarity_audit(bundle["development_rows"], rows),
            "limitations": [
                "Distinct source names do not establish independent provenance.",
                "Metrics measure text labels, not agent compromise.",
                "Family checks rely on supplied annotations.",
            ],
        }
    )
    write_json(out / "report.json", result)
    write_jsonl(out / "predictions.jsonl", predictions)
    return result


def predict(model_path, text):
    if not text.strip():
        raise ValueError("Input text is empty")
    bundle = joblib.load(model_path)
    score = float(bundle["model"].predict_proba([text])[0, 1])
    threshold = bundle["metadata"]["threshold"]
    return {
        "score": score,
        "threshold": threshold,
        "flagged": score >= threshold,
        "note": "Model score is not a calibrated probability of a successful attack.",
    }


def print_summary(report):
    result = report.get("test", report)
    fields = ("n", "precision", "recall", "f1", "false_positive_rate", "average_precision")
    print(json.dumps({k: result[k] for k in fields if k in result}, indent=2))
