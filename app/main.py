import os
from fastapi import FastAPI, Request, HTTPException, Query
from dotenv import load_dotenv

from app.models.webhook_models import WhatsAppWebhookPayload
from app.services.text_parser import parse_text_query

load_dotenv()

app = FastAPI(
    title="DNA Thrift WhatsApp AI Automation",
    description="Backend API for WhatsApp-based thrift shoe inventory assistant.",
    version="0.2.0"
)

VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")


@app.get("/")
def health_check():
    return {
        "status": "running",
        "message": "DNA Thrift WhatsApp AI backend is alive.",
        "version": "0.2.0"
    }


@app.post("/dev/webhook")
def receive_dev_webhook(payload: WhatsAppWebhookPayload):
    if payload.message_type == "text":
        parser_result = parse_text_query(payload.text)

        return {
            "status": "parsed",
            "sender_id": payload.sender_id,
            "message_id": payload.message_id,
            "message_type": payload.message_type,
            "parsed_query": parser_result.query.model_dump(),
            "missing_fields": parser_result.missing_fields,
            "clarification_needed": parser_result.clarification_needed,
            "clarification_question": parser_result.clarification_question
        }

    return {
        "status": "received",
        "message": "Image messages will be processed in the vision/OCR pipeline later.",
        "sender_id": payload.sender_id,
        "message_id": payload.message_id,
        "message_type": payload.message_type
    }


@app.get("/webhook")
def verify_whatsapp_webhook(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge")
):
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return int(hub_challenge)

    raise HTTPException(status_code=403, detail="Webhook verification failed")


@app.post("/webhook")
async def receive_whatsapp_webhook(request: Request):
    body = await request.json()

    return {
        "status": "received",
        "source": "meta_whatsapp",
        "raw_payload_preview": body
    }