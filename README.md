# SVMP

SVMP is a Mongo-backed FastAPI service for tenant-scoped WhatsApp support automation. The current system accepts inbound messages, buffers fragmented user input into a session window, runs scheduled processing to answer or escalate, and writes an immutable governance log for every decision.

Today the active runtime lives in [`svmp-core/`](./svmp-core). `svmp-platform/` is still a placeholder for future platform work and is not part of the running path.

## What The Current System Does

- accepts inbound WhatsApp traffic through a provider-aware `/webhook`
- supports three intake shapes:
  - normalized internal JSON
  - Meta WhatsApp webhook JSON
  - Twilio WhatsApp form posts
- auto-resolves `tenantId` for Meta and Twilio payloads from tenant channel mappings in MongoDB
- stores the current message window in `session_state`
- runs Workflow B on a scheduler to process ready sessions after debounce expiry
- resolves a tenant/domain, asks OpenAI to choose the best FAQ candidate, and applies a deterministic confidence gate
- sends answered replies through the active WhatsApp provider
- records answered, escalated, and cleanup decisions in `governance_logs`
- runs Workflow C on a scheduler to remove stale sessions

## Repository Layout

`svmp-core/`

- FastAPI app factory and runtime wiring
- webhook routes
- Workflow A / B / C
- Mongo repositories
- provider integrations for normalized, Meta, and Twilio payloads
- OpenAI client wrapper
- unit and integration tests

`scripts/`

- `seed_tenant.py` seeds a tenant document into MongoDB
- `seed_knowledge_base.py` seeds tenant/domain FAQ entries into MongoDB
- `verify_live_runtime.py` runs a live Workflow A -> Workflow B check against MongoDB and OpenAI
- `demo_data/` contains sample tenant and FAQ payloads

`svmp-platform/`

- reserved for future platform-facing work

## Runtime Flow

1. `POST /webhook` receives one or more inbound WhatsApp messages.
2. The webhook route resolves the provider and, when needed, resolves `tenantId` from provider identities stored in MongoDB.
3. Workflow A appends the inbound fragment(s) to the current session and resets `debounceExpiresAt`.
4. APScheduler runs Workflow B every `WORKFLOW_B_INTERVAL_SECONDS` and atomically acquires one ready session.
5. Workflow B builds an `activeQuestion` from the current message window, treats older processed windows as archived context, resolves the tenant domain, and loads active FAQ entries for that tenant/domain.
6. OpenAI ranks the FAQ candidates and returns `bestIndex`, `similarityScore`, and `reason`.
7. A deterministic threshold gate decides whether to answer or escalate.
8. Answered sessions send a reply through the session's provider and write an answered governance log.
9. Escalated sessions write an escalated governance log.
10. Workflow B archives the processed message window into `session.context`.
11. Workflow C runs every `WORKFLOW_C_INTERVAL_HOURS` to delete stale sessions.

## Quick Start

1. Create and activate a Python 3.11+ environment.
2. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and set the runtime values you need.

Minimum required values depend on provider selection:

- always required:
  - `MONGODB_URI`
  - `OPENAI_API_KEY`
- if `WHATSAPP_PROVIDER=normalized`:
  - no extra provider credentials are required
- if `WHATSAPP_PROVIDER=meta`:
  - `WHATSAPP_TOKEN`
  - `WHATSAPP_PHONE_NUMBER_ID`
  - `WHATSAPP_VERIFY_TOKEN`
- if `WHATSAPP_PROVIDER=twilio`:
  - `TWILIO_ACCOUNT_SID`
  - `TWILIO_AUTH_TOKEN`
  - `TWILIO_WHATSAPP_NUMBER`

4. Seed the demo tenant and FAQ corpus:

```bash
python scripts/seed_tenant.py
python scripts/seed_knowledge_base.py
```

5. Start the app from the repo root:

```bash
uvicorn svmp_core.main:app --app-dir svmp-core --reload --port 8000
```

6. Send a normalized local test payload:

```bash
curl -X POST http://127.0.0.1:8000/webhook ^
  -H "Content-Type: application/json" ^
  -d "{\"tenantId\":\"Stay\",\"clientId\":\"whatsapp\",\"userId\":\"9845891194\",\"text\":\"How much do your perfumes cost?\"}"
```

## Useful Validation Commands

Fast feedback on app boot, webhook intake, and end-to-end processing:

```bash
python -m pytest svmp-core/tests/integration/test_main.py
python -m pytest svmp-core/tests/integration/test_webhook_route.py
python -m pytest svmp-core/tests/integration/test_demo_smoke.py
python -m pytest svmp-core/tests/integration/test_workflow_b.py
```

Live runtime verification against real MongoDB and OpenAI:

```bash
python scripts/verify_live_runtime.py --tenant-id Stay --user-id demo-user-001 --text "What size are STAY Parfums bottles?"
```

## Current Operational Notes

- Workflow B is poll-based, not per-session scheduled. Real response time includes debounce delay plus up to one Workflow B poll interval.
- Workflow B currently sends the full active tenant/domain FAQ list to OpenAI. `OPENAI_MATCHER_CANDIDATE_LIMIT` exists in settings but is not currently applied in the matcher path.
- `USE_OPENAI_MATCHER` and `OPENAI_SHADOW_MODE` are still present in settings for compatibility, but the current Workflow B path always uses the direct OpenAI matcher.
- `LLM_MODEL` defaults to `gpt-4.1` in code. `.env.example` pins `gpt-4o-mini` for the demo configuration template.
- Only Meta supports `GET /webhook` verification. Twilio and normalized providers return `405` for verification requests.
- If outbound sending fails after Workflow B has acquired a session, the session remains latched until new inbound traffic reopens it through Workflow A.

## Documentation

- Architecture: [`ARCHITECTURE.md`](./ARCHITECTURE.md)
- Detailed architecture snapshot: [`system_architecture.md`](./system_architecture.md)
- Historical schema notes: [`docs/schema_notes.md`](./docs/schema_notes.md)
