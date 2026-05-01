from backend.app.services.hf_client import HuggingFaceInferenceClient


def test_hf_client_extracts_generated_text() -> None:
    client = HuggingFaceInferenceClient(api_token=None)
    assert client._extract_text([{"generated_text": "Hello"}]) == "Hello"


def test_hf_client_extracts_summary_text() -> None:
    client = HuggingFaceInferenceClient(api_token=None)
    assert client._extract_text([{"summary_text": "Short summary"}]) == "Short summary"
