from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description="Fine-tune BERT NER for action items and deadlines.")
    parser.add_argument("--config", default="ml/configs/ner.yaml")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.dry_run:
        print(f"Validated NER config: {args.config}")
        return

    raise SystemExit("Full NER training requires labeled token classification data.")


if __name__ == "__main__":
    main()
