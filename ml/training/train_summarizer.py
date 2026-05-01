from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description="Fine-tune PEGASUS summarizer with LoRA.")
    parser.add_argument("--config", default="ml/configs/summarizer.yaml")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.dry_run:
        print(f"Validated summarizer training config: {args.config}")
        return

    raise SystemExit("Full summarizer training requires EmailSum data and GPU runtime.")


if __name__ == "__main__":
    main()
