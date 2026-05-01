chrome.runtime.onInstalled.addListener(async () => {
  try {
    const ort = await import("./onnxruntime-web.min.js");
    console.log("ONNX Runtime loaded in MV3 service worker", Boolean(ort));
  } catch (error) {
    console.error("ONNX Runtime MV3 import failed", error);
  }
});
