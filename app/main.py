import os
from fastapi import FastAPI, Request, HTTPException, Query
from dotenv import load_dotenv

from app.models.webhook_models import WhatsAppWebhookPayload

load_dotenv()

app = FastAPI(
    title="DNA Thrift WhatsApp AI Automation",
    description="Backend API for WhatsApp-based thrift shoe inventory assistant.",
    version="0.1.0"
)

VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")


@app.get("/")
def health_check():
    return {
        "status": "running",
        "message": "DNA Thrift WhatsApp AI backend is alive."
    }


@app.post("/dev/webhook")
def receive_dev_webhook(payload: WhatsAppWebhookPayload):
    """
    Local development webhook.

    This endpoint uses our simple fake WhatsApp-style (Simulation Based) payload.
    We use this for fast testing before connecting real WhatsApp.
    """
    return {
        "reply": "Dev webhook received successfully.",
        "sender_id": payload.sender_id,
        "message_id": payload.message_id,
        "received_type": payload.message_type
    }


@app.get("/webhook")
def verify_whatsapp_webhook(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge")
):
    """
    Meta WhatsApp webhook verification endpoint.

    Meta sends a GET request to verify that this webhook belongs to us.
    If the verify token matches, we return the challenge.
    """
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return int(hub_challenge)

    raise HTTPException(status_code=403, detail="Webhook verification failed")


@app.post("/webhook")
async def receive_whatsapp_webhook(request: Request):
    """
    Real WhatsApp webhook endpoint.

    Meta sends incoming WhatsApp messages here.
    For Day 1, we only receive and inspect the payload.
    Later we will parse messages from this payload properly.
    """
    body = await request.json()

    return {
        "status": "received",
        "source": "meta_whatsapp",
        "raw_payload_preview": body
    }