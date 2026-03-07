# SVMP

SVMP is a governance and orchestration layer for AI-powered customer service systems.

---

Customer conversations often arrive as fragmented message streams rather than complete requests. Traditional LLM-based agents treat each message independently, which leads to hallucinations, unsafe actions, and unreliable automation.

SVMP introduces a state-aware architecture that merges fragmented user messages into coherent request units, isolates tenant context, and deterministically routes intents between informational responses and transactional actions.

The system was originally prototyped using n8n workflows and has been rebuilt as a code-based architecture for reliability, observability, and production deployment.

SVMP is designed to make AI-driven customer service agents safer, more predictable, and easier to operate in multi-tenant environments.

---

## Core Concepts

SVMP introduces several architectural components to stabilize AI customer service automation:

- **Identity Frame** — isolates tenant-specific state, configuration, and permissions.
- **Soft Debounce Queue** — merges fragmented user messages into a single coherent request unit.
- **Intent Logic Fork** — separates informational queries handled by LLMs from transactional actions executed through APIs.
- **Governance Layer** — enforces validation, routing rules, and observability across the system.
