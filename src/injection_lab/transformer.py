"""Study 2 Part B: fixed-recipe transformer fine-tuning and scoring (no tuning, no search).

Torch/transformers are imported lazily so the rest of the package stays CPU-light.
Recipe is fixed by Amendment 3 in docs/PREREGISTRATION_LEAKAGE.md.
"""

import numpy as np

FINETUNE_MODEL = "microsoft/deberta-v3-small"
RELEASED_DETECTORS = (
    # (repo id, index of the injection class in the model's output, gated?)
    ("protectai/deberta-v3-base-prompt-injection-v2", "INJECTION", False),
    ("meta-llama/Llama-Prompt-Guard-2-86M", "LABEL_1", True),
)
RECIPE = {
    "learning_rate": 2e-5,
    "epochs": 1,
    "max_length": 256,
    "batch_size": 32,
    "warmup_fraction": 0.06,
    "weight_decay": 0.01,
    "class_weighting": "balanced (inverse frequency), matching the linear detector",
}


def _device():
    import torch

    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def resolve_revision(repo_id, token=None):
    """Pin a Hub repo to its current commit sha, recorded before any fitting or scoring."""
    from huggingface_hub import model_info

    return model_info(repo_id, token=token).sha


def finetune(
    train_rows,
    seed,
    model_name=FINETUNE_MODEL,
    revision=None,
    model=None,
    tokenizer=None,
    recipe=RECIPE,
):
    """Fine-tune a sequence classifier once with the fixed recipe. Returns (model, tokenizer).

    `model`/`tokenizer` may be passed directly (used by the offline smoke test).
    """
    import torch
    from transformers import (
        AutoModelForSequenceClassification,
        AutoTokenizer,
        get_linear_schedule_with_warmup,
    )

    torch.manual_seed(seed)
    np.random.seed(seed)
    if tokenizer is None:
        tokenizer = AutoTokenizer.from_pretrained(model_name, revision=revision)
    if model is None:
        model = AutoModelForSequenceClassification.from_pretrained(
            model_name, revision=revision, num_labels=2
        )
    device = _device()
    model.to(device).train()
    texts = [r["text"] for r in train_rows]
    labels = np.array([r["label"] for r in train_rows])
    counts = np.bincount(labels, minlength=2)
    weights = torch.tensor(len(labels) / (2 * np.maximum(counts, 1)), dtype=torch.float)
    loss_fn = torch.nn.CrossEntropyLoss(weight=weights.to(device))
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=recipe["learning_rate"], weight_decay=recipe["weight_decay"]
    )
    batch = recipe["batch_size"]
    steps = recipe["epochs"] * int(np.ceil(len(texts) / batch))
    scheduler = get_linear_schedule_with_warmup(
        optimizer, int(recipe["warmup_fraction"] * steps), steps
    )
    scaler = torch.amp.GradScaler(enabled=device.type == "cuda")
    rng = np.random.default_rng(seed)
    for _ in range(recipe["epochs"]):
        order = rng.permutation(len(texts))
        for start in range(0, len(texts), batch):
            idx = order[start : start + batch]
            enc = tokenizer(
                [texts[i] for i in idx],
                truncation=True,
                max_length=recipe["max_length"],
                padding=True,
                return_tensors="pt",
            ).to(device)
            target = torch.tensor(labels[idx], device=device)
            with torch.autocast(device.type, enabled=device.type == "cuda"):
                logits = model(**enc).logits
            loss = loss_fn(logits.float(), target)
            optimizer.zero_grad()
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            scaler.step(optimizer)
            scaler.update()
            scheduler.step()
    model.eval()
    return model, tokenizer


def score(model, tokenizer, texts, positive_index=1, max_length=256, batch=64):
    """Probability of the injection class for each text."""
    import torch

    device = _device()
    model.to(device).eval()
    out = []
    with torch.no_grad():
        for start in range(0, len(texts), batch):
            enc = tokenizer(
                texts[start : start + batch],
                truncation=True,
                max_length=max_length,
                padding=True,
                return_tensors="pt",
            ).to(device)
            with torch.autocast(device.type, enabled=device.type == "cuda"):
                logits = model(**enc).logits
            out.append(torch.softmax(logits.float(), dim=-1)[:, positive_index].cpu().numpy())
    return np.concatenate(out) if out else np.array([])


def load_released(repo_id, label_name, revision, token=None):
    """Load a released detector pinned to `revision`; return (model, tokenizer, class index)."""
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(repo_id, revision=revision, token=token)
    model = AutoModelForSequenceClassification.from_pretrained(
        repo_id, revision=revision, token=token
    )
    mapping = {v: int(k) for k, v in model.config.id2label.items()}
    if label_name not in mapping:
        raise ValueError(f"{repo_id}: label {label_name!r} not in {model.config.id2label}")
    return model, tokenizer, mapping[label_name]
