"""Audio conversion utilities."""

import subprocess
from pathlib import Path


class ConversionError(Exception):
    """Raised when audio conversion fails."""


def convert_to_wav(input_path: str | Path, output_path: str | Path) -> None:
    """Convert audio/video file to WAV format using ffmpeg.

    Args:
        input_path: Path to the input audio or video file.
        output_path: Path where the WAV file will be saved.

    Raises:
        ConversionError: If ffmpeg conversion fails.
        FileNotFoundError: If ffmpeg is not found or input file doesn't exist.
    """
    input = Path(input_path)
    output = Path(output_path)

    if not input.exists():
        raise FileNotFoundError(f"Input file not found: {input}")

    # ffmpeg command to extract audio and convert to WAV
    cmd = [
        "ffmpeg",
        "-i",
        str(input),
        "-vn",  # No video
        "-acodec",
        "pcm_s16le",  # 16-bit PCM
        "-ar",
        "16000",  # 16kHz sample rate (required by Mistral)
        "-ac",
        "1",  # Mono
        "-y",  # Overwrite output file
        str(output),
    ]

    try:
        _ = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        raise ConversionError(f"ffmpeg failed: {e.stderr}") from e
    except FileNotFoundError as e:
        raise FileNotFoundError(
            "ffmpeg not found. Please install ffmpeg and ensure it's in your PATH."
        ) from e
