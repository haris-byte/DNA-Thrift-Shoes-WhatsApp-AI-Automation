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