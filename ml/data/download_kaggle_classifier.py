from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path


DEFAULT_DATASET = "saiash/spam-and-ham-email-classification-dataset"
SPAM_LABELS = {"1", "spam", "true", "yes"}
HAM_LABELS = {"0", "ham", "non-spam", "not spam", "false", "no"}


def download_dataset(dataset: str, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    kaggle_exe = Path(sys.executable).with_name("kaggle.exe")
    command = [str(kaggle_exe), "datasets", "download", "-d", dataset, "-p", str(out_dir), "--unzip"]
    subprocess.run(command, check=True)


def find_csv(raw_dir: Path) -> Path:
    csv_files = sorted(raw_dir.rglob("*.csv"))
    if not csv_files:
        raise SystemExit(f"No CSV files found under {raw_dir}")
    return csv_files[0]


def pick_column(fieldnames: list[str], candidates: tuple[str, ...]) -> str:
    lowered = {name.lower().strip(): name for name in fieldnames}
    for candidate in candidates:
        if candidate in lowered:
            return lowered[candidate]
    raise SystemExit(f"Could not find any of columns {candidates}. Available columns: {fieldnames}")


def normalize_label(value: str) -> str | None:
    cleaned = value.strip().lower()
    if cleaned in SPAM_LABELS:
        return "spam"
    if cleaned in HAM_LABELS:
        return "low-priority"
    return None


def convert_csv(csv_path: Path, out_file: Path, limit_per_label: int) -> dict[str, int]:
    counts = {"spam": 0, "low-priority": 0}
    out_file.parent.mkdir(parents=True, exist_ok=True)

    with csv_path.open("r", encoding="utf-8", errors="ignore", newline="") as source:
        reader = csv.DictReader(source)
        if not reader.fieldnames:
            raise SystemExit(f"CSV has no header: {csv_path}")

        text_column = pick_column(reader.fieldnames, ("text", "email", "message", "body", "email_text"))
        label_column = pick_column(reader.fieldnames, ("label", "spam", "class", "category", "target"))

        with out_file.open("w", encoding="utf-8") as target:
            for row in reader:
                label = normalize_label(str(row.get(label_column, "")))
                text = str(row.get(text_column, "")).strip()
                if not label or not text:
                    continue
                if counts[label] >= limit_per_label:
                    continue

                target.write(json.dumps({"text": text, "label": label}, ensure_ascii=True) + "\n")
                counts[label] += 1

                if all(count >= limit_per_label for count in counts.values()):
                    break

    return counts


def merge_with_seed(seed_file: Path, kaggle_file: Path, out_file: Path) -> None:
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with out_file.open("w", encoding="utf-8") as target:
        for source in (seed_file, kaggle_file):
            with source.open("r", encoding="utf-8") as handle:
                for line in handle:
                    if line.strip():
                        target.write(line)


def main() -> None:
    parser = argparse.ArgumentParser(description="Download and normalize a public Kaggle email classifier dataset.")
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--raw-dir", default="ml/data/raw/kaggle_spamassassin")
    parser.add_argument("--seed-file", default="ml/data/raw/classifier_demo.jsonl")
    parser.add_argument("--normalized-file", default="ml/data/processed/kaggle_spam_ham.jsonl")
    parser.add_argument("--combined-file", default="ml/data/processed/classifier_train_kaggle.jsonl")
    parser.add_argument("--limit-per-label", type=int, default=1500)
    parser.add_argument("--skip-download", action="store_true")
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir)
    if not args.skip_download:
        download_dataset(args.dataset, raw_dir)

    csv_path = find_csv(raw_dir)
    normalized_file = Path(args.normalized_file)
    counts = convert_csv(csv_path, normalized_file, args.limit_per_label)
    merge_with_seed(Path(args.seed_file), normalized_file, Path(args.combined_file))

    print(f"Dataset: {args.dataset}")
    print(f"CSV: {csv_path}")
    print(f"Normalized: {normalized_file}")
    print(f"Combined training file: {args.combined_file}")
    print("Counts:")
    for label, count in counts.items():
        print(f"- {label}: {count}")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        print("Kaggle download failed. Check your Kaggle API credentials.", file=sys.stderr)
        raise SystemExit(exc.returncode) from exc
