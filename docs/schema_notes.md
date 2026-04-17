# SVMP Schema Notes

## Purpose

This document is the shared schema and behavior snapshot for the Mongo-first rebuild of SVMP. It captures the best-known state of the old n8n implementation as of March 29, 2026 and defines the canonical shapes the code version should target first.

This file is the schema contract for shared commit `S1`.


## Canonical Identity Tuple

All active-session lookups should use:

- `tenantId`
- `clientId`
- `userId`

Definitions:
- `tenantId`: real company identifier, such as `Niyomilan`
- `clientId`: source/channel type such as `whatsapp`, `gmail`, or `website`
- `userId`: end-user identifier such as a phone number, email address, or equivalent source-native key

Notes:
- Historical test IDs such as `t_001` are not canonical.
- Historical internal-looking client IDs such as `c_002` should not define the rebuild contract.

## Workflow Reference

### Workflow A: Ingestor

Purpose:

- buffer fragmented inbound messages into active session state
- implement soft debounce by resetting the session expiry window

Behavior:

- triggered on every inbound message
- find existing `session_state` document by the identity tuple
- if found:
  - append the new message
  - update `updatedAt`
  - set `debounceExpiresAt = now + 2.5 seconds`
  - force `processing = false`
- if not found:
  - create a new session document
  - initialize `messages`
  - set `createdAt`, `updatedAt`, and `debounceExpiresAt`
  - set `processing = false`

### Workflow B: Processor

Purpose:

- process ready sessions exactly once
- choose the best FAQ response or escalate

Behavior:

- triggered every 1 second
- find sessions where:
  - `debounceExpiresAt <= now`
  - `processing = false`
- atomically set `processing = true`
- aggregate messages into one `combinedText`
- if tenant tags include `ecom` or `d2c`, support the future order-ID path before standard FAQ handling
- otherwise:
  - fetch tenant metadata
  - fetch available domains
  - choose the most relevant domain
  - fetch FAQs for the selected tenant/domain
  - call OpenAI to choose best match and return similarity score
- if similarity score is above threshold:
  - auto-answer
  - write to `governance_logs`
- if similarity score is below threshold:
  - escalate to human
  - write to `governance_logs`

### Workflow C: Janitor

Purpose:

- remove stale active sessions and record closure

Behavior:

- triggered every 24 hours
- find stale sessions
- write closure event into `governance_logs`
- directly delete stale sessions after logging closure

## Canonical Collection Shapes

### `session_state`

Purpose:

- mutable active state for the current conversation/session
- debounce buffer
- processing lock

Target shape:

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
    },
    {
      "text": "what do you guys do",
      "at": "2026-01-22T16:44:20.192Z"
    }
  ],
  "createdAt": "ISODate",
  "updatedAt": "ISODate",
  "debounceExpiresAt": "ISODate"
}
```

Field notes:

- `status` should support at least `open` and `closed`
- `processing` is the exactly-once lock flag for Workflow B
- `messages` is append-only while the session is active
- `debounceExpiresAt` is the processing readiness time

### `knowledge_base`

Purpose:

- tenant-scoped FAQ corpus used for retrieval and answer selection

Target shape:

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

Field notes:

- `domainId` is used to narrow FAQ search space before model matching
- `active` should allow safe deactivation without deleting the entry
- embeddings are not included in the current visible sample and should be treated as an implementation detail until confirmed

### `tenants`

Purpose:

- tenant metadata
- domain metadata
- threshold and routing settings
- future branching behavior such as ecom or d2c

Target shape:

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

Field notes:

- `domains[].domainId` is the canonical domain key for filtering and routing
- `tags` should carry capability markers such as `ecom` and `d2c`
- `settings.confidenceThreshold` is the tenant-level similarity threshold

### `governance_logs`

Purpose:

- immutable audit trail of automated decisions and closure actions

Target shape:

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

Field notes:

- expected `decision` values include at least:
  - `answered`
  - `escalated`
  - `closed`
- `metadata` can hold extra context without changing the core schema
- this collection is append-only

## Collection and Index Notes

Best-known historical setup from the old n8n Mongo architecture:

- `knowledge_base`: clustered collection
- `governance_logs`: time-series collection
- `session_state`: standard collection with TTL/index-based lifecycle support
- `tenants`: standard collection

Best-known index expectations:

- `session_state` should support efficient lookup by identity tuple
- `session_state` should support efficient readiness checks for Workflow B
- `knowledge_base` should support tenant/domain filtering
- `knowledge_base` historically used Atlas Vector Search with tenant/domain pre-filtering
- `tenants` should support fast tenant lookup

## Historical Mismatch Notes

Older notes described:

- `sessionId` instead of relying on Mongo `_id`
- `expiresAt` instead of `debounceExpiresAt`

The rebuild should use:

- Mongo `_id`
- `debounceExpiresAt`

unless a later schema review explicitly changes that decision.

Older screenshots also showed examples such as:

- tenant test IDs like `t_001`
- client IDs like `c_002`

These are treated as historical/test artifacts rather than canonical rebuild fields.

## Rebuild Decisions Locked During S1

- MongoDB remains the first implementation target.
- `tenantId` is the real company identifier.
- `clientId` is the channel/source type.
- stale sessions should be log-then-delete.
- `ecom` / `d2c` branching should come from tenant `tags`.
- the rebuild should preserve the old three-workflow structure:
  - A: ingestor
  - B: processor
  - C: janitor

## Still Subject to Later Verification

- whether embeddings are stored directly in `knowledge_base` or generated/stored separately
- the exact production indexes currently active in Atlas
- the exact final payload shape used for governance log metadata in the live cluster

These items are not blockers for the code-first SVMP rebuild.
