"""OpenRouter client for transcription, through its speech-to-text API.

https://openrouter.ai/docs/api/api-reference/stt/create-transcription
"""

import base64
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx

from transcribe.types import ProviderName, Segment, TranscriptionError

URL = "https://openrouter.ai/api/v1/audio/transcriptions"
DEFAULT_MODEL = "microsoft/mai-transcribe-2"
# Upstream providers time out after 60 seconds per request, so the audio goes
# in shorter pieces than Mistral takes.
CHUNK_SECONDS = 300
MAX_BIAS_TERMS = 1000  # API limit for keyterms.
# Rate limits, gateway timeouts and overloaded providers pass with a retry.
RETRY_STATUSES = {408, 429, 500, 502, 503, 504, 524, 529}
ATTEMPTS = 4
TIMEOUT = httpx.Timeout(180.0, connect=15.0)

JSON = dict[str, Any]


class OpenRouterProvider:
    """Transcribes with any speech-to-text model on OpenRouter."""

    name = ProviderName.OPENROUTER
    chunk_seconds = CHUNK_SECONDS
    max_bias_terms = MAX_BIAS_TERMS

    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        client: httpx.Client | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.client = client or httpx.Client(timeout=TIMEOUT)
        self.sleep = sleep
        self.cost: float | None = None
        # Azure (MAI-Transcribe) may want its own names for speaker labels and
        # keyword biasing; once it does, every later chunk uses them.
        self.azure_options = False

    def standard(self, audio: Path, bias_terms: list[str] | None) -> str:
        """Return the full transcription text without timestamps or speaker labels."""
        data = self._transcribe(audio, {"response_format": "json"}, False, bias_terms)
        return str(data.get("text", ""))

    def segments(
        self, audio: Path, diarize: bool, bias_terms: list[str] | None
    ) -> list[Segment]:
        """Return transcription segments with timestamps and optional speaker
        labels."""
        options: JSON = {
            "response_format": "verbose_json",
            "timestamp_granularities": ["segment", "word"] if diarize else ["segment"],
        }
        data = self._transcribe(audio, options, diarize, bias_terms)
        return parse_segments(data, diarize)

    def _transcribe(
        self,
        audio: Path,
        options: JSON,
        diarize: bool,
        bias_terms: list[str] | None,
    ) -> JSON:
        audio_data = base64.b64encode(audio.read_bytes()).decode("ascii")
        extras = bool(diarize or bias_terms)
        try:
            data = self._post(
                request_body(
                    self.model,
                    audio_data,
                    audio.suffix.lstrip(".").lower(),
                    options,
                    diarize,
                    bias_terms,
                    self.azure_options,
                )
            )
        except _BadRequest as e:
            if self.azure_options or not extras or not _is_azure(self.model):
                raise TranscriptionError(str(e)) from None
            # The generic fields aren't supported by every provider; Azure
            # takes its own under provider.options.
            self.azure_options = True
            return self._transcribe(audio, options, diarize, bias_terms)
        cost = (data.get("usage") or {}).get("cost")
        if isinstance(cost, int | float):
            self.cost = (self.cost or 0.0) + cost
        return data

    def _post(self, body: JSON) -> JSON:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        for attempt in range(1, ATTEMPTS + 1):
            try:
                response = self.client.post(URL, json=body, headers=headers)
            except httpx.HTTPError as e:
                if attempt == ATTEMPTS:
                    raise TranscriptionError(f"OpenRouter: {e}") from None
            else:
                if response.is_success:
                    return response.json()
                message = _error_message(response)
                if response.status_code == 400:
                    raise _BadRequest(message)
                if response.status_code not in RETRY_STATUSES or attempt == ATTEMPTS:
                    raise TranscriptionError(message)
            self.sleep(2.0**attempt)
        raise AssertionError("unreachable")


class _BadRequest(Exception):
    """A 400 from OpenRouter: the request asks for something unsupported."""


def request_body(
    model: str,
    audio_data: str,
    audio_format: str,
    options: JSON,
    diarize: bool,
    bias_terms: list[str] | None,
    azure_options: bool,
) -> JSON:
    """The JSON body for one transcription request."""
    body: JSON = {
        "model": model,
        "input_audio": {"data": audio_data, "format": audio_format},
        **options,
    }
    if azure_options:
        azure: JSON = {}
        if diarize:
            azure["diarization"] = {"enabled": True}
        if bias_terms:
            azure["phraseList"] = {"phrases": bias_terms}
        body["provider"] = {"options": {"azure": azure}}
        return body
    if diarize:
        body["diarize"] = True
    if bias_terms:
        body["keyterms"] = bias_terms
    return body


def parse_segments(data: JSON, diarize: bool) -> list[Segment]:
    """Segments from a verbose_json response.

    Speaker labels come on the segments or only on the words, depending on
    the provider; a segment without one takes the speaker of most of its
    words.
    """
    words: list[JSON] = data.get("words") or []
    segments: list[Segment] = []
    for seg in data.get("segments") or []:
        speaker = None
        if diarize:
            speaker = _speaker(seg) or _speaker_of_words(seg, words)
        segments.append(
            Segment(
                start=float(seg["start"]),
                end=float(seg["end"]),
                text=str(seg["text"]),
                speaker_id=speaker,
            )
        )
    text = str(data.get("text") or "").strip()
    if not segments and text:
        # Some providers return only the text: one segment for the whole chunk.
        segments.append(Segment(0.0, float(data.get("duration") or 0.0), text))
    return segments


def _speaker(item: JSON) -> str | None:
    label = item.get("speaker_label")
    if isinstance(label, str) and label:
        return label
    number = item.get("speaker")
    # OpenRouter numbers speakers from 0; the labels count from 1, as Mistral's.
    return f"speaker_{number + 1}" if isinstance(number, int) else None


def _speaker_of_words(seg: JSON, words: list[JSON]) -> str | None:
    counts: dict[str, int] = {}
    for word in words:
        if seg["start"] <= word.get("start", -1) < seg["end"]:
            speaker = _speaker(word)
            if speaker:
                counts[speaker] = counts.get(speaker, 0) + 1
    return max(counts, key=lambda s: counts[s]) if counts else None


def _is_azure(model: str) -> bool:
    return model.startswith("microsoft/")


def _error_message(response: httpx.Response) -> str:
    try:
        error = response.json().get("error") or {}
        message = error.get("message") or response.text
    except ValueError:
        message = response.text
    return f"OpenRouter {response.status_code}: {message}"
