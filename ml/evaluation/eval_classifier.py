from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def predict(text: str) -> str:
    lowered = text.lower()
    signals = [
        ("urgent", ("urgent", "asap", "immediately", "eod", "blocked", "critical", "important")),
        ("follow-up", ("following up", "follow up", "checking in", "reminder", "gentle reminder", "waiting")),
        ("opportunity", ("internship", "placement", "tnp", "training and placement", "career opportunity", "hiring", "apply", "campus drive", ".ac.in")),
        ("action-required", ("please", "can you", "could you", "need you to", "submit", "confirm", "send")),
        ("finance", ("invoice", "payment", "receipt", "billing", "refund", "paid", "amount due")),
        ("newsletter", ("newsletter", "unsubscribe", "weekly update", "digest", "read more")),
        ("spam", ("winner", "free money", "claim now", "limited offer", "act now", "prize")),
        ("personal", ("family", "dinner", "birthday", "weekend", "trip", "holiday")),
        ("work", ("project", "meeting", "deadline", "review", "proposal", "client", "report")),
    ]
    for label, keywords in signals:
        if any(keyword in lowered for keyword in keywords):
            return label
    return "low-priority"


def macro_f1(rows: list[tuple[str, str]], labels: list[str]) -> tuple[float, dict[str, float]]:
    per_label = {}
    for label in labels:
        tp = sum(1 for gold, pred in rows if gold == label and pred == label)
        fp = sum(1 for gold, pred in rows if gold != label and pred == label)
        fn = sum(1 for gold, pred in rows if gold == label and pred != label)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        per_label[label] = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return sum(per_label.values()) / len(labels), per_label


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the Phase 2 keyword classifier baseline.")
    parser.add_argument("--data", default="ml/data/raw/classifier_demo.jsonl")
    args = parser.parse_args()

    data_path = Path(args.data)
    rows: list[tuple[str, str]] = []
    labels: set[str] = set()
    confusion: dict[str, Counter[str]] = defaultdict(Counter)

    with data_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            gold = row["label"]
            pred = predict(row["text"])
            labels.add(gold)
            labels.add(pred)
            rows.append((gold, pred))
            confusion[gold][pred] += 1

    ordered_labels = sorted(labels)
    score, per_label = macro_f1(rows, ordered_labels)

    print(f"Examples: {len(rows)}")
    print(f"Macro F1: {score:.3f}")
    print("Per-label F1:")
    for label in ordered_labels:
        print(f"- {label}: {per_label[label]:.3f}")
    print("Confusion matrix rows:")
    for label in ordered_labels:
        values = ", ".join(f"{pred}={confusion[label][pred]}" for pred in ordered_labels if confusion[label][pred])
        print(f"- {label}: {values or 'none'}")


if __name__ == "__main__":
    main()
