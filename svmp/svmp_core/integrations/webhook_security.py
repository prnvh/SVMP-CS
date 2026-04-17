"""Webhook signature verification helpers for provider inbound traffic."""

from __future__ import annotations

import base64
import hashlib
import hmac
from collections.abc import Mapping
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from pydantic import SecretStr

from svmp_core.config import Settings
from svmp_core.exceptions import SecurityError


def _secret_value(secret: SecretStr | None) -> str | None:
    """Return a non-blank secret string when configured."""

    if secret is None:
        return None
    value = secret.get_secret_value().strip()
    return value or None


def _request_url_for_signature(request_url: str, *, settings: Settings) -> str:
    """Resolve the public URL that providers used when calculating signatures."""

    public_base_url = settings.WEBHOOK_PUBLIC_BASE_URL
    if public_base_url is None or not public_base_url.strip():
        return request_url

    parsed_request = urlsplit(request_url)
    path_and_query = urlunsplit(("", "", parsed_request.path, parsed_request.query, ""))
    return f"{public_base_url.rstrip('/')}{path_and_query}"


def verify_meta_signature(
    *,
    raw_body: bytes,
    signature_header: str | None,
    settings: Settings,
) -> None:
    """Validate Meta's X-Hub-Signature-256 header."""

    app_secret = _secret_value(settings.META_APP_SECRET)
    if app_secret is None:
        raise SecurityError("META_APP_SECRET is not configured")

    if signature_header is None or not signature_header.strip().startswith("sha256="):
        raise SecurityError("missing Meta webhook signature")

    expected = "sha256=" + hmac.new(
        app_secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected, signature_header.strip()):
        raise SecurityError("invalid Meta webhook signature")


def verify_twilio_signature(
    *,
    request_url: str,
    form_payload: Mapping[str, Any],
    signature_header: str | None,
    settings: Settings,
) -> None:
    """Validate Twilio's X-Twilio-Signature header for form posts."""

    auth_token = _secret_value(settings.TWILIO_AUTH_TOKEN)
    if auth_token is None:
        raise SecurityError("TWILIO_AUTH_TOKEN is not configured")

    if signature_header is None or not signature_header.strip():
        raise SecurityError("missing Twilio webhook signature")

    public_url = _request_url_for_signature(request_url, settings=settings)
    signature_base = public_url + "".join(
        f"{key}{form_payload[key]}"
        for key in sorted(form_payload)
    )
    expected = base64.b64encode(
        hmac.new(
            auth_token.encode("utf-8"),
            signature_base.encode("utf-8"),
            hashlib.sha1,
        ).digest()
    ).decode("ascii")

    if not hmac.compare_digest(expected, signature_header.strip()):
        raise SecurityError("invalid Twilio webhook signature")


def verify_normalized_webhook_secret(
    *,
    secret_header: str | None,
    settings: Settings,
) -> None:
    """Require an explicit opt-in or shared secret for normalized test payloads."""

    configured_secret = _secret_value(settings.NORMALIZED_WEBHOOK_SECRET)
    if configured_secret is not None:
        if secret_header is None or not hmac.compare_digest(configured_secret, secret_header.strip()):
            raise SecurityError("invalid normalized webhook secret")
        return

    if settings.ALLOW_NORMALIZED_WEBHOOKS:
        return

    raise SecurityError("normalized webhook payloads are disabled")


def verify_inbound_webhook(
    *,
    provider_name: str,
    request_url: str,
    headers: Mapping[str, str],
    raw_body: bytes,
    form_payload: Mapping[str, Any] | None,
    settings: Settings,
) -> None:
    """Validate the inbound request for the resolved provider before ingesting it."""

    provider = provider_name.strip().lower()
    if provider == "meta":
        verify_meta_signature(
            raw_body=raw_body,
            signature_header=headers.get("x-hub-signature-256"),
            settings=settings,
        )
        return

    if provider == "twilio":
        verify_twilio_signature(
            request_url=request_url,
            form_payload=form_payload or {},
            signature_header=headers.get("x-twilio-signature"),
            settings=settings,
        )
        return

    if provider == "normalized":
        verify_normalized_webhook_secret(
            secret_header=headers.get("x-svmp-webhook-secret"),
            settings=settings,
        )
        return

    raise SecurityError(f"unsupported webhook provider: {provider_name}")
