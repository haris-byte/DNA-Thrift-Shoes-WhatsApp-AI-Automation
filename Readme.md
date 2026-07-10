# DNA Thrift WhatsApp AI Automation

A backend system for a WhatsApp-based thrift shoe shopping assistant.

Customers can send shoe text queries or shoe images. The backend validates incoming webhook payloads, extracts shoe information, checks inventory, applies condition-based pricing, and returns a conversational response.

## Day 1 Progress

- Created FastAPI backend
- Added health check endpoint
- Added fake WhatsApp webhook endpoint
- Added Pydantic model for incoming webhook payloads
- Tested valid and invalid payloads using Swagger docs

[✓] Add Meta webhook verification support
[✓] Keep local dev webhook working
[✓] Understand WhatsApp API pricing and limits
[✓] Prepare code for real integration

## Tech Stack

- Python
- FastAPI
- Pydantic
- Uvicorn

## Run Locally

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
``` 


## Day 2 Progress

Day 2 completed the text-query parsing path and inventory lookup/pricing logic.

### Added

- Strict `ShoeQuery` Pydantic model
- `InventoryItem` Pydantic model
- `InventoryMatchResult` Pydantic model
- Rule-based text parser
- Sample DNA Thrift inventory
- Exact match handling
- Partial match handling
- No-match handling
- Condition-based pricing

### Text Query Flow

```text
Customer text
→ WhatsAppWebhookPayload validation
→ Text parser
→ ShoeQuery
→ Inventory lookup
→ Price calculation
→ Reply preview
```

Input:

```json
{
  "sender_id": "user_123",
  "message_id": "msg_001",
  "message_type": "text",
  "text": "Do you have Air Jordan 1 size 10?",
  "image_url": null
}
```

Output:

Yes, we have Nike Air Jordan 1 Retro High in US 10.0.
Condition: 9/10.
Price: Rs. 18500.
Availability: in_stock.