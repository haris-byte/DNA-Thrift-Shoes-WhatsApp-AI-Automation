from fastapi.testclient import TestClient

from app.main import create_app


def test_health_endpoint(settings) -> None:
    client = TestClient(create_app(settings))
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "running"


def test_dev_text_flow(settings) -> None:
    client = TestClient(create_app(settings))
    response = client.post(
        "/dev/webhook",
        json={
            "sender_id": "api_user",
            "message_id": "api_msg_1",
            "message_type": "text",
            "text": "Air Jordan 1 size 10",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["state"] == "AWAITING_PURCHASE_INTENT"
    assert "18,500" in body["reply"]


def test_structured_validation_error(settings) -> None:
    client = TestClient(create_app(settings))
    response = client.post(
        "/dev/webhook",
        json={
            "sender_id": "api_user",
            "message_id": "api_msg_2",
            "message_type": "text",
            "text": "   ",
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "request_validation_failed"


def test_meta_verification(settings) -> None:
    client = TestClient(create_app(settings))
    response = client.get(
        "/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "test-token",
            "hub.challenge": "12345",
        },
    )
    assert response.status_code == 200
    assert response.text == "12345"


def test_meta_text_webhook_processes_and_sends_reply(settings, monkeypatch) -> None:
    configured = settings.model_copy(
        update={
            "whatsapp_access_token": "test-access-token",
            "whatsapp_phone_number_id": "phone-id",
        }
    )
    app = create_app(configured)
    sent: list[tuple[str, str]] = []
    monkeypatch.setattr(
        app.state.container.meta_client,
        "send_text",
        lambda recipient, text: sent.append((recipient, text)),
    )
    client = TestClient(app)
    response = client.post(
        "/webhook",
        json={
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "waba",
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
                                        "id": "wamid.meta.1",
                                        "timestamp": "1700000000",
                                        "type": "text",
                                        "text": {"body": "Air Jordan 1 size 10"},
                                    }
                                ],
                            },
                        }
                    ],
                }
            ],
        },
    )
    assert response.status_code == 200
    assert response.json()["messages_received"] == 1
    assert response.json()["replies_sent"] == 1
    assert sent and sent[0][0] == "923001234567"
    assert "Air Jordan 1" in sent[0][1]


def test_duplicate_meta_delivery_does_not_resend_reply(settings, monkeypatch) -> None:
    configured = settings.model_copy(
        update={
            "whatsapp_access_token": "test-access-token",
            "whatsapp_phone_number_id": "phone-id",
        }
    )
    app = create_app(configured)
    sent: list[tuple[str, str]] = []
    monkeypatch.setattr(
        app.state.container.meta_client,
        "send_text",
        lambda recipient, text: sent.append((recipient, text)),
    )
    client = TestClient(app)
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "waba",
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
                                    "id": "wamid.duplicate.1",
                                    "timestamp": "1700000000",
                                    "type": "text",
                                    "text": {"body": "Air Jordan 1 size 10"},
                                }
                            ],
                        },
                    }
                ],
            }
        ],
    }
    first = client.post("/webhook", json=payload)
    second = client.post("/webhook", json=payload)
    assert first.json()["replies_sent"] == 1
    assert second.json()["replies_sent"] == 0
    assert len(sent) == 1


def test_real_image_route_refuses_fake_fallback_without_vlm_key(settings, tmp_path) -> None:
    from PIL import Image

    image_path = tmp_path / "shoe.png"
    Image.new("RGB", (50, 50), "white").save(image_path)
    client = TestClient(create_app(settings))
    with image_path.open("rb") as image_file:
        response = client.post(
            "/dev/upload",
            data={"sender_id": "photo_user", "message_id": "photo_no_key_1"},
            files={"image": ("shoe.png", image_file, "image/png")},
        )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "configuration_error"
