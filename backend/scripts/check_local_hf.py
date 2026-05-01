import importlib.util
import sys
from pathlib import Path
import argparse

sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.app.core.config import settings
from backend.app.services.local_hf import LocalHuggingFaceService


def installed(package: str) -> bool:
    return importlib.util.find_spec(package) is not None


def main() -> None:
    parser = argparse.ArgumentParser(description="Check local Hugging Face runtime dependencies.")
    parser.add_argument("--generate", action="store_true", help="Also load local models and run tiny generations.")
    args = parser.parse_args()

    print("HF_LOCAL_ENABLED:", settings.hf_local_enabled)
    print("HF_LOCAL_SUMMARIZER_MODEL:", settings.hf_local_summarizer_model)
    print("HF_LOCAL_REPLY_MODEL:", settings.hf_local_reply_model)
    print("transformers:", "installed" if installed("transformers") else "missing")
    print("torch:", "installed" if installed("torch") else "missing")
    print("sentencepiece:", "installed" if installed("sentencepiece") else "missing")
    print("protobuf:", "installed" if installed("google.protobuf") else "missing")

    missing = [pkg for pkg in ("torch", "sentencepiece") if not installed(pkg)]
    if missing:
        print("\nMissing local HF dependencies:")
        print(", ".join(missing))
        print("\nInstall them with:")
        print(r'& "$env:LOCALAPPDATA\Python\pythoncore-3.14-64\python.exe" -m pip install -r backend\requirements-hf-local.txt')
        return

    if args.generate:
        service = LocalHuggingFaceService(settings.hf_local_summarizer_model, settings.hf_local_reply_model)
        print("\nSummary test:")
        print(service.summarize("Please bring your ID card tomorrow and report to the exam hall by 9 AM."))
        print("\nReply test:")
        print(service.reply("Can you review the seating plan by tomorrow?", "concise"))


if __name__ == "__main__":
    main()
