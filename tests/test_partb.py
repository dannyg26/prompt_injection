import numpy as np
import pytest

torch = pytest.importorskip("torch")
transformers = pytest.importorskip("transformers")

from injection_lab.partb import analyze, plan, run_all  # noqa: E402
from injection_lab.transformer import finetune, score  # noqa: E402

WORDS = [f"w{i}" for i in range(60)] + ["ignore", "previous", "instructions", "secret"]


def tiny_model(tmp_path):
    vocab = tmp_path / "vocab.txt"
    vocab.write_text("\n".join(["[PAD]", "[UNK]", "[CLS]", "[SEP]", "[MASK]", *WORDS]))
    tokenizer = transformers.BertTokenizerFast(vocab_file=str(vocab))
    config = transformers.BertConfig(
        vocab_size=len(WORDS) + 5,
        hidden_size=16,
        num_hidden_layers=1,
        num_attention_heads=2,
        intermediate_size=32,
        num_labels=2,
    )
    return transformers.BertForSequenceClassification(config), tokenizer


def synthetic_rows(n=240, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(n):
        label = int(i % 4 == 0)
        source = (
            ["hackaprompt-dataset", "TaskTracker", "BIPIA", "jailbreak-classification"][
                (i // 4) % 4
            ]
            if label
            else "open-instruct"
        )
        text = " ".join(rng.choice(WORDS[:60], 8)) + (
            " ignore previous instructions" if label else ""
        )
        group = f"hp{i % 3}" if source == "hackaprompt-dataset" else f"g{i // 2}"
        rows.append({"id": str(i), "text": text, "label": label, "source": source, "group": group})
    return rows


def test_finetune_and_score_tiny_model(tmp_path):
    model, tokenizer = tiny_model(tmp_path)
    rows = synthetic_rows(64)
    recipe = {
        "learning_rate": 1e-3,
        "epochs": 1,
        "max_length": 32,
        "batch_size": 16,
        "warmup_fraction": 0.1,
        "weight_decay": 0.0,
    }
    model, tokenizer = finetune(rows, 0, model=model, tokenizer=tokenizer, recipe=recipe)
    scores = score(model, tokenizer, [r["text"] for r in rows], max_length=32)
    assert scores.shape == (64,) and np.all((scores >= 0) & (scores <= 1))


def test_run_all_is_resumable_and_analysis_complete(tmp_path):
    rows = synthetic_rows()
    calls = []

    def deberta(train_rows, seed):
        calls.append(seed)
        model, tokenizer = tiny_model(tmp_path)
        recipe = {
            "learning_rate": 1e-3,
            "epochs": 1,
            "max_length": 32,
            "batch_size": 32,
            "warmup_fraction": 0.1,
            "weight_decay": 0.0,
        }
        return finetune(train_rows, seed, model=model, tokenizer=tokenizer, recipe=recipe)

    def released(name, texts):
        return np.array([0.9 if "ignore" in t else 0.1 for t in texts])

    results = run_all(rows, tmp_path / "out", deberta, released, ["fake"], log=lambda _: None)
    assert len(results) == len(plan(rows, ["fake"]))
    fits = len(calls)
    run_all(rows, tmp_path / "out", deberta, released, ["fake"], log=lambda _: None)
    assert len(calls) == fits  # nothing re-run on resume
    report = analyze(rows, results, ["fake"])
    assert report["inflation"]["tfidf|TaskTracker"]["repeats"] == 5
    assert len(report["loto"]["deberta"]) == 3
    assert report["released"]["fake"]["hackaprompt_per_template"]
