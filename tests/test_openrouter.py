import json
from pathlib import Path
from typing import Any

import httpx
import pytest

from transcribe.openrouter import OpenRouterProvider, parse_segments
from transcribe.types import Segment, TranscriptionError

Handler = Any


def _provider(
    handler: Handler, model: str = "microsoft/mai-transcribe-2"
) -> tuple[OpenRouterProvider, list[float]]:
    slept: list[float] = []
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return OpenRouterProvider("key", model, client, slept.append), slept


@pytest.fixture
def audio(tmp_path: Path) -> Path:
    path = tmp_path / "chunk_000.mp3"
    path.write_bytes(b"ID3 fake mp3")
    return path


VERBOSE = {
    "text": "Hello there. Hi!",
    "segments": [
        {"id": 0, "start": 0.0, "end": 1.2, "text": "Hello there.", "speaker": 0},
        {"id": 1, "start": 1.4, "end": 2.0, "text": "Hi!", "speaker": 1},
    ],
    "usage": {"seconds": 2.0, "cost": 0.0001},
}


def test_segments_send_the_audio_and_the_options(audio: Path) -> None:
    bodies: list[dict[str, Any]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == "https://openrouter.ai/api/v1/audio/transcriptions"
        assert request.headers["Authorization"] == "Bearer key"
        bodies.append(json.loads(request.content))
        return httpx.Response(200, json=VERBOSE)

    provider, _ = _provider(handler)
    segments = provider.segments(audio, diarize=False, bias_terms=["Briançon"])

    assert segments == [
        Segment(0.0, 1.2, "Hello there."),
        Segment(1.4, 2.0, "Hi!"),
    ]
    body = bodies[0]
    assert body["model"] == "microsoft/mai-transcribe-2"
    assert body["input_audio"] == {"data": "SUQzIGZha2UgbXAz", "format": "mp3"}
    assert body["response_format"] == "verbose_json"
    assert body["timestamp_granularities"] == ["segment"]
    assert body["keyterms"] == ["Briançon"]
    assert "diarize" not in body and "provider" not in body
    assert provider.cost == pytest.approx(0.0001)


def test_annotated_labels_speakers_from_one(audio: Path) -> None:
    bodies: list[dict[str, Any]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        bodies.append(json.loads(request.content))
        return httpx.Response(200, json=VERBOSE)

    provider, _ = _provider(handler)
    segments = provider.segments(audio, diarize=True, bias_terms=None)

    assert [s.speaker_id for s in segments] == ["speaker_1", "speaker_2"]
    assert bodies[0]["diarize"] is True
    assert bodies[0]["timestamp_granularities"] == ["segment", "word"]
    assert "keyterms" not in bodies[0]


def test_azure_options_when_the_generic_ones_are_refused(audio: Path) -> None:
    bodies: list[dict[str, Any]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        bodies.append(body)
        if "diarize" in body or "keyterms" in body:
            return httpx.Response(400, json={"error": {"message": "unsupported"}})
        return httpx.Response(200, json=VERBOSE)

    provider, _ = _provider(handler)
    provider.segments(audio, diarize=True, bias_terms=["Cádiz"])
    provider.segments(audio, diarize=True, bias_terms=["Cádiz"])

    # refused once, then the Azure names for this chunk and every later one
    assert len(bodies) == 3
    assert bodies[1]["provider"] == {
        "options": {
            "azure": {
                "diarization": {"enabled": True},
                "phraseList": {"phrases": ["Cádiz"]},
            }
        }
    }
    assert bodies[2]["provider"] == bodies[1]["provider"]
    assert provider.cost == pytest.approx(0.0002)


def test_a_bad_request_without_extras_is_an_error(audio: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"error": {"code": 400, "message": "no"}})

    provider, _ = _provider(handler)
    with pytest.raises(TranscriptionError, match="OpenRouter 400: no"):
        provider.standard(audio, bias_terms=None)


def test_other_models_get_no_azure_retry(audio: Path) -> None:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(400, json={"error": {"message": "no diarize"}})

    provider, _ = _provider(handler, model="openai/whisper-large-v3")
    with pytest.raises(TranscriptionError, match="no diarize"):
        provider.segments(audio, diarize=True, bias_terms=None)
    assert len(calls) == 1


def test_overloaded_and_unreachable_are_retried(audio: Path) -> None:
    answers: list[httpx.Response | Exception] = [
        httpx.Response(529, json={"error": {"message": "overloaded"}}),
        httpx.ConnectError("down"),
        httpx.Response(200, json={"text": "Hello", "usage": {"cost": 0.00005}}),
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        answer = answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer

    provider, slept = _provider(handler)
    assert provider.standard(audio, bias_terms=None) == "Hello"
    assert slept == [2.0, 4.0]


def test_retries_end(audio: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"error": {"message": "busy"}})

    provider, slept = _provider(handler)
    with pytest.raises(TranscriptionError, match="OpenRouter 503: busy"):
        provider.standard(audio, bias_terms=None)
    assert len(slept) == 3


def test_a_wrong_key_is_not_retried(audio: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": {"message": "No auth"}})

    provider, slept = _provider(handler)
    with pytest.raises(TranscriptionError, match="401"):
        provider.standard(audio, bias_terms=None)
    assert slept == []


def test_speakers_only_on_words_go_to_their_segment() -> None:
    data = {
        "segments": [
            {"id": 0, "start": 0.0, "end": 2.0, "text": "Hello there."},
            {"id": 1, "start": 2.0, "end": 3.0, "text": "Hi."},
        ],
        "words": [
            {"word": "Hello", "start": 0.0, "end": 0.5, "speaker": 1},
            {"word": "there", "start": 0.6, "end": 1.0, "speaker": 1},
            {"word": "Hi", "start": 2.1, "end": 2.4, "speaker_label": "Guide"},
        ],
    }
    assert [s.speaker_id for s in parse_segments(data, diarize=True)] == [
        "speaker_2",
        "Guide",
    ]
    assert [s.speaker_id for s in parse_segments(data, diarize=False)] == [
        None,
        None,
    ]


def test_text_without_segments_is_one_segment() -> None:
    data = {"text": " Hello. ", "duration": 4.5}
    assert parse_segments(data, diarize=False) == [Segment(0.0, 4.5, "Hello.")]
    assert parse_segments({"text": ""}, diarize=False) == []
