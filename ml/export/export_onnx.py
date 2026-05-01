from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


DEFAULT_LABELS = [
    "urgent",
    "follow-up",
    "action-required",
    "low-priority",
    "finance",
    "newsletter",
    "opportunity",
    "spam",
    "work",
    "personal",
]


def sync_label_manifest(model_dir: Path, out_dir: Path) -> None:
    source = model_dir / "labels.json"
    labels = json.loads(source.read_text(encoding="utf-8")) if source.exists() else DEFAULT_LABELS
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / "labels.json"
    target.write_text(json.dumps(labels, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote label manifest with {len(labels)} labels: {target}")


def copy_tokenizer_assets(model_dir: Path, out_dir: Path) -> None:
    for name in ("tokenizer.json", "tokenizer_config.json", "vocab.txt", "special_tokens_map.json"):
        source = model_dir / name
        if source.exists():
            shutil.copy2(source, out_dir / name)
            print(f"Copied {name}")


def export_onnx(model_dir: Path, out_dir: Path, quantize: bool) -> None:
    try:
        from optimum.onnxruntime import ORTModelForSequenceClassification
        from transformers import AutoTokenizer
    except ImportError as exc:
        raise SystemExit("Install ONNX export dependencies first: `pip install -r ml/requirements.txt`.") from exc

    if not model_dir.exists():
        raise SystemExit(f"Trained classifier directory not found: {model_dir}")

    out_dir.mkdir(parents=True, exist_ok=True)
    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    tokenizer.save_pretrained(out_dir)

    model = ORTModelForSequenceClassification.from_pretrained(model_dir, export=True)
    model.save_pretrained(out_dir)

    exported = list(out_dir.glob("*.onnx"))
    if exported and exported[0].name != "model.onnx":
        exported[0].replace(out_dir / "model.onnx")

    if quantize:
        quantize_model(out_dir)

    sync_label_manifest(model_dir, out_dir)
    copy_tokenizer_assets(model_dir, out_dir)
    print(f"Exported ONNX classifier to {out_dir}")


def quantize_model(out_dir: Path) -> None:
    try:
        from onnxruntime.quantization import QuantType, quantize_dynamic
    except ImportError as exc:
        raise SystemExit("Install onnxruntime quantization dependencies first: `pip install -r ml/requirements.txt`.") from exc

    model_path = out_dir / "model.onnx"
    if not model_path.exists():
        raise SystemExit(f"Cannot quantize missing ONNX model: {model_path}")

    quantized_path = out_dir / "model.int8.onnx"
    quantize_dynamic(str(model_path), str(quantized_path), weight_type=QuantType.QInt8)
    quantized_path.replace(model_path)
    print(f"Quantized ONNX model: {model_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Export classifier to ONNX and optionally apply INT8 quantization.")
    parser.add_argument("--model-dir", default="ml/artifacts/classifier")
    parser.add_argument("--out-dir", default="extension/public/models/classifier")
    parser.add_argument("--quantize", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    model_dir = Path(args.model_dir)
    out_dir = Path(args.out_dir)

    if args.dry_run:
        print(f"Would export {model_dir} to {out_dir}")
        print(f"Quantize: {args.quantize}")
        sync_label_manifest(model_dir, out_dir)
        return

    export_onnx(model_dir, out_dir, quantize=args.quantize)


if __name__ == "__main__":
    main()
