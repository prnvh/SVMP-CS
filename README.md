# SVMP

SVMP is a governance and orchestration layer for AI-powered customer service systems. It is a code-first FastAPI service that receives WhatsApp conversations, merges fragmented customer messages into coherent requests, routes them safely, and keeps a governance trail of what happened.

## Direction

This repository is the main SVMP application. Product, runtime, tenant, security, and deployment concerns belong in this repo as one system.

The near-term goal is to:

- keep the SVMP runtime testable from the start
- use repository interfaces so business logic is not tightly coupled to MongoDB
- ship a production-oriented WhatsApp automation service from this codebase
- leave room for a later PostgreSQL adapter if it becomes worthwhile

## Repository Structure

`svmp/`

- FastAPI app and webhook intake
- workflows for ingest, processing, and cleanup
- models, config, logging, exceptions, and DB interfaces
- MongoDB implementation first
- OpenAI and WhatsApp provider integrations
- tests for the application runtime

`scripts/`

- one-off setup and demo scripts
- knowledge-base seeding and local/dev utilities

`docs/`

- architecture notes, provider setup, and schema notes
- public landing page plan
- customer portal product, API, auth, and billing contracts

## Runtime Flow

1. A webhook receives a customer message.
2. Workflow A writes or updates session state and starts the debounce window.
3. Workflow B picks up ready sessions, classifies intent/domain, queries the KB, generates or routes a response, and records governance data.
4. Workflow C removes stale session state.

## Status

SVMP is now runnable in its Mongo-first app shape:

- the FastAPI app boots and wires Workflow B / Workflow C scheduler jobs
- webhook verification and inbound intake routes are available
- provider POST webhooks are signature-checked before SVMP ingests messages
- Workflow A, Workflow B, and Workflow C all have integration coverage
- a demo smoke test proves ingest -> process -> governance in one end-to-end path
- a repeatable knowledge-base seed script is available under `scripts/`

Provider connection details live in [`docs/provider_connection.md`](docs/provider_connection.md).
Public landing page planning lives in [`docs/landing_page.md`](docs/landing_page.md).
Customer portal planning starts in [`docs/customer_portal.md`](docs/customer_portal.md), with API contracts in [`docs/dashboard_api.md`](docs/dashboard_api.md) and auth/billing rules in [`docs/auth_billing_model.md`](docs/auth_billing_model.md).

Production deploys should track the latest GitHub head together with the active Vercel environment configuration.

## Quick Validation

From the repo root, these commands give the fastest proof that the current app is wired correctly:

```bash
python -m pytest svmp/tests/integration/test_main.py
python -m pytest svmp/tests/integration/test_demo_smoke.py
python -m pytest svmp/tests/integration/test_seed_script.py
```
