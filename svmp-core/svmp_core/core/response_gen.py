"""Customer-facing response generation built on top of the OpenAI wrapper."""

from __future__ import annotations

from svmp_core.config import Settings, get_settings
from svmp_core.exceptions import IntegrationError
from svmp_core.integrations import generate_completion
from svmp_core.models import KnowledgeEntry

_NO_MATCH_RESPONSE = (
    "I couldn't find a reliable answer yet, so I'm handing this over to a human for help."
)


async def generate_customer_response(
    query: str,
    *,
    knowledge_entry: KnowledgeEntry | None,
    settings: Settings | None = None,
) -> str:
    """Generate a customer-facing answer from a matched KB entry when available."""

    normalized_query = query.strip()
    if not normalized_query:
        raise IntegrationError("query must not be blank")

    if knowledge_entry is None:
        return _NO_MATCH_RESPONSE

    runtime_settings = settings or get_settings()

    system_prompt = (
        "You are a helpful customer support assistant. "
        "Answer only using the trusted FAQ answer provided. "
        "Be concise, clear, and customer-friendly. "
        "Do not invent policies or details that are not in the FAQ answer."
    )
    user_prompt = (
        f"Customer question: {normalized_query}\n\n"
        f"Matched FAQ question: {knowledge_entry.question}\n"
        f"Matched FAQ answer: {knowledge_entry.answer}\n\n"
        "Write the final reply to the customer."
    )

    try:
        return await generate_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            settings=runtime_settings,
        )
    except IntegrationError as exc:
        raise IntegrationError("response generation failed") from exc
