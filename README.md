# transcribe

A CLI tool for transcribing audio and video files using Mistral's Voxtral API.

## Installation

### Prerequisites

1. **Mistral API Key**: Set your `MISTRAL_API_KEY` environment variable.
   ```bash
   export MISTRAL_API_KEY="your-api-key-here"
   ```
   - You can get one here: https://admin.mistral.ai/organization/api-keys
   - Transcription is cheap: put €5 in the account and you can transcribe 30+ hours of
     content.

### Install with pipx

Use `pipx` if you want to have an isolated installation.

Install `pipx`:

```bash
pip install pipx
```

Then, install the latest version of transcribe:

```bash
pipx install git+https://github.com/joostvisser/transcribe.git
```

Or install a specific version:

```bash
pipx install git+https://github.com/joostvisser/transcribe.git@2.0.0
```

### Commands

#### `transcribe INPUT_FILE OUTPUT_FILE [--kind KIND]`

Transcribe a video or audio file to text.

**Arguments:**
- `INPUT_FILE`: Path to the input video or audio file.
- `OUTPUT_FILE`: Path where the transcription will be saved
  If `OUTPUT_FILE` ends with `.srt`, the transcription will be saved as an SRT File.

**Options:**
- `--kind`: Type of transcription (default: `segmented`)
  - `standard`: Full transcription without timestamps or speaker labels
  - `segmented`: Transcription with timestamps for each segment
  - `annotated`: Transcription with timestamps and speaker labels (diarization)

### Examples

```bash
# Segmented transcription with timestamps
transcribe recording.wav segments.txt

# Generating subtitles for a video.
transcribe video.mp4 subtitles.srt

# Annotated transcription with speaker labels
transcribe interview.mp4 interview.txt --kind annotated

# Get help
transcribe --help
```

## Development

Development requires `uv` for Python and `pre-commit` for pre-commit hooks.

Download [uv](https://docs.astral.sh/uv/getting-started/installation/) and
[pre-commit](https://pre-commit.com/#install) to get started.

```bash
# Install dependencies
uv sync

# Install pre-commit hook
pre-commit install
```

Then, you need to create a `.env` file with your key:
```
MISTRAL_API_KEY=...
```

Finally, you can run the CI:
```
# Run the CLI
uv run transcribe input.mp3 output.txt
```
