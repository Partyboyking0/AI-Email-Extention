from __future__ import annotations

import argparse
import json
from pathlib import Path


def count_feedback(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def main() -> None:
    parser = argparse.ArgumentParser(description="Run PPO alignment for reply generator.")
    parser.add_argument("--feedback-jsonl", default="ml/data/processed/feedback.jsonl")
    parser.add_argument("--min-examples", type=int, default=200)
    parser.add_argument("--steps", type=int, default=1000)
    args = parser.parse_args()

    feedback_count = count_feedback(Path(args.feedback_jsonl))
    assert feedback_count >= args.min_examples, "Insufficient feedback for RLHF - collect more data first"
    print(json.dumps({"status": "ready", "feedback_count": feedback_count, "ppo_steps": args.steps}))


if __name__ == "__main__":
    main()
