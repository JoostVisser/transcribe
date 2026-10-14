from pathlib import Path

import pytest

from transcribe.mistral import MistralProvider
from transcribe.openrouter import OpenRouterProvider
from transcribe.providers import make_provider
from transcribe.types import ProviderName, TranscriptionError


@pytest.fixture(autouse=True)
def no_keys(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """No keys from the environment or the user's files; returns the
    config home."""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.chdir(tmp_path)
    return tmp_path / "config"


def test_openrouter_when_its_key_is_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-key")
    monkeypatch.setenv("MISTRAL_API_KEY", "m-key")

    provider = make_provider(None, None)

    assert isinstance(provider, OpenRouterProvider)
    assert provider.model == "microsoft/mai-transcribe-2"
    assert provider.api_key == "or-key"


def test_mistral_with_only_its_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MISTRAL_API_KEY", "m-key")

    provider = make_provider(None, "voxtral-small-latest")

    assert isinstance(provider, MistralProvider)
    assert provider.model == "voxtral-small-latest"


def test_the_key_from_the_user_config(no_keys: Path) -> None:
    (no_keys / "transcribe").mkdir(parents=True)
    (no_keys / "transcribe" / ".env").write_text("OPENROUTER_API_KEY=from-config\n")

    provider = make_provider(None, None)

    assert isinstance(provider, OpenRouterProvider)
    assert provider.api_key == "from-config"


def test_the_local_env_file_wins(no_keys: Path, tmp_path: Path) -> None:
    (no_keys / "transcribe").mkdir(parents=True)
    (no_keys / "transcribe" / ".env").write_text("OPENROUTER_API_KEY=from-config\n")
    (tmp_path / ".env").write_text("OPENROUTER_API_KEY=from-here\n")

    provider = make_provider(ProviderName.OPENROUTER, "openai/whisper-large-v3")

    assert isinstance(provider, OpenRouterProvider)
    assert provider.api_key == "from-here"
    assert provider.model == "openai/whisper-large-v3"


def test_no_key_says_where_to_put_one() -> None:
    with pytest.raises(TranscriptionError, match="OPENROUTER_API_KEY"):
        make_provider(None, None)


def test_the_provider_asked_for_needs_its_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-key")
    with pytest.raises(TranscriptionError, match="MISTRAL_API_KEY"):
        make_provider(ProviderName.MISTRAL, None)
