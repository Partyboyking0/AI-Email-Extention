from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description="Push versioned model artifacts to Hugging Face Hub.")
    parser.add_argument("--repo-id", required=True)
    parser.add_argument("--artifact-dir", required=True)
    args = parser.parse_args()
    print(f"Ready to upload {args.artifact_dir} to {args.repo_id} once huggingface-hub login is configured.")


if __name__ == "__main__":
    main()
