from dataclasses import dataclass
from enum import StrEnum


@dataclass
class Segment:
    start: float
    end: float
    text: str
    speaker_id: str | None = None


class TranscriptionKind(StrEnum):
    """Enumeration of transcription types.

    STANDARD: Full transcription without timestamps or speaker labels.
    SEGMENTED: Transcription with timestamps for each segment.
    ANNOTATED: Transcription with timestamps and speaker labels.
    """

    STANDARD = "standard"
    SEGMENTED = "segmented"
    ANNOTATED = "annotated"
