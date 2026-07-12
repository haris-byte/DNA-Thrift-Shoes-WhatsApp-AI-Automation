# Architecture and control boundaries

## Deterministic control

The conversation engine is the only component allowed to change conversation state. NLP, VLM, and OCR components only return validated observations.

## Typed boundaries

- Dev webhook JSON → `DevWebhookPayload`
- Internal message → `IncomingMessage`
- Meta provider body → `MetaWebhookPayload`
- NLP output → `TextParserResult`
- Vision output → `VisionAnalysisResult`
- OCR output → `OCRResult`
- Unified photo result → `PhotoAnalysisResult`
- Inventory output → `InventoryMatchResult`
- State persistence → `ConversationSession`
- API reply → `BotResponse`

## Persistence

SQLite tables:

- `inventory`
- `conversation_sessions`
- `processed_messages`

`processed_messages.message_id` is the idempotency key. Duplicate webhook deliveries return the stored response.

## Security decisions

- `.env` is excluded from Git.
- Secrets are stored as `SecretStr`.
- Error responses do not expose tracebacks.
- Remote image URLs block loopback, private, link-local, multicast, reserved, and unspecified addresses.
- Remote downloads are streamed and size-capped.
- PIL verifies actual image content instead of trusting filename extensions or HTTP headers.
