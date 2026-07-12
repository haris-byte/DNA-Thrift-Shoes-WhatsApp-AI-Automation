from app.models.meta_webhook_models import MetaWebhookPayload


def test_meta_text_payload_is_typed() -> None:
    payload = MetaWebhookPayload.model_validate(
        {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "waba-id",
                    "changes": [
                        {
                            "field": "messages",
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {
                                    "display_phone_number": "15550001111",
                                    "phone_number_id": "phone-id",
                                },
                                "messages": [
                                    {
                                        "from": "923001234567",
                                        "id": "wamid.1",
                                        "timestamp": "1700000000",
                                        "type": "text",
                                        "text": {"body": "Air Jordan 1 size 10"},
                                    }
                                ],
                                "provider_future_field": "ignored safely",
                            },
                        }
                    ],
                }
            ],
        }
    )
    message = payload.entry[0].changes[0].value.messages[0]
    assert message.sender == "923001234567"
    assert message.text is not None
    assert message.text.body == "Air Jordan 1 size 10"
