from pathlib import Path

import pytest
import typer

from transcribe import transcribe
from transcribe.types import ProviderName, Segment, TranscriptionKind


class FakeProvider:
    name = ProviderName.OPENROUTER
    model = "fake/model"
    chunk_seconds = 300
    max_bias_terms = 10

    def __init__(self, segments: list[list[Segment]]) -> None:
        self.chunks = segments
        self.cost: float | None = 0.002
        self.calls: list[tuple[str, bool, list[str] | None]] = []

    def standard(self, audio: Path, bias_terms: list[str] | None) -> str:
        self.calls.append((audio.name, False, bias_terms))
        return " ".join(s.text for s in self.chunks.pop(0))

    def segments(
        self, audio: Path, diarize: bool, bias_terms: list[str] | None
    ) -> list[Segment]:
        self.calls.append((audio.name, diarize, bias_terms))
        return self.chunks.pop(0)


@pytest.fixture
def chunks(monkeypatch: pytest.MonkeyPatch) -> list[int]:
    """Skips ffmpeg: the conversion writes a file, the split makes as many
    chunks as the list says (one by default)."""
    count = [1]

    def convert(input_path: Path, output_path: Path) -> None:
        Path(output_path).write_bytes(b"mp3")

    def split(input_path: Path, output_dir: Path, chunk_seconds: int) -> list[Path]:
        paths = [output_dir / f"chunk_{i:03d}.mp3" for i in range(count[0])]
        for path in paths:
            path.write_bytes(b"mp3")
        return paths

    monkeypatch.setattr(transcribe, "convert_to_mp3", convert)
    monkeypatch.setattr(transcribe, "split_mp3", split)
    return count


@pytest.fixture
def video(tmp_path: Path) -> Path:
    path = tmp_path / "DJI_0001.MP4"
    path.write_bytes(b"video")
    return path


def test_chunks_are_shifted_by_their_start(
    chunks: list[int], video: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    chunks[0] = 2
    provider = FakeProvider(
        [
            [Segment(1.0, 2.5, "Here we go.", "speaker_1")],
            [Segment(0.5, 1.0, "Still going.", "speaker_1")],
        ]
    )
    out = tmp_path / "DJI_0001.srt"

    transcribe.transcribe_file(
        video, out, TranscriptionKind.ANNOTATED, provider, ["Lagos"]
    )

    assert out.read_text() == (
        "1\n00:00:01,000 --> 00:00:02,500\nspeaker_1: Here we go.\n\n"
        "2\n00:05:00,500 --> 00:05:01,000\nspeaker_1: Still going.\n"
    )
    assert provider.calls == [
        ("chunk_000.mp3", True, ["Lagos"]),
        ("chunk_001.mp3", True, ["Lagos"]),
    ]
    output = capsys.readouterr().out
    assert "fake/model (openrouter)" in output
    assert "Cost: $0.0020" in output


def test_no_speech_is_an_empty_transcription(
    chunks: list[int], video: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "DJI_0001.srt"

    transcribe.transcribe_file(
        video, out, TranscriptionKind.SEGMENTED, FakeProvider([[]])
    )

    assert out.read_text() == ""
    assert "No speech found." in capsys.readouterr().out


def test_standard_joins_the_chunks(
    chunks: list[int], video: Path, tmp_path: Path
) -> None:
    chunks[0] = 2
    provider = FakeProvider([[Segment(0, 1, "One.")], [Segment(0, 1, "Two.")]])
    out = tmp_path / "out.txt"

    transcribe.transcribe_file(video, out, TranscriptionKind.STANDARD, provider)

    assert out.read_text() == "One. Two."


def test_srt_needs_timestamps(chunks: list[int], video: Path, tmp_path: Path) -> None:
    with pytest.raises(typer.Exit):
        transcribe.transcribe_file(
            video, tmp_path / "out.srt", TranscriptionKind.STANDARD, FakeProvider([])
        )
