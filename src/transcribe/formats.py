"""Output format converters for transcription segments."""

from transcribe.types import Segment, Word

# A subtitle cue ends at a pause, at the end of a sentence once it has been
# on screen a moment, or before it gets too long to read.
CUE_PAUSE = 1.0  # seconds of silence between words
CUE_SENTENCE = 1.5  # seconds before a sentence end may close the cue
CUE_SECONDS = 6.0
CUE_CHARS = 80


def to_annotated_text(segments: list[Segment]) -> str:
    """Format segments as annotated text with timestamps and optional speaker labels."""
    lines: list[str] = []
    for segment in segments:
        speaker = f" {segment.speaker_id}" if segment.speaker_id else ""
        line = (
            f"[{segment.start:.1f}s → {segment.end:.1f}s]"
            f"{speaker}: {segment.text.strip()}"
        )
        lines.append(line)
    return "\n".join(lines)


def to_srt(segments: list[Segment]) -> str:
    """Format segments as an SRT subtitle file, split into readable cues
    where the segments have word timestamps."""
    blocks: list[str] = []
    cues = [cue for segment in segments for cue in to_cues(segment)]
    for i, cue in enumerate(cues, start=1):
        start = _seconds_to_srt_timestamp(cue.start)
        end = _seconds_to_srt_timestamp(cue.end)
        speaker_prefix = f"{cue.speaker_id}: " if cue.speaker_id else ""
        text = f"{speaker_prefix}{cue.text.strip()}"
        blocks.append(f"{i}\n{start} --> {end}\n{text}")
    return "\n\n".join(blocks) + "\n"


def to_cues(segment: Segment) -> list[Segment]:
    """The segment as subtitle cues: whole when it has no word timestamps,
    else split at pauses, sentence ends and length limits."""
    if not segment.words:
        return [segment]
    groups: list[list[Word]] = [[]]
    for word in segment.words:
        cue = groups[-1]
        if cue and _ends_cue(cue, word):
            cue = []
            groups.append(cue)
        cue.append(word)
    return [
        Segment(
            cue[0].start,
            cue[-1].end,
            " ".join(w.text.strip() for w in cue),
            segment.speaker_id,
            cue,
        )
        for cue in groups
    ]


def _ends_cue(cue: list[Word], next_word: Word) -> bool:
    last = cue[-1]
    if next_word.start - last.end >= CUE_PAUSE:
        return True
    if (
        last.text.rstrip().endswith((".", "?", "!"))
        and last.end - cue[0].start >= CUE_SENTENCE
    ):
        return True
    text = " ".join(w.text.strip() for w in [*cue, next_word])
    return next_word.end - cue[0].start > CUE_SECONDS or len(text) > CUE_CHARS


def _seconds_to_srt_timestamp(seconds: float) -> str:
    """Convert seconds to SRT timestamp format HH:MM:SS,mmm."""
    total_ms = round(seconds * 1000)
    ms = total_ms % 1000
    total_s = total_ms // 1000
    s = total_s % 60
    total_m = total_s // 60
    m = total_m % 60
    h = total_m // 60
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
