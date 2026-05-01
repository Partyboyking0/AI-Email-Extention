from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any


def load_config(path: str) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        raise SystemExit("Install pyyaml or run `pip install -r ml/requirements.txt`.") from exc

    with Path(path).open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data


def load_jsonl(path: Path, text_column: str, label_column: str, labels: set[str]) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Classifier training data not found: {path}")

    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            row = json.loads(line)
            text = str(row.get(text_column, "")).strip()
            label = str(row.get(label_column, "")).strip()
            if not text:
                raise SystemExit(f"Missing text at {path}:{line_number}")
            if label not in labels:
                raise SystemExit(f"Unknown label '{label}' at {path}:{line_number}")
            rows.append({"text": text, "label": label})
    return rows


def validate_dataset(config: dict[str, Any]) -> tuple[list[dict[str, str]], dict[str, int]]:
    data_config = config.get("data", {})
    train_file = Path(data_config.get("train_file", ""))
    text_column = data_config.get("text_column", "text")
    label_column = data_config.get("label_column", "label")
    labels = set(config.get("labels", []))

    rows = load_jsonl(train_file, text_column, label_column, labels)
    counts: Counter[str] = Counter(row["label"] for row in rows)

    missing = sorted(labels - set(counts))
    if missing:
        raise SystemExit(f"Training data has no examples for labels: {', '.join(missing)}")

    return rows, dict(sorted(counts.items()))


def split_rows(rows: list[dict[str, str]], eval_split: float, seed: int) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(row["label"], []).append(row)

    rng = random.Random(seed)
    train_rows: list[dict[str, str]] = []
    eval_rows: list[dict[str, str]] = []
    for label_rows in grouped.values():
        rng.shuffle(label_rows)
        eval_count = max(1, round(len(label_rows) * eval_split)) if len(label_rows) > 1 else 0
        eval_rows.extend(label_rows[:eval_count])
        train_rows.extend(label_rows[eval_count:])

    rng.shuffle(train_rows)
    rng.shuffle(eval_rows)
    return train_rows, eval_rows


def macro_f1(labels: list[int], predictions: list[int], label_count: int) -> float:
    scores = []
    for label_id in range(label_count):
        tp = sum(1 for gold, pred in zip(labels, predictions) if gold == label_id and pred == label_id)
        fp = sum(1 for gold, pred in zip(labels, predictions) if gold != label_id and pred == label_id)
        fn = sum(1 for gold, pred in zip(labels, predictions) if gold == label_id and pred != label_id)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        scores.append(2 * precision * recall / (precision + recall) if precision + recall else 0.0)
    return sum(scores) / len(scores)


def train(config: dict[str, Any], rows: list[dict[str, str]], output_dir: Path, eval_split: float, seed: int) -> None:
    try:
        import numpy as np
        from datasets import Dataset
        from transformers import AutoModelForSequenceClassification, AutoTokenizer, Trainer, TrainingArguments
    except ImportError as exc:
        raise SystemExit("Install ML dependencies first: `pip install -r ml/requirements.txt`.") from exc

    labels = list(config["labels"])
    label_to_id = {label: index for index, label in enumerate(labels)}
    id_to_label = {index: label for label, index in label_to_id.items()}
    train_rows, eval_rows = split_rows(rows, eval_split=eval_split, seed=seed)
    if not train_rows or not eval_rows:
        raise SystemExit("Need enough data for both train and eval splits.")

    tokenizer = AutoTokenizer.from_pretrained(config["model_name"])

    def encode(batch: dict[str, list[str]]) -> dict[str, Any]:
        encoded = tokenizer(batch["text"], truncation=True, padding="max_length", max_length=256)
        encoded["labels"] = [label_to_id[label] for label in batch["label"]]
        return encoded

    train_dataset = Dataset.from_list(train_rows).map(encode, batched=True, remove_columns=["text", "label"])
    eval_dataset = Dataset.from_list(eval_rows).map(encode, batched=True, remove_columns=["text", "label"])

    model = AutoModelForSequenceClassification.from_pretrained(
        config["model_name"],
        num_labels=len(labels),
        id2label=id_to_label,
        label2id=label_to_id,
    )

    training_config = config.get("training", {})

    def compute_metrics(eval_prediction):
        logits, gold = eval_prediction
        pred = np.argmax(logits, axis=-1)
        return {
            "accuracy": float((pred == gold).mean()),
            "f1_macro": macro_f1(list(gold), list(pred), len(labels)),
        }

    args = TrainingArguments(
        output_dir=str(output_dir),
        learning_rate=float(training_config.get("learning_rate", 2e-5)),
        per_device_train_batch_size=int(training_config.get("batch_size", 16)),
        per_device_eval_batch_size=int(training_config.get("batch_size", 16)),
        num_train_epochs=float(training_config.get("num_epochs", 3)),
        weight_decay=float(training_config.get("weight_decay", 0.01)),
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1_macro",
        report_to=[],
        seed=seed,
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        compute_metrics=compute_metrics,
    )
    trainer.train()
    trainer.save_model(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))
    (output_dir / "labels.json").write_text(json.dumps(labels, indent=2) + "\n", encoding="utf-8")
    print(f"Saved classifier artifacts to {output_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Fine-tune DistilBERT email classifier.")
    parser.add_argument("--config", default="ml/configs/classifier.yaml")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--eval-split", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    config = load_config(args.config)
    rows, counts = validate_dataset(config)

    if args.dry_run:
        print(f"Validated classifier training config: {args.config}")
        print(f"Examples: {len(rows)}")
        print("Label counts:")
        for label, count in counts.items():
            print(f"- {label}: {count}")
        return

    output_dir = Path(args.output_dir or config.get("output_dir", "ml/artifacts/classifier"))
    train(config, rows, output_dir=output_dir, eval_split=args.eval_split, seed=args.seed)


if __name__ == "__main__":
    main()
