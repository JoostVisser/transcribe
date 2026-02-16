from enum import StrEnum


class TranscriptionKind(StrEnum):
    """Enumeration of transcription types.

    STANDARD: Full transcription without timestamps or speaker labels.
    SEGMENTED: Transcription with timestamps for each segment.
    ANNOTATED: Transcription with timestamps and speaker labels.
    """

    STANDARD = "standard"
    SEGMENTED = "segmented"
    ANNOTATED = "annotated"
