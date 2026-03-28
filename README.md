# SVMP

SVMP is a governance and orchestration layer for AI-powered customer service systems. The project is being rebuilt from an n8n prototype into a code-first service that is easier to test, observe, and ship.

Customer conversations often arrive as fragmented message streams rather than complete requests. SVMP is designed to merge those fragments into a coherent request, route the request safely, and keep a governance trail of what happened.

## Current Direction

The repo is being rebuilt in a Mongo-first shape so the core product can become demoable quickly using the existing MongoDB cluster and document schemas from the n8n prototype.

The near-term goal is to:

- get `svmp-core` running first
- keep the core testable from the start
- use repository interfaces so business logic is not tightly coupled to MongoDB
- leave room for a later PostgreSQL adapter if it becomes worthwhile

## Planned Architecture

`svmp-core/`

- reusable application core
- FastAPI app and webhook intake
- workflows for ingest, processing, and cleanup
- models, config, logging, exceptions, and DB interfaces
- MongoDB implementation first

`svmp-platform/`

- reserved for the later SaaS/platform wrapper
- tenant-aware auth, admin, security, and deployment concerns
- should stay thin and reuse `svmp-core` rather than fork the logic

`scripts/`

- one-off setup and demo scripts
- knowledge base seeding and local/dev utilities

## Core Runtime Flow

1. A webhook receives a customer message.
2. Workflow A writes or updates session state and starts the debounce window.
3. Workflow B picks up ready sessions, classifies intent/domain, queries the KB, generates or routes a response, and records governance data.
4. Workflow C removes stale session state.

## Status

The repo is still in scaffolding mode. The next step is to replace the old mixed Mongo/Postgres plan with a file-by-file Mongo-first build plan and then implement the core incrementally with tests in the same commit as each major change.
