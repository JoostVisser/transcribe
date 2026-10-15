from transcribe.formats import to_annotated_text, to_cues, to_srt
from transcribe.types import Segment, Word


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


def _words(*items: tuple[float, float, str]) -> list[Word]:
    return [Word(start, end, text) for start, end, text in items]


def test_a_long_segment_is_split_at_pauses_and_sentences() -> None:
    # as MAI-Transcribe 2 gave it: one segment over 27 s with long pauses
    segment = Segment(
        0.0,
        27.0,
        "Let us go conquer. Oh no. Enter. We're entering the mouth.",
        "speaker_1",
        _words(
            (0.24, 0.42, "Let"),
            (0.48, 0.62, "us"),
            (0.8, 0.92, "go"),
            (1.48, 2.12, "conquer."),
            (3.04, 3.2, "Oh"),
            (3.28, 3.56, "no."),
            (7.88, 8.48, "Enter."),
            (14.52, 14.7, "We're"),
            (14.76, 15.12, "entering"),
            (15.16, 15.28, "the"),
            (15.3, 15.9, "mouth."),
        ),
    )

    cues = to_cues(segment)

    assert [(c.start, c.end, c.text) for c in cues] == [
        (0.24, 2.12, "Let us go conquer."),
        (3.04, 3.56, "Oh no."),
        (7.88, 8.48, "Enter."),
        (14.52, 15.9, "We're entering the mouth."),
    ]
    assert {c.speaker_id for c in cues} == {"speaker_1"}


def test_a_short_sentence_end_stays_with_what_follows() -> None:
    segment = Segment(
        0.0, 2.0, "Hi. Hello.", None, _words((0.0, 0.3, "Hi."), (0.4, 1.0, "Hello."))
    )
    assert [c.text for c in to_cues(segment)] == ["Hi. Hello."]


def test_cues_stay_short_enough_to_read() -> None:
    words = [(i * 0.5, i * 0.5 + 0.4, f"word{i}") for i in range(30)]
    cues = to_cues(Segment(0.0, 15.0, "", None, _words(*words)))

    assert len(cues) > 1
    assert all(c.end - c.start <= 6.0 and len(c.text) <= 80 for c in cues)
    assert " ".join(c.text for c in cues) == " ".join(w for _, _, w in words)


def test_without_words_a_segment_is_one_cue() -> None:
    segment = Segment(0.0, 27.0, "All of it.")
    assert to_cues(segment) == [segment]
