from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_feedback(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Train reward model from reply feedback.")
    parser.add_argument("--feedback-jsonl", default="ml/data/processed/feedback.jsonl")
    parser.add_argument("--min-examples", type=int, default=200)
    args = parser.parse_args()

    examples = load_feedback(Path(args.feedback_jsonl))
    assert len(examples) >= args.min_examples, "Insufficient feedback for reward model - collect more data first"
    raise SystemExit("Reward model training scaffold ready; wire in BERT pair classifier here.")


if __name__ == "__main__":
    main()
