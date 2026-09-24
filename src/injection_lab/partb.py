"""Study 2 Part B orchestration: task plan, resumable execution, analysis (Amendment 3)."""

import json
from pathlib import Path

import numpy as np

from .adaptation import fit_detector
from .splitcompare import (
    ATTACK_SOURCES,
    SPLIT_SEED_BASE,
    TEST_FRACTION,
    evaluate_split,
    nadeau_bengio_interval,
    random_group_split,
    recall_at_fpr,
    row_split,
)

PARTB_REPEATS = 5
PRIMARY_SOURCES = ("TaskTracker", "BIPIA", "jailbreak-classification")
TRAINED = ("tfidf", "deberta")


def hackaprompt_groups(rows):
    return sorted(
        {r["group"] for r in rows if r["source"] == "hackaprompt-dataset" and r["label"] == 1}
    )


def plan(rows, released_names):
    tasks = []
    for detector in TRAINED:
        for repeat in range(PARTB_REPEATS):
            for kind in ("row", "group"):
                tasks.append(f"{detector}|{kind}|{repeat}")
        for group in hackaprompt_groups(rows):
            tasks.append(f"{detector}|loto|{group}")
    tasks += [f"released|{name}" for name in released_names]
    return tasks


def split_mask(rows, kind, repeat):
    seed = SPLIT_SEED_BASE + repeat
    return row_split(rows, seed) if kind == "row" else random_group_split(rows, seed)


def loto_mask(rows, group):
    benign = random_group_split(rows, SPLIT_SEED_BASE) & np.array([r["label"] == 0 for r in rows])
    return benign | np.array([r["group"] == group for r in rows])


def train_and_score(detector, train_rows, test_texts, seed, deberta):
    if detector == "tfidf":
        return fit_detector(train_rows).predict_proba(test_texts)[:, 1]
    model, tokenizer = deberta(train_rows, seed)
    from .transformer import score

    return score(model, tokenizer, test_texts)


def run_task(task, rows, deberta, released_scorer):
    """Execute one task; returns a JSON-serializable result (scores kept for released)."""
    parts = task.split("|")
    if parts[0] == "released":
        texts = [r["text"] for r in rows]
        return {"task": task, "scores": released_scorer(parts[1], texts).tolist()}
    detector, kind, key = parts
    mask = loto_mask(rows, key) if kind == "loto" else split_mask(rows, kind, int(key))
    seed = SPLIT_SEED_BASE + (0 if kind == "loto" else int(key))
    train = [r for r, t in zip(rows, mask) if not t]
    texts = [r["text"] for r, t in zip(rows, mask) if t]
    scores = np.full(len(rows), np.nan)
    scores[mask] = train_and_score(detector, train, texts, seed, deberta)
    if kind == "loto":
        labels = np.array([r["label"] for r in rows])[mask]
        recall, _ = recall_at_fpr(scores[mask], labels, labels == 1)
        return {"task": task, "recall_at_1pct_fpr": recall, "rows": int((labels == 1).sum())}
    result = evaluate_split(scores, rows, mask)
    result.update({"task": task, "n_test": int(mask.sum())})
    return result


def run_all(rows, out_dir, deberta, released_scorer, released_names, log=print):
    """Resumable: each finished task is written to out_dir/tasks and skipped on restart."""
    tasks_dir = Path(out_dir) / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    for task in plan(rows, released_names):
        path = tasks_dir / (task.replace("|", "__").replace("/", "_").replace(":", "_") + ".json")
        if path.exists():
            continue
        log(f"running {task}")
        result = run_task(task, rows, deberta, released_scorer)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(_safe(result)), encoding="utf-8")
        tmp.replace(path)
    return {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in tasks_dir.glob("*.json")}


def _safe(value):
    if isinstance(value, dict):
        return {k: _safe(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_safe(v) for v in value]
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def _num(value):
    return np.nan if value is None else float(value)


def analyze(rows, results, released_names):
    by_task = {r["task"]: r for r in results.values()}
    n_test = int(round(TEST_FRACTION * len(rows)))
    report = {"inflation": {}, "design_effect": {}, "loto": {}, "released": {}}
    for detector in TRAINED:
        for source in ("pooled",) + ATTACK_SOURCES:
            key = f"recall_at_1pct_fpr|{source}"
            diffs, row_vals, group_vals = [], [], []
            for repeat in range(PARTB_REPEATS):
                a = by_task.get(f"{detector}|row|{repeat}")
                b = by_task.get(f"{detector}|group|{repeat}")
                if a is None or b is None:
                    continue
                row_vals.append(_num(a.get(key)))
                group_vals.append(_num(b.get(key)))
                diffs.append(row_vals[-1] - group_vals[-1])
            report["inflation"][f"{detector}|{source}"] = {
                "primary": source in PRIMARY_SOURCES,
                "repeats": len(diffs),
                "row_mean": float(np.nanmean(row_vals)) if row_vals else None,
                "group_mean": float(np.nanmean(group_vals)) if group_vals else None,
                "inflation_mean": float(np.nanmean(diffs)) if diffs else None,
                "ci95_nadeau_bengio": nadeau_bengio_interval(diffs, len(rows) - n_test, n_test),
            }
        for source in ATTACK_SOURCES:
            values = [
                _num(by_task[f"{detector}|group|{r}"].get(f"design_effect|{source}"))
                for r in range(PARTB_REPEATS)
                if f"{detector}|group|{r}" in by_task
            ]
            finite = [v for v in values if np.isfinite(v)]
            report["design_effect"][f"{detector}|{source}"] = {
                "median": float(np.median(finite)) if finite else None,
                "range": [min(finite), max(finite)] if finite else None,
                "defined_repeats": len(finite),
            }
        report["loto"][detector] = [
            {"group": g, **{k: by_task[t][k] for k in ("rows", "recall_at_1pct_fpr")}}
            for g in hackaprompt_groups(rows)
            if (t := f"{detector}|loto|{g}") in by_task
        ]
    for name in released_names:
        task = by_task.get(f"released|{name}")
        if task is None:
            continue
        scores = np.array(task["scores"], dtype=float)
        splits = [
            evaluate_split(scores, rows, random_group_split(rows, SPLIT_SEED_BASE + r))
            for r in range(PARTB_REPEATS)
        ]
        per_source = {}
        for source in ("pooled",) + ATTACK_SOURCES:
            vals = [_num(s.get(f"recall_at_1pct_fpr|{source}")) for s in splits]
            per_source[source] = {"mean": float(np.nanmean(vals)), "range": [min(vals), max(vals)]}
        loto = []
        for g in hackaprompt_groups(rows):
            mask = loto_mask(rows, g)
            labels = np.array([r["label"] for r in rows])[mask]
            recall, _ = recall_at_fpr(scores[mask], labels, labels == 1)
            loto.append(
                {"group": g, "rows": int((labels == 1).sum()), "recall_at_1pct_fpr": recall}
            )
        report["released"][name] = {
            "recall_at_1pct_fpr_over_group_splits": per_source,
            "design_effect_median": {
                s: float(np.nanmedian([_num(x.get(f"design_effect|{s}")) for x in splits]))
                for s in ATTACK_SOURCES
                if any(np.isfinite(_num(x.get(f"design_effect|{s}"))) for x in splits)
            },
            "hackaprompt_per_template": loto,
            "note": "No training here; training data of released detectors is partly unknown, "
            "so no inflation is estimated. Overlap with these rows cannot be ruled out.",
        }
    return _safe(report)
