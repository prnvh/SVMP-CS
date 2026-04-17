# Provider Connection Flow

Users do not connect to SVMP by sending a "Meta webhook API" value into chat. SVMP exposes a webhook endpoint, and each provider is configured to call that endpoint.

## Meta WhatsApp

1. Deploy SVMP publicly with HTTPS.
2. Set `WEBHOOK_PUBLIC_BASE_URL` to the public origin, for example `https://svmp.example.com`.
3. In the Meta developer app, configure the WhatsApp callback URL as:

```text
https://svmp.example.com/webhook
```

4. Use the same verify token in Meta and in `WHATSAPP_VERIFY_TOKEN`.
5. Set `META_APP_SECRET` so SVMP can validate `X-Hub-Signature-256` on every inbound POST.
6. Store the tenant's WhatsApp identifiers in the tenant document:

```json
{
  "tenantId": "Stay",
  "channels": {
    "meta": {
      "phoneNumberIds": ["1234567890"],
      "displayNumbers": ["+15551234567"]
    }
  }
}
```

When Meta sends a message webhook, SVMP reads the `phone_number_id` / display number from the payload and resolves the tenant from `channels.meta`.

## Twilio WhatsApp

1. Configure the Twilio WhatsApp inbound message webhook as:

```text
https://svmp.example.com/webhook
```

2. Set `TWILIO_AUTH_TOKEN`; SVMP uses it to validate `X-Twilio-Signature`.
3. Store the tenant's Twilio identifiers in the tenant document:

```json
{
  "tenantId": "Stay",
  "channels": {
    "twilio": {
      "whatsappNumbers": ["whatsapp:+14155238886"],
      "accountSids": ["AC123"]
    }
  }
}
```

## Current Limitation

Inbound tenant resolution is tenant-aware, but outbound Meta/Twilio credentials are still runtime-wide environment variables. That means the current app is suitable for a single live provider account or controlled demos. Multi-account production needs per-tenant provider credentials before unrelated customers can safely connect their own WhatsApp Business accounts.

## Internal Normalized Payloads

The internal normalized webhook schema is disabled by default for public safety. For trusted local tools, either set `ALLOW_NORMALIZED_WEBHOOKS=true` or set `NORMALIZED_WEBHOOK_SECRET` and send it as:

```text
X-SVMP-Webhook-Secret: <secret>
```
