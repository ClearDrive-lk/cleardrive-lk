import json
from unittest.mock import AsyncMock

import pytest
from app.services.email import _get_resend_api_key, send_email
from app.services.email_queue import email_queue


@pytest.mark.asyncio
async def test_send_email_smtp(mocker):
    # Mock settings so it goes to SMTP
    mocker.patch("app.services.email.settings.RESEND_API_KEY", None)
    mocker.patch("app.services.email.settings.SMTP_HOST", "smtp.example.com")
    mocker.patch("app.services.email.settings.SMTP_PORT", 587)

    mock_send = mocker.patch("aiosmtplib.send", new_callable=AsyncMock)
    mock_send.return_value = ({}, "250 OK")

    result = await send_email("test@example.com", "Test Subject", "<p>Test</p>", "Test")

    assert result is True
    mock_send.assert_called_once()


@pytest.mark.asyncio
async def test_email_queue_enqueue(mocker):
    # Mock redis
    mock_redis = AsyncMock()
    mocker.patch("app.services.email_queue.get_redis", return_value=mock_redis)

    email_id = await email_queue.enqueue(
        to_email="test@example.com",
        subject="Queued Subject",
        html_body="<p>Queued</p>",
        priority=1,
        template_name="status_change.html",
        template_data={"order_id": "123"},
    )

    assert isinstance(email_id, str)
    mock_redis.zadd.assert_called_once()
    queued_payload = json.loads(mock_redis.zadd.call_args.args[1].popitem()[0])
    assert queued_payload["template_name"] == "status_change.html"
    assert queued_payload["template_data"] == {"order_id": "123"}


@pytest.mark.asyncio
async def test_send_email_resend(mocker):
    # Mock settings so it goes to Resend
    mocker.patch("app.services.email.settings.RESEND_API_KEY", "re_test_key")

    mock_post = mocker.patch("httpx.AsyncClient.post", new_callable=AsyncMock)
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    result = await send_email("test@example.com", "Test Subject", "<p>Test</p>")

    assert result is True
    mock_post.assert_called_once()


def test_get_resend_api_key_prefers_explicit_setting(mocker):
    mocker.patch("app.services.email.settings.RESEND_API_KEY", "re_explicit_key")
    mocker.patch("app.services.email.settings.SMTP_PASSWORD", "smtp-password")

    assert _get_resend_api_key() == "re_explicit_key"


def test_get_resend_api_key_accepts_resend_key_in_smtp_password(mocker):
    mocker.patch("app.services.email.settings.RESEND_API_KEY", None)
    mocker.patch("app.services.email.settings.SMTP_PASSWORD", "re_from_smtp_password")

    assert _get_resend_api_key() == "re_from_smtp_password"


def test_get_resend_api_key_rejects_plain_smtp_password(mocker):
    mocker.patch("app.services.email.settings.RESEND_API_KEY", None)
    mocker.patch("app.services.email.settings.SMTP_PASSWORD", "plain-smtp-password")

    assert _get_resend_api_key() is None
