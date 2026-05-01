# Phase 0 Validation

## Gmail DOM Selector Check

Run this in Gmail DevTools with an email open:

```js
document.querySelectorAll('[data-message-id]').length
```

Record whether it returns `> 0`, then test the fallback selectors used in `extension/src/content/domReader.ts`.

## ONNX MV3 Check

The Phase 2 classifier starts with `extension/src/content/onnxClassifier.ts`. Replace the keyword fallback with ONNX Runtime Web once the quantized model exists.

## HF Latency Check

Use `docs/latency_report.md` to capture cold and warm endpoint calls before enabling real summarization.
