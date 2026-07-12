# Test report — Days 1 to 5

## Automated result

```text
30 passed
```

Command:

```bash
pytest -q
```

## Covered areas

- FastAPI health route
- Local text webhook route
- Structured request validation errors
- Meta verification challenge
- Typed Meta text webhook processing
- WhatsApp reply invocation
- Duplicate Meta delivery suppression
- Air Force 1 vs Air Jordan 1 parser separation
- Informal/ambiguous query behavior
- Valid and invalid US sizes
- Exact inventory matching
- Partial nearby-size matching
- No-match brand alternatives
- Condition-price tiers
- Strict extra-field rejection
- OCR cross-field consistency
- Inventory-result cross-field consistency
- US/UK/EU OCR size interpretation
- Multi-turn missing-size completion
- Loop-prevention fallback
- Message idempotency
- Photo-pipeline combination using injected deterministic adapters
- Real VLM HTTP request structure with image data URL and JSON schema
- Meta webhook provider-field tolerance
- Private/local image URL blocking

## Credential-bound tests not executed in this environment

The source code contains real adapters, but the following live external checks require the owner's credentials and accounts:

1. A live OpenRouter request using the final selected image-capable model.
2. First-run EasyOCR model download and OCR on the owner's real shoe-tag images.
3. Meta WhatsApp test-number webhook delivery, media download, and outbound reply.

These are Day 6 end-to-end tests. They cannot be honestly claimed as executed without the real API keys, public callback URL, Meta app, and final image set.
