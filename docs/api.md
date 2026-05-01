# API Contract

## `POST /api/summarize`

Request:

```json
{ "email_text": "Please review this by EOD.", "thread_id": "abc123" }
```

Response:

```json
{ "bullets": ["...", "...", "..."], "model_version": "mock-pegasus-phase-3", "latency_ms": 12 }
```

## `POST /api/reply`

Request:

```json
{ "email_text": "Can you review this?", "tone": "formal" }
```

## `POST /api/tasks`

Request:

```json
{ "email_text": "Please send the report by Friday." }
```

## `POST /api/classify`

Request:

```json
{ "email_text": "Urgent: please review this by EOD.", "thread_id": "abc123" }
```

Response:

```json
{ "label": "urgent", "score": 0.86, "model_version": "heuristic-classifier-v1" }
```

## `POST /api/feedback`

Request:

```json
{ "email_text": "...", "generated_reply": "...", "rating": "down", "reason": "Too long" }
```
