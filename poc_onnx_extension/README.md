# ONNX MV3 POC

Copy `onnxruntime-web.min.js` from `node_modules/onnxruntime-web/dist/` into this directory, then load this folder as an unpacked extension.

The background worker dynamically imports ONNX Runtime so you can confirm MV3 compatibility before wiring the Phase 2 classifier.
