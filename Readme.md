# DNA Thrift WhatsApp AI Automation

A production-oriented backend for a WhatsApp thrift-shoe assistant. Customers can send natural-language requests or real shoe images. The application validates every boundary with Pydantic, uses a vision-language model for brand/model/condition recognition, uses EasyOCR for size-tag reading, searches a persistent SQLite inventory, applies condition-based pricing, and routes the conversation through a deterministic state machine with loop prevention.

<img width="1080" height="720" alt="image" src="https://github.com/user-attachments/assets/d7572b8e-72fd-4f47-8bb3-a8f81ab11f93" />


## What is implemented — Days 1 to 5

### Day 1 — Webhook and project foundation

- FastAPI application with health endpoint and Swagger documentation.
- Local JSON webhook simulation at `POST /dev/webhook`.
- Real multipart image upload at `POST /dev/upload`.
- Meta webhook verification at `GET /webhook`.
- Typed Meta WhatsApp message webhook receiver at `POST /webhook`.
- WhatsApp media download and text-reply client using the official Graph API flow.

### Day 2 — Text parsing, inventory, and pricing

- Rule-based parser for known brands/models and US sizes.
- Optional OpenRouter LLM extraction for flexible or informal text.
- LLM output is schema-constrained and Pydantic-validated.
- Persistent SQLite inventory rather than an in-memory list.
- Exact model + size matching.
- Nearby-size partial matching.
- Brand alternatives for no-match cases.
- Condition-based price calculation.

### Day 3 — Real multimodal image path

- **No filename-based or URL-keyword shoe detector exists.**
- OpenRouter multimodal API analyzes actual image pixels for:
  - brand
  - exact model when confidence is sufficient
  - style family
  - visible condition score
  - wear/creasing/sole notes
- EasyOCR reads actual image pixels from three preprocessing variants.
- OCR detects US, UK, and EU size markings.
- Explicit US sizes can be routed directly.
- UK/EU conversions are treated as estimates and require customer confirmation.
- Missing or unreadable size tags trigger clarification rather than guessing.
- Local files, public URLs, Swagger uploads, and downloaded WhatsApp media are supported.

### Day 4 — Deterministic conversation state machine

Implemented states:

- `AWAITING_QUERY`
- `IDENTIFYING_SHOE`
- `AWAITING_SIZE_CONFIRMATION`
- `PRESENTING_RESULT`
- `AWAITING_PURCHASE_INTENT`
- `FALLBACK_HUMAN`

The state machine—not the LLM—decides which transitions are allowed. It remembers partial information across messages, such as:

```text
Customer: Air Force 1
Bot: What US size are you looking for?
Customer: US 10
Bot: Nike Air Force 1 White ... Rs. 9,450 ...
```

Loop prevention is deterministic:

```text
Initial ambiguous request      → clarification
First failed follow-up         → clarification again
Second failed follow-up        → FALLBACK_HUMAN
```

### Day 5 — Validation and hardening

- Strict internal Pydantic models use `extra="forbid"`.
- Third-party Meta models validate known fields while safely ignoring provider-added fields.
- Cross-field validation prevents contradictory OCR, match, and conversation objects.
- All endpoints use typed request and response models.
- Structured 422, 415, 422-provider, 502, 503, and 500 error responses.
- Internal tracebacks are logged but not exposed to customers.
- SQLite-backed idempotency prevents duplicate webhook deliveries from advancing state or sending the same WhatsApp reply twice.
- SQLite-backed sessions survive application-level object recreation.
- Remote image downloader validates format, limits bytes, follows safe redirects, and blocks private/local-network URLs.
- No application code uses `Any`.
- All application functions have parameter and return annotations.

## Architecture

```text
WhatsApp / Swagger / JSON webhook
                │
                ▼
       Pydantic webhook models
                │
                ▼
     Deterministic conversation engine
          │                  │
          │ text             │ image
          ▼                  ▼
 Hybrid NLP parser      Image validation
(rule + optional LLM)       │
          │                 ├── OpenRouter VLM
          │                 └── EasyOCR size reading
          │                  │
          └────────┬─────────┘
                   ▼
             Typed ShoeQuery
                   │
                   ▼
        SQLite inventory repository
                   │
                   ▼
     Exact / partial / no-match routing
                   │
                   ▼
       Condition-adjusted price reply
                   │
                   ▼
       Typed response + saved session
```

## Project structure

```text
app/
├── conversation/
│   └── engine.py
├── core/
│   ├── config.py
│   ├── errors.py
│   ├── exception_handlers.py
│   └── logging_config.py
├── inventory/
│   ├── database.py
│   ├── pricing.py
│   ├── seed.py
│   └── service.py
├── models/
│   ├── api_models.py
│   ├── base.py
│   ├── conversation_models.py
│   ├── error_models.py
│   ├── inventory_models.py
│   ├── meta_webhook_models.py
│   ├── shoe_models.py
│   └── webhook_models.py
├── nlp/
│   └── text_parser.py
├── vision/
│   ├── image_io.py
│   ├── ocr.py
│   ├── photo_pipeline.py
│   └── vlm.py
├── webhook/
│   ├── dev_routes.py
│   ├── meta_client.py
│   └── routes.py
├── container.py
└── main.py

tests/
samples/
docs/
scripts/
```

## Technology decisions

### FastAPI

FastAPI gives typed request handling, automatic OpenAPI/Swagger documentation, dependency-friendly architecture, and native Pydantic integration.

### SQLite

SQLite is a real structured database and is appropriate for this one-week challenge and local demonstration. It stores inventory, conversation sessions, and processed-message idempotency records. A high-traffic deployment should migrate the same repository interfaces to PostgreSQL and Redis.

### OpenRouter multimodal VLM

The application uses a real OpenAI-compatible multimodal request with a base64 image and strict JSON schema. The default example model is `openrouter/free`, which can route to a compatible free model. For a controlled final demo, pin a specific vision-capable model in `VISION_MODEL` after verifying it in your OpenRouter account.

### EasyOCR

EasyOCR is used specifically for text on the size tag. It does **not** identify the shoe model. Shoe recognition and OCR remain separate typed services so failures are visible and independently testable.

### Hybrid NLP

Rules handle common inventory terms without network latency. When rules cannot fully understand an informal request and OpenRouter is configured, the LLM attempts schema-constrained extraction. Flow control remains deterministic.

## Requirements

Recommended:

- Python 3.11 or 3.12
- Windows, Linux, or macOS
- OpenRouter API key for real photo recognition
- Meta WhatsApp Cloud API credentials only when using actual WhatsApp

> EasyOCR installs PyTorch-related dependencies and may take several minutes and substantial disk space on the first installation. Its model files are downloaded on the first OCR run.

## Installation

### 1. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Windows Command Prompt:

```cmd
python -m venv .venv
.venv\Scripts\activate
```

Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

For tests:

```bash
pip install -r requirements-dev.txt
```

### 3. Create local environment configuration

```bash
copy .env.example .env
```

Linux/macOS:

```bash
cp .env.example .env
```

Minimum for real photo analysis:

```env
OPENROUTER_API_KEY=your-key
VISION_MODEL=openrouter/free
ENABLE_EASYOCR=true
```

For stable evaluation, replace `openrouter/free` with a pinned image-capable model available in your account.

### 4. Check setup

```bash
python scripts/check_setup.py
```

### 5. Run the API

```bash
uvicorn app.main:app --reload
```

Open:

- API health: `http://127.0.0.1:8000/`
- Swagger: `http://127.0.0.1:8000/docs`

## Local text test

Use `POST /dev/webhook`:

```json
{
  "sender_id": "user_123",
  "message_id": "msg_001",
  "message_type": "text",
  "text": "Do you have Air Force 1 size 10?"
}
```

Expected inventory result includes:

```text
Nike Air Force 1 White
Condition: 6/10
Condition-adjusted price: Rs. 9,450
```

## Local real-image test

Use `POST /dev/upload` from Swagger:

- `sender_id`: `photo_user_1`
- `message_id`: `photo_msg_1`
- `image`: select a real JPEG/PNG/WEBP shoe image

The pipeline will:

1. Validate the actual image.
2. Send its pixels to the configured VLM.
3. Run EasyOCR on actual image pixels.
4. Produce a validated `PhotoAnalysisResult`.
5. Ask for clarification if brand/model/size is uncertain.
6. Search SQLite inventory only when brand, model, and confirmed US size are available.

A URL-based image can also be tested through `POST /dev/webhook`:

```json
{
  "sender_id": "photo_user_2",
  "message_id": "photo_msg_2",
  "message_type": "image",
  "image_url": "https://public.example.com/real-shoe-photo.jpg"
}
```

Private and local-network URLs are deliberately rejected.

## WhatsApp Cloud API setup

Set:

```env
WHATSAPP_VERIFY_TOKEN=a-long-random-value
WHATSAPP_ACCESS_TOKEN=your-meta-token
WHATSAPP_PHONE_NUMBER_ID=your-phone-number-id
WHATSAPP_GRAPH_VERSION=v25.0
```

Configure the public HTTPS callback URL in Meta:

```text
https://your-domain.example/webhook
```

Verification uses `GET /webhook`. Incoming text and image messages use `POST /webhook`. Image media is downloaded through Meta using the media ID, passed through the real photo pipeline, and the typed bot reply is sent through the Messages API.

For local Meta testing, expose the FastAPI server using a secure HTTPS tunnel or deploy it.

## Pricing policy

```text
Condition 9–10 → 100% of base price
Condition 7–8  → 85% of base price
Condition 5–6  → 70% of base price
Condition 1–4  → 55% of base price
```

The inventory pair's stored condition score is authoritative for returned price. A customer's uploaded photo condition is useful for visual analysis but does not overwrite the condition of a different physical inventory pair.

## Error behavior

Malformed payload example:

```json
{
  "sender_id": "user_1",
  "message_id": "msg_bad",
  "message_type": "text",
  "text": "   "
}
```

Returns a structured error:

```json
{
  "error": {
    "code": "request_validation_failed",
    "message": "The incoming request is malformed or incomplete.",
    "details": []
  }
}
```

External API secrets, authorization headers, raw images, and local file paths are not written to normal logs.

## Automated tests

Run:

```bash
python -m pytest -q
```

Current included suite covers:

- text parsing
- correct Air Force/Air Jordan separation
- size validation
- exact/partial/no-match inventory behavior
- condition pricing
- Pydantic rejection of malformed input
- OCR US/UK/EU interpretation
- multi-turn size confirmation
- loop prevention
- idempotency
- real photo-pipeline combination through injected test adapters
- Meta webhook schema parsing
- API health, webhook validation, and verification
- private-network image URL blocking

## Multimodal limitations

No vision system is perfectly reliable. The application deliberately exposes uncertainty.

- Similar colorways and silhouettes may confuse the VLM.
- A single photo may not show enough logos/model-specific details.
- Counterfeit/authenticity verification is outside this project's scope.
- EasyOCR can fail on blur, glare, low contrast, curved tags, extreme angles, partial crops, or worn printing.
- UK/EU to US conversion varies by brand, gender, and product line; those results require confirmation.
- Condition scoring is subjective and limited to visible surfaces.
- `openrouter/free` may route to different models; pin a model for consistent demonstration behavior.

The safe behavior is always: **ask rather than silently guess**.

## Submission demo sequence

Record these four required cases:

1. **Text success** — `Air Force 1 size 10` returns the correct item and Rs. 9,450.
2. **Photo success** — upload a clear shoe + tag image; show VLM, OCR, inventory, and response.
3. **Ambiguous clarification** — `Nike shoes?` asks for model and size.
4. **Loop fallback** — repeat the same incomplete reply until `FALLBACK_HUMAN` appears.

Also show one malformed payload returning structured validation failure. That directly proves Day 5 hardening.

## What remains for Days 6 and 7

- Run the complete test matrix using the exact final OpenRouter model.
- Test real WhatsApp end to end using Meta's test number.
- Capture real shoe/tag examples and record the required demo.
- Add screenshots and final environment/deployment instructions.
- Pin the final selected VLM after measuring accuracy and latency.

## Official implementation references

- OpenRouter image inputs: https://openrouter.ai/docs/guides/overview/multimodal/image-understanding
- OpenRouter structured outputs: https://openrouter.ai/docs/guides/features/structured-outputs
- OpenRouter free model router: https://openrouter.ai/openrouter/free
- EasyOCR API documentation: https://www.jaided.ai/easyocr/documentation/
- Meta WhatsApp webhook reference: https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/reference/messages
- Meta WhatsApp media API: https://developers.facebook.com/documentation/business-messaging/whatsapp/business-phone-numbers/media
- Meta WhatsApp send messages: https://developers.facebook.com/documentation/business-messaging/whatsapp/messages/send-messages
- Meta Graph API changelog: https://developers.facebook.com/docs/graph-api/changelog/
