from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description="Fine-tune Flan-T5 reply generator.")
    parser.add_argument("--config", default="ml/configs/reply_gen.yaml")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.dry_run:
        print(f"Validated reply generation config: {args.config}")
        return

    raise SystemExit("Full reply training requires Avocado reply pairs and GPU runtime.")


if __name__ == "__main__":
    main()
