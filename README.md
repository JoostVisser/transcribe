# transcribe

A CLI tool for transcribing audio and video files using Mistral's Voxtral API.

## Installation

### Prerequisites

1. **ffmpeg**: Install ffmpeg and ensure it's in your PATH.
   - Linux: `sudo apt install ffmpeg` (Debian/Ubuntu)
     or `sudo dnf install ffmpeg` (Fedora)
   - macOS: `brew install ffmpeg`
   - Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html)

2. **Mistral API Key**: Set your `MISTRAL_API_KEY` environment variable.
   ```bash
   export MISTRAL_API_KEY="your-api-key-here"
   ```
   - You can get one here: https://admin.mistral.ai/organization/api-keys
   - Transcription is cheap: put €5 in the account and you can transcribe
     28 hours of content.

### Install with pipx

```bash
pipx install git+https://github.com/joostvisser/transcribe.git
```

## Usage

### Commands

#### `transcribe run INPUT_FILE OUTPUT_TEXT [--kind KIND]`

Transcribe a video or audio file to text.

**Arguments:**
- `INPUT_FILE`: Path to the input video or audio file
- `OUTPUT_TEXT`: Path where the transcription will be saved

**Options:**
- `--kind`: Type of transcription (default: `standard`)
  - `standard`: Full transcription without timestamps or speaker labels
  - `segmented`: Transcription with timestamps for each segment
  - `annotated`: Transcription with timestamps and speaker labels (diarization)

### Examples

```bash
# Standard transcription
transcribe run meeting.mp3 meeting.txt

# Segmented transcription with timestamps
transcribe run recording.wav segments.txt --kind segmented

# Annotated transcription with speaker labels
transcribe run interview.mp4 interview.txt --kind annotated

# Get help
transcribe run --help
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
