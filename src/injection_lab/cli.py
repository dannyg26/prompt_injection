import argparse
import json
from pathlib import Path

from .experiment import evaluate, predict, print_summary, train
from .fetch import fetch_deepset


def main():
    parser = argparse.ArgumentParser(description="Offline prompt-injection detector experiments")
    commands = parser.add_subparsers(dest="command", required=True)
    fetch = commands.add_parser("fetch-deepset", help="Download and pin the public starter dataset")
    fetch.add_argument("--out", default="data/processed/deepset.jsonl")
    fetch.add_argument("--raw", default="data/raw/deepset")
    fetch.add_argument("--revision", default="main")
    fetch.add_argument("--seed", type=int, default=42)
    fit = commands.add_parser("train", help="Fit a baseline; select threshold on validation only")
    fit.add_argument("--data", required=True)
    fit.add_argument("--out", required=True)
    fit.add_argument("--seed", type=int, default=42)
    fit.add_argument("--max-fpr", type=float, default=0.05)
    fit.add_argument("--features", choices=["word", "char", "combined"], default="combined")
    test = commands.add_parser("evaluate", help="Score held-out JSONL with a frozen model")
    test.add_argument("--model", required=True, help="Trusted local joblib artifact only")
    test.add_argument("--data", required=True)
    test.add_argument("--out", required=True)
    test.add_argument("--require-new-source", action="store_true")
    test.add_argument("--require-new-families", action="store_true")
    infer = commands.add_parser("predict", help="Classify text without executing it")
    infer.add_argument("--model", required=True, help="Trusted local joblib artifact only")
    inputs = infer.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--text")
    inputs.add_argument("--file", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "fetch-deepset":
            print(json.dumps(fetch_deepset(args.out, args.raw, args.seed, args.revision), indent=2))
        elif args.command == "train":
            print_summary(train(args.data, args.out, args.seed, args.max_fpr, args.features))
        elif args.command == "evaluate":
            print_summary(
                evaluate(
                    args.model,
                    args.data,
                    args.out,
                    args.require_new_source,
                    args.require_new_families,
                )
            )
        else:
            text = args.file.read_text(encoding="utf-8") if args.file else args.text
            print(json.dumps(predict(args.model, text), indent=2))
    except (ValueError, OSError) as exc:
        parser.exit(2, f"error: {exc}\n")


if __name__ == "__main__":
    main()
