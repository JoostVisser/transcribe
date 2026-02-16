# transcribe - AI Agent Context

This document provides context for AI assistants working on the `transcribe` project.

## Project Overview

`transcribe` is a Python CLI tool for transcribing audio and video files using Mistral's Voxtral API. It converts input files to WAV format using ffmpeg, then sends them to Mistral's transcription service.

## Architecture

```
src/transcribe/
├── __init__.py
├── cli.py              # Typer CLI entry point
├── transcribe.py       # Main orchestration logic
├── audio.py            # ffmpeg conversion utilities
├── mistral.py          # Mistral API client
├── settings.py         # Pydantic settings for configuration
└── types.py            # Type definitions (TranscriptionKind enum)
```

## Key Components

### TranscriptionKind Enum
- `STANDARD`: Full transcription without timestamps or speaker labels
- `SEGMENTED`: Transcription with timestamps for each segment
- `ANNOTATED`: Transcription with timestamps and speaker labels (diarization)

### Audio Conversion
- Uses ffmpeg to convert any audio/video format to WAV
- Required format: 16-bit PCM, 16kHz sample rate, mono
- Handled by `convert_to_wav()` in `audio.py`

### Mistral API Integration
- Model: `voxtral-mini-latest`
- API endpoint: `https://api.mistral.ai/v1/audio/transcriptions`
- Authentication via `MISTRAL_API_KEY` environment variable

### CLI Entry Point
```bash
transcribe run INPUT_FILE OUTPUT_TEXT [--kind KIND]
```

## Dependencies

- `typer`: CLI framework
- `mistralai`: Mistral API client
- `pydantic-settings`: Settings management
- `httpx`: HTTP client (transitive dependency)
- `ffmpeg`: System dependency for audio conversion

## Development Setup

```bash
# Install with uv
uv sync

# Run tests
uv run pytest

# Run the CLI
uv run transcribe run input.mp3 output.txt
```

## Important Notes

1. The project uses `uv` as the package manager and build tool
2. ffmpeg must be installed on the system
3. Transcription quality depends on Mistral's service availability
4. Large files may take time to convert and transcribe
5. The project follows Semantic Versioning - current version is 1.0.0

## Common Tasks

- **Add a new transcription mode**: Extend `TranscriptionKind` enum and update `mistral.py`
- **Change audio conversion parameters**: Modify ffmpeg arguments in `audio.py`
- **Update API settings**: Edit `settings.py`
- **Add CLI options**: Modify `cli.py` and update `transcribe_file()` signature
