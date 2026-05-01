# Hugging Face Setup

The backend can use Hugging Face for summarization and reply generation when these `.env` values are filled:

```env
HF_SUMMARIZER_ENDPOINT=
HF_REPLY_ENDPOINT=
HF_API_TOKEN=
```

When these values are blank, the backend uses local fallback services:

- `local-extractive-summarizer-v1`
- `local-reply-generator-v1`

The Hugging Face paths are implemented with LangChain Core:

- prompt templates live in `backend/app/services/prompt_templates.py`
- local model execution lives in `backend/app/services/local_hf.py`
- remote/provider HTTP calls are wrapped in LangChain runnables in `backend/app/services/hf_client.py`

## 1. Create A Hugging Face Token

Create a Hugging Face access token from your Hugging Face account settings.

For protected endpoints, the token must be allowed to call inference APIs/endpoints.

For Option 2 serverless/provider inference, the token must include:

```text
Make calls to Inference Providers
```

For dedicated paid endpoints, the token must include:

```text
Make calls to your Inference Endpoints
```

Paste it into `.env`:

```env
HF_API_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Do not commit `.env`.

## Option 2: Serverless HF Inference Provider

Use this before paid dedicated endpoints.

Set:

```env
HF_API_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
HF_USE_PROVIDER=true
HF_PROVIDER_BASE_URL=https://router.huggingface.co/hf-inference/models
HF_CHAT_BASE_URL=https://router.huggingface.co/v1/chat/completions
HF_SUMMARIZER_MODEL=sshleifer/distilbart-cnn-12-6
HF_REPLY_MODEL=katanemo/Arch-Router-1.5B:hf-inference
HF_SUMMARIZER_ENDPOINT=
HF_REPLY_ENDPOINT=
```

This calls Hugging Face's serverless HF Inference provider by model ID. Availability can depend on Hugging Face quotas, model support, and account limits. If the provider call fails, the backend falls back to local summarization/reply generation.

If the check script returns `403 Forbidden`, recreate or edit the token and enable:

```text
Make calls to Inference Providers
```

Then restart the backend and run:

```powershell
& "$env:LOCALAPPDATA\Python\pythoncore-3.14-64\python.exe" backend\scripts\check_hf_config.py
```

Expected model versions after provider inference is active:

```text
hf-provider:sshleifer/distilbart-cnn-12-6
hf-provider:katanemo/Arch-Router-1.5B:hf-inference
```

## Option 3: Local Transformers Execution

Use this when you want to download Hugging Face models and run inference on your own machine.
This path uses LangChain LCEL for prompting and output parsing, then executes Hugging Face Transformers locally.

Install extra dependencies:

```powershell
& "$env:LOCALAPPDATA\Python\pythoncore-3.14-64\python.exe" -m pip install -r backend\requirements-hf-local.txt
```

Check local dependencies:

```powershell
& "$env:LOCALAPPDATA\Python\pythoncore-3.14-64\python.exe" backend\scripts\check_local_hf.py
```

Set:

```env
HF_LOCAL_ENABLED=true
HF_LOCAL_SUMMARIZER_MODEL=google/flan-t5-small
HF_LOCAL_REPLY_MODEL=google/flan-t5-small
```

Then restart the backend.

For local HF execution, PyTorch must be installed in the same Python environment that runs FastAPI. If PyTorch is missing, the backend logs the local HF failure and falls back to the deterministic local reply/summarizer so the extension still works.

Expected model versions:

```text
hf-local:google/flan-t5-small
hf-local:google/flan-t5-small
```

Local execution can be slow on CPU, especially the first run, because the models must be downloaded and loaded into memory.

Recommended verification:

```powershell
& "$env:LOCALAPPDATA\Python\pythoncore-3.14-64\python.exe" backend\scripts\check_local_hf.py --generate
```

Expected model versions after local HF is active:

```text
hf-local:google/flan-t5-small
```

## 2. Choose Endpoint Type

Recommended for this project:

- Summarizer endpoint: a summarization or text2text model.
- Reply endpoint: a text-generation or text2text model.

Good starting models for testing:

- Summarizer: `sshleifer/distilbart-cnn-12-6` or `google/pegasus-xsum`
- Reply generator: `google/flan-t5-base` or `google/flan-t5-large`

The original project plan eventually expects fine-tuned:

- `google/pegasus-xsum` for summaries
- `google/flan-t5-large` for replies

## 3. Create Inference Endpoints

In Hugging Face:

1. Open the model page.
2. Create an Inference Endpoint for the model.
3. Choose a protected endpoint if you want token-required access.
4. Wait until the endpoint status is running.
5. Copy the endpoint URL.

Paste URLs into `.env`:

```env
HF_SUMMARIZER_ENDPOINT=https://your-summarizer-endpoint.endpoints.huggingface.cloud
HF_REPLY_ENDPOINT=https://your-reply-endpoint.endpoints.huggingface.cloud
```

## 4. Restart Backend

After changing `.env`, restart FastAPI:

```powershell
& "$env:LOCALAPPDATA\Python\pythoncore-3.14-64\python.exe" -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8001 --reload
```

## 5. Verify

Run:

```powershell
& "$env:LOCALAPPDATA\Python\pythoncore-3.14-64\python.exe" backend\scripts\check_hf_config.py
```

Then test through Swagger:

```text
http://127.0.0.1:8001/docs
```

Use:

- `POST /api/summarize`
- `POST /api/reply`

Expected model versions after HF is active:

```text
hf-summarizer-endpoint
hf-reply-endpoint
```

If you still see local model versions, one of these is wrong:

- endpoint URL is blank
- token is blank/invalid
- endpoint is paused/not running
- endpoint task format is incompatible
