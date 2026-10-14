"""Choosing the transcription API."""

from transcribe.mistral import MistralProvider
from transcribe.openrouter import OpenRouterProvider
from transcribe.settings import Settings, user_env_file
from transcribe.types import Provider, ProviderName, TranscriptionError


def make_provider(name: ProviderName | None, model: str | None) -> Provider:
    """The provider asked for, or else OpenRouter when its key is set and
    Mistral otherwise, with the model given or the provider's default."""
    settings = Settings(_env_file=(user_env_file(), ".env"))  # pyright: ignore[reportCallIssue]
    if name is None:
        if settings.openrouter_api_key:
            name = ProviderName.OPENROUTER
        elif settings.mistral_api_key:
            name = ProviderName.MISTRAL
        else:
            raise TranscriptionError(
                "No API key: set OPENROUTER_API_KEY (or MISTRAL_API_KEY) in the "
                f"environment, in .env, or in {user_env_file()}."
            )
    if name is ProviderName.OPENROUTER:
        if not settings.openrouter_api_key:
            raise TranscriptionError("--provider openrouter needs OPENROUTER_API_KEY.")
        if model:
            return OpenRouterProvider(settings.openrouter_api_key, model)
        return OpenRouterProvider(settings.openrouter_api_key)
    if not settings.mistral_api_key:
        raise TranscriptionError("--provider mistral needs MISTRAL_API_KEY.")
    if model:
        return MistralProvider(settings.mistral_api_key, model)
    return MistralProvider(settings.mistral_api_key)
