import subprocess
from pathlib import Path

from transcribe.audio import _ffmpeg, convert_to_mp3, split_mp3


def _tone(path: Path, seconds: int) -> None:
    subprocess.run(
        [
            _ffmpeg(),
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency=440:duration={seconds}",
            "-y",
            str(path),
        ],
        check=True,
        capture_output=True,
    )


def test_split_into_the_providers_chunk_length(tmp_path: Path) -> None:
    source = tmp_path / "clip.wav"
    _tone(source, 7)
    mp3 = tmp_path / "clip.mp3"
    convert_to_mp3(source, mp3)
    out = tmp_path / "chunks"
    out.mkdir()

    chunks = split_mp3(mp3, out, chunk_seconds=3)

    assert [c.name for c in chunks] == [
        "chunk_000.mp3",
        "chunk_001.mp3",
        "chunk_002.mp3",
    ]


def test_a_short_file_is_one_chunk(tmp_path: Path) -> None:
    source = tmp_path / "clip.wav"
    _tone(source, 2)
    mp3 = tmp_path / "clip.mp3"
    convert_to_mp3(source, mp3)

    assert len(split_mp3(mp3, tmp_path, chunk_seconds=300)) == 1
