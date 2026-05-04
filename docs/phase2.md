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

The trained ONNX classifier now exists locally. The popup/background flow does not need to change. The next implementation step is to wire tokenization and `onnxruntime-web` inference into `extension/src/shared/classifier.ts`.

Current local model artifacts:

```text
model.onnx
tokenizer.json
labels.json
```

The ONNX file is intentionally ignored by git because it is a large binary artifact.

## Kaggle Training Run

Downloaded dataset:

```text
saiash/spam-and-ham-email-classification-dataset
```

Kaggle reported license:

```text
CC0-1.0
```

Local download/normalization script:

```text
ml/data/download_kaggle_classifier.py
```

Generated local data files:

```text
ml/data/raw/kaggle_spamassassin/
ml/data/processed/kaggle_spam_ham.jsonl
ml/data/processed/classifier_train_kaggle.jsonl
```

Training command:

```powershell
backend\.venv\Scripts\python.exe ml\training\train_classifier.py --config ml\configs\classifier.yaml --train-file ml\data\processed\classifier_train_kaggle.jsonl --output-dir ml\artifacts\classifier_kaggle
```

Export command:

```powershell
backend\.venv\Scripts\python.exe ml\export\export_onnx.py --model-dir ml\artifacts\classifier_kaggle --out-dir extension\public\models\classifier --quantize
```

Dataset summary:

```text
Combined examples: 1996
spam: 472
low-priority: 1502
opportunity: 6
other app labels: small seed examples
```

Training result:

```text
Accuracy: about 0.978
Macro F1: about 0.196
```

Quality note: this public Kaggle dataset is strong for spam/ham training, but it is not balanced for the app's 10-label taxonomy. The trained model should be treated as a first real artifact, not the final production classifier.

## Synthetic Balance Run

Generated 200 synthetic emails for each classifier label:

```text
urgent
follow-up
action-required
low-priority
finance
newsletter
opportunity
spam
work
personal
```

Generator script:

```text
ml/data/generate_synthetic_classifier.py
```

Generated local files:

```text
ml/data/processed/classifier_synthetic_200_each.jsonl
ml/data/processed/classifier_train_kaggle_synthetic.jsonl
```

Generation command:

```powershell
backend\.venv\Scripts\python.exe ml\data\generate_synthetic_classifier.py --per-label 200
```

Merged dataset summary:

```text
Combined examples: 3996
Synthetic examples: 2000
urgent: 202
follow-up: 202
action-required: 202
low-priority: 1702
finance: 202
newsletter: 202
opportunity: 206
spam: 674
work: 202
personal: 202
```

Retraining command:

```powershell
backend\.venv\Scripts\python.exe ml\training\train_classifier.py --config ml\configs\classifier.yaml --train-file ml\data\processed\classifier_train_kaggle_synthetic.jsonl --output-dir ml\artifacts\classifier_kaggle_synthetic
```

Retraining result:

```text
Accuracy: about 0.996
Macro F1: about 0.996
```

Quality note: this score is useful for confirming the pipeline works, but it is partly inflated because the new category data is synthetic and template-based. Real labeled category data is still needed before treating this as a production classifier.

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

1. Replace the keyword fallback path with real ONNX Runtime Web inference.
2. Add more balanced app-specific labeled emails.
3. Retrain the classifier after adding balanced data.
4. Re-export and quantize with `ml/export/export_onnx.py`.
