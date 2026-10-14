from transcribe.formats import to_annotated_text, to_srt
from transcribe.types import Segment


def test_srt_timestamps_and_speakers() -> None:
    segments = [
        Segment(0.0, 1.25, " Hello. ", "speaker_1"),
        Segment(3661.5, 3662.0, "Later."),
    ]
    assert to_srt(segments) == (
        "1\n00:00:00,000 --> 00:00:01,250\nspeaker_1: Hello.\n\n"
        "2\n01:01:01,500 --> 01:01:02,000\nLater.\n"
    )


def test_annotated_text() -> None:
    assert to_annotated_text([Segment(16.0, 17.2, "Hi", "speaker_2")]) == (
        "[16.0s → 17.2s] speaker_2: Hi"
    )
