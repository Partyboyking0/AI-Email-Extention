# Phase 2 - Client-Side Classifier

Phase 2 starts the browser-side classifier path while keeping the popup-driven UX.

## Completed In This Slice

- Added **Classify** as an explicit popup action.
- Added typed classification response in the extension.
- Added local client-side classifier module:

```text
extension/src/shared/classifier.ts
```

- Kept existing content-script badge classifier compatible through:

```text
extension/src/content/onnxClassifier.ts
```

- Added backend `/api/classify` model metadata for compatibility and testing.
- Added backend classifier service:

```text
backend/app/services/classifier.py
```

- Added `classify` to usage analytics feature types.
- Added model slot documentation:

```text
extension/public/models/classifier/README.md
```

- Added demo classifier seed data and label manifest:

```text
ml/data/raw/classifier_demo.jsonl
extension/public/models/classifier/labels.json
```

- Added lightweight classifier baseline evaluation:

```text
ml/evaluation/eval_classifier.py
```

- Upgraded classifier training/export scripts from placeholders to runnable pipelines:

```text
ml/training/train_classifier.py
ml/export/export_onnx.py
```

## Current Behavior

The popup reads the active Gmail email only after the user clicks **Classify**.

Classification currently runs locally in the extension with a deterministic keyword classifier. It returns:

- label
- confidence score
- model version
- source

The current model version is:

```text
keyword-classifier-phase-2
```

Backend compatibility model version:

```text
heuristic-classifier-v3
```

The keyword baseline now includes an `opportunity` label for placement, TNP, and internship emails. Institutional signals like `.ac.in`, `.edu`, `placement cell`, `iiit`, `iit`, `nit`, and `tnp` boost opportunity/work and suppress newsletter.

## ONNX Path

The extension now checks for:

```text
extension/public/models/classifier/model.onnx
```

When the trained ONNX classifier is exported, the popup/background flow does not need to change. The next implementation step is to wire tokenization and `onnxruntime-web` inference into `extension/src/shared/classifier.ts`.

Expected future model artifacts:

```text
model.onnx
tokenizer.json
labels.json
```

Train the classifier when enough labeled examples are available:

```powershell
backend\.venv\Scripts\python.exe ml\training\train_classifier.py --config ml\configs\classifier.yaml
```

Export the trained classifier:

```powershell
backend\.venv\Scripts\python.exe ml\export\export_onnx.py --model-dir ml\artifacts\classifier --out-dir extension\public\models\classifier --quantize
```

The export script writes/copies:

- `model.onnx`
- tokenizer assets
- `labels.json`

## Verification

```powershell
backend\.venv\Scripts\python.exe ml\training\train_classifier.py --dry-run
backend\.venv\Scripts\python.exe ml\evaluation\eval_classifier.py
backend\.venv\Scripts\python.exe ml\export\export_onnx.py --dry-run
backend\.venv\Scripts\python.exe -m pytest backend\tests
npm --prefix extension run lint
```

Latest baseline result on the demo seed data:

```text
Examples: 24
Macro F1: 1.000
```

## Next Steps

1. Prepare labeled classifier data.
2. Fine-tune the classifier in `ml/training/train_classifier.py`.
3. Export and quantize with `ml/export/export_onnx.py`.
4. Add tokenizer + labels artifacts to `extension/public/models/classifier/`.
5. Replace the keyword fallback path with real ONNX Runtime Web inference.
