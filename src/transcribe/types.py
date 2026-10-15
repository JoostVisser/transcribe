from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Protocol


@dataclass
class Word:
    start: float
    end: float
    text: str  # with its punctuation


@dataclass
class Segment:
    start: float
    end: float
    text: str
    speaker_id: str | None = None
    # When the provider gives word timestamps; subtitles split long segments
    # at them.
    words: list[Word] = field(default_factory=list)

    def shifted(self, offset: float) -> "Segment":
        """This segment `offset` seconds later."""
        return Segment(
            self.start + offset,
            self.end + offset,
            self.text,
            self.speaker_id,
            [Word(w.start + offset, w.end + offset, w.text) for w in self.words],
        )


class TranscriptionKind(StrEnum):
    """Enumeration of transcription types.

    STANDARD: Full transcription without timestamps or speaker labels.
    SEGMENTED: Transcription with timestamps for each segment.
    ANNOTATED: Transcription with timestamps and speaker labels.
    """

    STANDARD = "standard"
    SEGMENTED = "segmented"
    ANNOTATED = "annotated"


class ProviderName(StrEnum):
    """The transcription APIs this tool can use."""

    OPENROUTER = "openrouter"
    MISTRAL = "mistral"


class TranscriptionError(Exception):
    """Raised when transcription fails."""


class Provider(Protocol):
    """A transcription API, called once per audio chunk."""

    name: ProviderName
    model: str
    # Longest audio sent in one request.
    chunk_seconds: int
    # Most glossary terms one request takes.
    max_bias_terms: int
    # Total cost in USD of the requests so far, if the API reports it.
    cost: float | None

    def standard(self, audio: Path, bias_terms: list[str] | None) -> str:
        """Return the full transcription text without timestamps."""
        ...

    def segments(
        self, audio: Path, diarize: bool, bias_terms: list[str] | None
    ) -> list[Segment]:
        """Return segments with timestamps and, if `diarize`, speaker labels."""
        ...
