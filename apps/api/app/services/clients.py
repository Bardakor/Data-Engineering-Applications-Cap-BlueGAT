"""External API clients."""

from openai import OpenAI

from app.core.config import settings


def get_openai_client() -> OpenAI | None:
    """Return OpenAI client if API key is configured, else None."""
    if not settings.openai_api_key:
        return None
    return OpenAI(api_key=settings.openai_api_key)
