# Classifier Model Slot

Phase 2 uses a client-side classifier path.

Current behavior:

- The popup **Classify** action runs the extension keyword classifier locally.
- If `model.onnx` is added here later, the extension detects that a bundled model exists and keeps the same user flow.

Expected future files:

```text
extension/public/models/classifier/model.onnx
extension/public/models/classifier/tokenizer.json
extension/public/models/classifier/labels.json
```

The ONNX model should be exported from `ml/export/export_onnx.py` after classifier training is ready.
