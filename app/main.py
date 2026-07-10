import os
from fastapi import FastAPI, Request, HTTPException, Query
from dotenv import load_dotenv

from app.models.webhook_models import WhatsAppWebhookPayload
from app.nlp.text_parser import parse_text_query
from app.inventory.matcher import lookup_inventory

load_dotenv()

app = FastAPI(
    title="DNA Thrift WhatsApp AI Automation",
    description="Backend API for WhatsApp-based thrift shoe inventory assistant.",
    version="0.3.0"
)

VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")


@app.get("/")
def health_check():
    return {
        "status": "running",
        "message": "DNA Thrift WhatsApp AI backend is alive.",
        "version": "0.3.0"
    }


@app.post("/dev/webhook")
def receive_dev_webhook(payload: WhatsAppWebhookPayload):
    if payload.message_type == "text":
        parser_result = parse_text_query(payload.text)

        if parser_result.clarification_needed:
            return {
                "status": "clarification_needed",
                "sender_id": payload.sender_id,
                "message_id": payload.message_id,
                "message_type": payload.message_type,
                "parsed_query": parser_result.query.model_dump(),
                "missing_fields": parser_result.missing_fields,
                "reply": parser_result.clarification_question
            }

        inventory_result = lookup_inventory(parser_result.query)

        return {
            "status": "inventory_checked",
            "sender_id": payload.sender_id,
            "message_id": payload.message_id,
            "message_type": payload.message_type,
            "parsed_query": parser_result.query.model_dump(),
            "inventory_result": inventory_result.model_dump(),
            "reply": inventory_result.message
        }

    return {
        "status": "received",
        "message": "Image messages will be processed in the vision/OCR pipeline on Day 3.",
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
@app.get("/dev/debug-parser")
def debug_parser(text: str):
    result = parse_text_query(text)
    return result.model_dump()