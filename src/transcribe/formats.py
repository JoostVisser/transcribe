"""Output format converters for transcription segments."""

from transcribe.types import Segment


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
    """Format segments as an SRT subtitle file."""
    blocks: list[str] = []
    for i, segment in enumerate(segments, start=1):
        start = _seconds_to_srt_timestamp(segment.start)
        end = _seconds_to_srt_timestamp(segment.end)
        speaker_prefix = f"{segment.speaker_id}: " if segment.speaker_id else ""
        text = f"{speaker_prefix}{segment.text.strip()}"
        blocks.append(f"{i}\n{start} --> {end}\n{text}")
    return "\n\n".join(blocks) + "\n"


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
