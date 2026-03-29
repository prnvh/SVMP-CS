# Demo Run Notes

These notes are the practical runbook for demoing the current `svmp-core` build.

## What Is Included Right Now

- FastAPI app factory and scheduler wiring
- webhook verification and webhook intake route
- Workflow A ingestion
- Workflow B processing
- Workflow C cleanup
- demo smoke test for ingest -> process -> governance
- demo knowledge-base seeding script and sample FAQ data

## Demo Assumptions

The current live demo path assumes all of the following are available:

- a reachable MongoDB instance
- an `OPENAI_API_KEY` for live model-backed behavior
- a tenant document already present in Mongo for the demo tenant
- a webhook verify token set in the environment

Important:

- `scripts/seed_knowledge_base.py` seeds the `knowledge_base` collection only
- it does **not** create the tenant document needed by Workflow B

## Required Environment

Minimum environment variables for the live demo:

```bash
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=svmp
OPENAI_API_KEY=your-openai-key
WHATSAPP_VERIFY_TOKEN=verify-me
```

Useful defaults already exist in code for:

- `WORKFLOW_B_INTERVAL_SECONDS=1`
- `WORKFLOW_C_INTERVAL_HOURS=24`
- `SIMILARITY_THRESHOLD=0.75`

## Install

From the repo root:

```bash
python -m venv .venv
```

Activate the virtual environment:

```powershell
.venv\Scripts\Activate.ps1
```

Then install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Tenant Prerequisite

Before running the live app against Mongo, ensure the demo tenant exists.

Example tenant document:

```json
{
  "tenantId": "Niyomilan",
  "domains": [
    {
      "domainId": "general",
      "name": "General",
      "description": "What we do, company details, and contact information",
      "keywords": ["what", "company", "contact"]
    }
  ],
  "settings": {
    "confidenceThreshold": 0.75
  }
}
```

The sample KB seed file uses:

- `tenantId = Niyomilan`
- `domainId = general`

## Seed Demo Knowledge Base

From the repo root:

```bash
python scripts/seed_knowledge_base.py --file scripts/demo_data/sample_kb.json
```

Expected result:

- the script prints how many KB entries were written
- entries are upserted into the configured `knowledge_base` collection

## Start The App

From the repo root:

```bash
python -m uvicorn --app-dir svmp-core svmp_core.main:app --host 127.0.0.1 --port 8000
```

Expected result:

- the server starts successfully
- app startup connects the database
- scheduler jobs for Workflow B and Workflow C are attached automatically

## Verify Webhook Setup

Use the configured verify token:

```bash
curl "http://127.0.0.1:8000/webhook?hub.mode=subscribe&hub.verify_token=verify-me&hub.challenge=12345"
```

Expected result:

- response status `200`
- response body `12345`

## Send A Sample Inbound Message

```bash
curl -X POST "http://127.0.0.1:8000/webhook" -H "Content-Type: application/json" -d "{\"tenantId\":\"Niyomilan\",\"clientId\":\"whatsapp\",\"userId\":\"9845891194\",\"text\":\"What do you do?\"}"
```

Expected result:

- response status `200`
- response body contains:

```json
{
  "status": "accepted",
  "sessionId": "..."
}
```

Workflow A writes or updates the active session immediately. Workflow B then processes the session on its scheduler interval.

## Fastest Proof Commands

If you need the quickest confidence check before a demo, run these from the repo root:

```bash
python -m pytest svmp-core/tests/integration/test_main.py
python -m pytest svmp-core/tests/integration/test_demo_smoke.py
python -m pytest svmp-core/tests/integration/test_seed_script.py
```

These prove:

- the app boots and wires dependencies
- the end-to-end demo flow works in the smoke path
- the KB seed script parses and writes correctly

## Current Caveats

- The README previously described the repo as scaffolding; the codebase is now beyond that stage.
- The live processor path depends on tenant data existing in Mongo.
- The live processor path also depends on valid OpenAI credentials.
- The automated smoke proof uses in-memory test doubles, which is useful for demo confidence but is not the same as a live Mongo + OpenAI run.
