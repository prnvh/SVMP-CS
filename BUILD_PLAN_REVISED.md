# SVMP Revised Build Plan

## Goal

Build a Mongo-first, demoable `svmp-core` as quickly as possible without sacrificing testability or future portability. The immediate target is a working code version of the core product that can run against the existing MongoDB cluster and reflect the n8n prototype behavior closely enough for a pre-demo build.

This plan is intentionally:

- file-by-file instead of phase-heavy
- commit-by-commit
- Mongo-first
- testable from the start
- optimized for parallel work where safe

`svmp-platform` is deferred until after `svmp-core` is stable and demoable.

## Team Roles

### Lead Architect (you)

- Own the full architecture and technical direction.
- Own the main coding surface across the repo.
- Define module boundaries, data contracts, repository interfaces, runtime flow, and merge standards.
- Implement the highest-risk and most central code paths first.
- Review and approve integration points and workflow wiring.

### Product Lead (cofounder)

- Own product behavior, demo goals, and alignment to the original n8n workflow behavior.
- Support implementation inside the architecture defined by the Lead Architect.
- Help code product-facing modules, tests, fixtures, and demo scripts.
- Pressure-test user journeys, operator flow, and response behavior.

## Ground Rules

- Every major change lands as one GitHub commit.
- Every commit must leave the repo in a sanity-testable state.
- Tests can be minor at first, but every new file or module should have a confirming test.
- Business logic must depend on interfaces, not raw Mongo calls scattered through the codebase.
- MongoDB is the first implementation, not the only possible one.
- `svmp-core` comes before `svmp-platform`.
- Do not start the SaaS wrapper until the core app can ingest, process, and respond in a demo flow.

## Architecture Direction

### Runtime shape

1. Webhook receives inbound message.
2. Workflow A stores message in session state and sets debounce expiry.
3. Workflow B picks up ready sessions, determines domain and intent, retrieves KB context, generates or routes a response, and writes governance data.
4. Workflow C cleans old session state.

### Inherited n8n Workflow Behavior

The code rebuild should preserve the old n8n workflow behavior unless a later change is explicitly documented.

Workflow A: Ingestor

- Triggered by every inbound message.
- Looks up `session_state` using the identity tuple:
  - `tenantId`
  - `clientId`
  - `userId`
- If a session is found:
  - append the new message
  - update `updatedAt`
  - reset `debounceExpiresAt` to `now + 2.5 seconds`
  - force `processing = false`
- If a session is not found:
  - create a new session document
  - initialize `messages`
  - set `createdAt`, `updatedAt`, and `debounceExpiresAt`
  - set `processing = false`

Workflow B: Processor

- Triggered every 1 second.
- Finds sessions that are ready and not currently processing.
- Atomically sets `processing = true` before processing each session.
- Aggregates all message fragments into one `combinedText`.
- If tenant tags indicate `ecom` or `d2c`, the flow supports a future order-ID branch before normal FAQ handling.
- Otherwise:
  - fetch tenant details
  - fetch domains
  - choose a domain from `combinedText`
  - fetch tenant/domain FAQs
  - call OpenAI to select the best match and produce a similarity score
- If the score is above threshold:
  - auto-answer
  - write governance log
- If the score is below threshold:
  - escalate to human
  - write governance log

Workflow C: Janitor

- Triggered every 24 hours.
- Finds stale sessions.
- Writes a governance log recording closure.
- Deletes stale sessions directly after logging closure.

### Database direction

- Use MongoDB first because the cluster and sample schemas already exist.
- Keep DB access behind repository interfaces.
- Avoid Mongo-specific assumptions in workflows and routes where possible.
- Make a future Postgres adapter possible without rewriting the core business flow.

### Canonical Identity Tuple

The rebuild should standardize on:

- `tenantId`: real company identifier, such as `Niyomilan`
- `clientId`: channel/source type such as `whatsapp`, `gmail`, or `website`
- `userId`: end-user identifier such as phone number, email address, or equivalent source-native identifier

Historical test identifiers like `t_001` should not be treated as canonical tenant identity in the rebuilt codebase.

### Canonical Mongo Collection Shapes

These are the current best-known target shapes for the rebuild, based on the old n8n implementation and the latest notes/screenshots supplied on March 29, 2026.

`session_state`

```json
{
  "_id": "ObjectId",
  "tenantId": "Niyomilan",
  "clientId": "whatsapp",
  "userId": "9845891194",
  "status": "open",
  "processing": false,
  "messages": [
    {
      "text": "hi",
      "at": "2026-01-22T16:44:14.369Z"
    }
  ],
  "createdAt": "ISODate",
  "updatedAt": "ISODate",
  "debounceExpiresAt": "ISODate"
}
```

Purpose:

- mutable active session state
- message buffering for soft debounce
- locking and lifecycle control

`knowledge_base`

```json
{
  "_id": "faq_001",
  "tenantId": "Niyomilan",
  "domainId": "general",
  "question": "What does our company do?",
  "answer": "We are Niyomilan...",
  "tags": ["us"],
  "active": true,
  "createdAt": "ISODate",
  "updatedAt": "ISODate"
}
```

Purpose:

- tenant-scoped FAQ corpus
- domain-filtered retrieval before matching

`tenants`

```json
{
  "tenantId": "Niyomilan",
  "domains": [
    {
      "domainId": "sales",
      "name": "Sales",
      "description": "Questions about product sales, pricing, discounts"
    },
    {
      "domainId": "general",
      "name": "General",
      "description": "Questions about company, contact info, general policy"
    }
  ],
  "tags": ["marketplace", "ecom"],
  "settings": {
    "confidenceThreshold": 0.75,
    "aiPromptExamples": [
      "Intent examples for sales domain",
      "Intent examples for general domain"
    ]
  },
  "contactInfo": {
    "email": "redacted@example.com",
    "phone": "redacted"
  },
  "createdAt": "ISODate",
  "updatedAt": "ISODate"
}
```

Purpose:

- tenant-level routing and configuration
- domain metadata
- tags such as `ecom` and `d2c` for branching behavior

`governance_logs`

```json
{
  "_id": "ObjectId",
  "tenantId": "Niyomilan",
  "clientId": "whatsapp",
  "userId": "9845891194",
  "decision": "answered",
  "similarityScore": 0.82,
  "combinedText": "hi what do you guys do",
  "answerSupplied": "We are Niyomilan...",
  "timestamp": "ISODate",
  "metadata": {}
}
```

Purpose:

- immutable audit log of every automated decision
- future basis for dashboards, debugging, and analytics

### Historical Mismatch Notes

Older notes described:

- `sessionId` rather than relying on Mongo `_id`
- `expiresAt` rather than `debounceExpiresAt`

The rebuild should follow the newer shape centered on:

- Mongo `_id`
- `debounceExpiresAt`

unless a later schema review explicitly changes this.

### Scope for this plan

In scope now:

- `svmp-core`
- Mongo repositories
- FastAPI webhook surface
- demo seeding utilities
- unit and integration sanity tests

Deferred:

- `svmp-platform`
- tenant auth/admin surface
- encryption/key vault concerns
- production hardening beyond demo readiness

## Planned File Structure

```text
svmp-core/
  pyproject.toml
  svmp_core/
    __init__.py
    config.py
    exceptions.py
    logger.py
    main.py
    models/
      __init__.py
      session.py
      knowledge.py
      governance.py
      webhook.py
    db/
      __init__.py
      base.py
      mongo.py
    core/
      __init__.py
      identity_frame.py
      domain_filter.py
      intent_fork.py
      similarity_gate.py
      response_gen.py
      governance.py
      escalation.py
    integrations/
      __init__.py
      openai_client.py
      whatsapp.py
      slack.py
    routes/
      __init__.py
      webhook.py
    workflows/
      __init__.py
      workflow_a.py
      workflow_b.py
      workflow_c.py
  tests/
    conftest.py
    test_config.py
    test_logger.py
    unit/
    integration/
scripts/
  seed_knowledge_base.py
  demo_data/
    sample_kb.json
docs/
  schema_notes.md
```

## Independent Commit Tracks

This section replaces a single shared sequence with two explicit commit tracks. Each commit is intended to be independently reviewable, independently testable, and small enough to merge without dragging in unrelated work.

Dependency notation:

- `Depends on:` means the commit should not start until that dependency is merged.
- `Independent of:` means both commits can be worked on and merged in either order.

### Shared Setup Commits

These happen first because both tracks depend on them.

#### Shared Commit S1: Repo Contract and Schema Snapshot

Primary owner: Lead Architect  
Support: Product Lead

Files:

- `README.md`
- `BUILD_PLAN_REVISED.md`
- `docs/schema_notes.md`

Test:

- manual schema sanity check against the current Mongo collections, notes, and screenshots
- manual confirmation that Workflow A, Workflow B, and Workflow C are described accurately

Done means:

- one written architecture contract exists
- one written schema contract exists
- one written inherited n8n workflow reference exists

#### Shared Commit S2: Package Bootstrap and Settings

Primary owner: Lead Architect

Files:

- `svmp-core/svmp_core/__init__.py`
- `svmp-core/svmp_core/config.py`
- `svmp-core/tests/test_config.py`

Test:

- settings import works
- env override works
- required values validate correctly

Done means:

- all future modules can import shared settings

#### Shared Commit S3: Logging and Exceptions

Primary owner: Lead Architect

Files:

- `svmp-core/svmp_core/logger.py`
- `svmp-core/svmp_core/exceptions.py`
- `svmp-core/tests/test_logger.py`
- `svmp-core/tests/test_exceptions.py`

Test:

- logger creation smoke
- exception hierarchy smoke

Done means:

- later commits share the same logging and exception base

#### Shared Commit S4: Models

Primary owner: Lead Architect  
Support: Product Lead

Files:

- `svmp-core/svmp_core/models/__init__.py`
- `svmp-core/svmp_core/models/session.py`
- `svmp-core/svmp_core/models/knowledge.py`
- `svmp-core/svmp_core/models/governance.py`
- `svmp-core/svmp_core/models/webhook.py`
- `svmp-core/tests/unit/test_models.py`

Test:

- model validation and defaults
- webhook alias handling

Done means:

- app-level contracts are frozen enough for parallel work

#### Shared Commit S5: Repository Interfaces

Primary owner: Lead Architect

Files:

- `svmp-core/svmp_core/db/__init__.py`
- `svmp-core/svmp_core/db/base.py`
- `svmp-core/tests/unit/test_db_base.py`

Test:

- interface existence
- abstract base smoke checks

Done means:

- DB implementation and workflow logic can now split safely

## Lead Architect Track

### LA-1: Mongo Repository Implementation

Depends on: `S5`  
Independent of: `PL-1`, `PL-2`

Files:

- `svmp-core/svmp_core/db/mongo.py`
- `svmp-core/tests/integration/test_db_mongo.py`

Test:

- connect/disconnect smoke
- session create/get/update
- KB insert/list
- governance log create

Done means:

- a real Mongo-backed persistence layer exists

### LA-2: Identity Frame

Depends on: `S4`, `S5`  
Independent of: `PL-1`, `PL-2`, `PL-3`

Files:

- `svmp-core/svmp_core/core/__init__.py`
- `svmp-core/svmp_core/core/identity_frame.py`
- `svmp-core/tests/unit/test_identity_frame.py`

Test:

- valid identity builds
- invalid identity fails

Done means:

- workflows have a stable identity object

### LA-3: Similarity Gate

Depends on: `S4`, `S5`  
Independent of: `PL-2`, `PL-3`

Files:

- `svmp-core/svmp_core/core/similarity_gate.py`
- `svmp-core/tests/unit/test_similarity_gate.py`

Test:

- scoring behavior
- threshold pass/fail
- no candidate behavior

Done means:

- KB confidence logic is isolated and tested

### LA-4: Governance Helpers

Depends on: `S4`, `S5`  
Independent of: `PL-2`, `PL-3`

Files:

- `svmp-core/svmp_core/core/governance.py`
- `svmp-core/tests/unit/test_governance.py`

Test:

- governance log helper creates expected model payload

Done means:

- outcome logging is centralized before Workflow B

### LA-5: Escalation Stub

Depends on: `S3`, `S4`  
Independent of: `PL-2`, `PL-3`

Files:

- `svmp-core/svmp_core/core/escalation.py`
- `svmp-core/tests/unit/test_escalation.py`

Test:

- no-op escalation returns predictably
- failure paths are wrapped predictably

Done means:

- low-confidence and failure branches have a clean interface

### LA-6: Workflow A

Depends on: `LA-1`, `LA-2`, `S4`  
Independent of: `PL-4`, `PL-5`

Files:

- `svmp-core/svmp_core/workflows/workflow_a.py`
- `svmp-core/tests/integration/test_workflow_a.py`

Test:

- new inbound message creates session
- follow-up inbound behavior matches chosen schema
- invalid input fails safely

Done means:

- inbound messages can be persisted and debounced

### LA-7: Workflow B

Depends on: `LA-1`, `LA-2`, `LA-3`, `LA-4`, `LA-5`, `PL-2`, `PL-3`  
Independent of: `PL-6`

Files:

- `svmp-core/svmp_core/workflows/workflow_b.py`
- `svmp-core/tests/integration/test_workflow_b.py`

Test:

- happy-path informational flow
- low-confidence path
- internal-error path

Done means:

- the central processing loop exists end-to-end

### LA-8: App Factory and Scheduler

Depends on: `LA-6`, `LA-7`, `PL-5`  
Independent of: `PL-6`

Files:

- `svmp-core/svmp_core/main.py`
- `svmp-core/tests/integration/test_main.py`

Test:

- app boots
- startup/shutdown lifecycle works
- scheduler jobs attach
- routes register

Done means:

- `svmp-core` is runnable

### LA-9: Demo Smoke Test

Depends on: `LA-8`, `PL-6`  
Independent of: none

Files:

- `svmp-core/tests/integration/test_demo_smoke.py`

Test:

- ingest -> process -> governance smoke flow with mocked external calls

Done means:

- there is one proof the core app is demoable

## Product Lead Track

### PL-1: Shared Test Fixtures and Mocks

Depends on: `S4`, `S5`  
Independent of: `LA-1`, `LA-2`

Files:

- `svmp-core/tests/conftest.py`
- optional `svmp-core/tests/unit/test_fixtures_smoke.py`

Test:

- fixture import smoke
- sample fixture object sanity

Done means:

- both tracks can add tests faster with less duplication

### PL-2: Domain Filter

Depends on: `S2`, `S3`, `S4`  
Independent of: `LA-1`, `LA-2`, `LA-3`

Files:

- `svmp-core/svmp_core/core/domain_filter.py`
- `svmp-core/tests/unit/test_domain_filter.py`

Test:

- keyword match
- fallback behavior
- invalid query behavior

Done means:

- product domain routing rules are explicit

### PL-3: Intent Fork

Depends on: `S3`, `S4`  
Independent of: `LA-1`, `LA-2`, `LA-3`

Files:

- `svmp-core/svmp_core/core/intent_fork.py`
- `svmp-core/tests/unit/test_intent_fork.py`

Test:

- informational detection
- transactional detection
- unknown/safe fallback

Done means:

- Workflow B can branch by product behavior

### PL-4: OpenAI Client Wrapper

Depends on: `S2`, `S3`  
Independent of: `LA-3`, `LA-4`, `LA-5`

Files:

- `svmp-core/svmp_core/integrations/__init__.py`
- `svmp-core/svmp_core/integrations/openai_client.py`
- `svmp-core/tests/integration/test_openai_client.py`

Test:

- client creation/caching
- embedding mock call
- completion mock call
- invalid input behavior

Done means:

- all OpenAI traffic goes through one wrapper

### PL-5: Webhook Route

Depends on: `S4`, `LA-6`  
Independent of: `LA-7`

Files:

- `svmp-core/svmp_core/routes/__init__.py`
- `svmp-core/svmp_core/routes/webhook.py`
- `svmp-core/tests/integration/test_webhook_route.py`

Test:

- GET verification
- POST intake path
- malformed payload path

Done means:

- external entrypoint exists for the app

### PL-6: Workflow C

Depends on: `LA-1`  
Independent of: `LA-7`, `PL-5`

Files:

- `svmp-core/svmp_core/workflows/workflow_c.py`
- `svmp-core/tests/integration/test_workflow_c.py`

Test:

- cleanup retention window
- DB failure path

Done means:

- maintenance loop exists and is test-backed

### PL-7: Response Generator

Depends on: `PL-4`, `S4`  
Independent of: `LA-4`, `LA-5`

Files:

- `svmp-core/svmp_core/core/response_gen.py`
- `svmp-core/tests/unit/test_response_gen.py`

Test:

- successful mocked generation
- no-KB fallback
- wrapped failure path

Done means:

- customer-facing answer generation exists behind one function

### PL-8: Seed Script and Demo KB Data

Depends on: `LA-1`, `PL-4`  
Independent of: `LA-8`

Files:

- `scripts/seed_knowledge_base.py`
- `scripts/demo_data/sample_kb.json`
- `svmp-core/tests/integration/test_seed_script.py`

Test:

- sample file parses
- transform behavior is correct
- mocked repository write path works

Done means:

- demo data can be loaded repeatably

### PL-9: Demo Run Notes

Depends on: `LA-8`, `PL-8`  
Independent of: none

Files:

- `README.md`
- optional demo notes file under `docs/`

Test:

- manual run-through checklist:
  - install works
  - app boots
  - seed path works
  - sample webhook flow works

Done means:

- the repo is easy to explain and run before demo day

## Merge Order Summary

The recommended merge order is:

1. `S1` -> `S2` -> `S3` -> `S4` -> `S5`
2. Parallel start:
   - Lead Architect: `LA-1`, `LA-2`
   - Product Lead: `PL-1`, `PL-2`, `PL-3`, `PL-4`
3. Then:
   - Lead Architect: `LA-3`, `LA-4`, `LA-5`, `LA-6`
   - Product Lead: `PL-6`, `PL-7`
4. Then:
   - Product Lead: `PL-5`, `PL-8`
   - Lead Architect: `LA-7`
5. Then:
   - Lead Architect: `LA-8`
   - Product Lead: `PL-9`
6. Final proof:
   - Lead Architect: `LA-9`

## Testing Standard Per Commit

Each commit should include the smallest test that proves the new file or module is wired correctly.

Examples:

- config file: settings load and env override
- model file: validate required fields and defaults
- repository file: create/get/update smoke
- workflow file: happy path plus one failure path
- route file: request/response smoke using test client
- script file: parser and one mocked write path

The aim is not exhaustive coverage at the start. The aim is to prevent silent broken wiring.

## Commit Rules

- Keep commits narrow.
- Do not mix architecture rewrites with product tuning in one commit.
- Do not add a new module without at least one confirming test.
- Prefer mock-based tests for external APIs.
- Prefer real test collections for Mongo repository integration tests when feasible.
- Document any schema assumption the moment it becomes code.

## Deferred Until After Demo

- `svmp-platform` implementation
- tenant isolation layer
- admin routes
- key vault and encryption
- advanced observability
- production deployment assets
- DB portability work beyond keeping interfaces clean

## Definition of "Core Running"

The core is considered running when all of the following are true:

- FastAPI app boots locally
- webhook verification route works
- inbound webhook payload creates or updates session state
- scheduler can trigger Workflow B and Workflow C
- Workflow B can resolve at least one demo informational query
- governance logs are written
- demo KB can be seeded from file
- there is one end-to-end smoke test proving the path

## Hand-off Notes

If something is unclear during execution:

- the Lead Architect decides architecture and boundary questions
- the Product Lead decides product behavior questions unless they require architectural change
- if a change affects contracts, pause and align before merging
