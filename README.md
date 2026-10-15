# transcribe

A CLI tool for transcribing audio and video files to text or subtitles, using
any speech-to-text model on [OpenRouter](https://openrouter.ai/collections/speech-to-text-models)
(by default Microsoft's MAI-Transcribe 2) or Mistral's Voxtral API.

## Installation

### Prerequisites

An API key for one of the providers:

- **OpenRouter** (recommended): `OPENROUTER_API_KEY`, from
  https://openrouter.ai/settings/keys. The default model,
  `microsoft/mai-transcribe-2`, costs about $0.10 per hour of audio and
  supports 60 languages, speaker labels and keyword biasing.
- **Mistral**: `MISTRAL_API_KEY`, from
  https://admin.mistral.ai/organization/api-keys. Voxtral Mini costs about
  $0.18 per hour of audio.

Put the key in one of these places (earlier ones win):

1. an environment variable: `export OPENROUTER_API_KEY="..."`
2. a `.env` file in the current directory
3. `~/.config/transcribe/.env` (or `$XDG_CONFIG_HOME/transcribe/.env`), for
   services and scripts that run from another directory

```
OPENROUTER_API_KEY=...
```

With both keys set, OpenRouter is used unless you pass `--provider mistral`.

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
pipx install git+https://github.com/joostvisser/transcribe.git@2.2.0
```

### Commands

#### `transcribe INPUT_FILE OUTPUT_FILE [--kind KIND] [--bias FILE] [--provider NAME] [--model MODEL]`

Transcribe a video or audio file to text.

**Arguments:**
- `INPUT_FILE`: Path to the input video or audio file.
- `OUTPUT_FILE`: Path where the transcription will be saved.
  If `OUTPUT_FILE` ends with `.srt`, the transcription will be saved as an SRT file.

**Options:**
- `--kind`: Type of transcription (default: `segmented`)
  - `standard`: Full transcription without timestamps or speaker labels
  - `segmented`: Transcription with timestamps for each segment
  - `annotated`: Transcription with timestamps and speaker labels (diarization)
- `--bias`: Optional glossary file with one term per line (blank lines and
  `#` comments are ignored). The terms bias the spelling of proper nouns:
  Azure's phrase list for Microsoft's models, `keyterms` for other
  OpenRouter models (at most 1000), or Mistral's `context_bias` (at most
  100). Terms are hints, not forced output.
- `--provider`: `openrouter` or `mistral` (default: OpenRouter when
  `OPENROUTER_API_KEY` is set, else Mistral).
- `--model`: The model on that provider (default:
  `microsoft/mai-transcribe-2` on OpenRouter, `voxtral-mini-latest` on
  Mistral). On OpenRouter, any model that returns segment timestamps
  (`verbose_json`) works for `segmented` and `annotated`; some, such as
  `openai/gpt-4o-transcribe`, only do `standard`.

Audio is sent in pieces: 5 minutes on OpenRouter (its providers time out
after 60 seconds per request), 10 minutes on Mistral. Speaker labels are per
piece, so in long recordings `speaker_1` in one piece may be another person
in the next. Audio without speech gives an empty transcription, not an
error. Where the model gives word timestamps (MAI-Transcribe 2 does), `.srt`
cues are split at pauses, sentence ends and at about 6 seconds or 80
characters, so subtitles stay readable; `.txt` keeps whole segments. OpenRouter reports what each request cost; the total is printed at
the end.

### Examples

```bash
# Segmented transcription with timestamps
transcribe recording.wav segments.txt

# Generating subtitles for a video.
transcribe video.mp4 subtitles.srt

# Annotated transcription with speaker labels
transcribe interview.mp4 interview.txt --kind annotated

# Improve proper-noun spelling with a glossary file
transcribe interview.mp4 interview.txt --bias glossary.txt

# Another model on OpenRouter, or Mistral
transcribe video.mp4 subtitles.srt --model openai/whisper-large-v3-turbo
transcribe video.mp4 subtitles.srt --provider mistral

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

Then, create a `.env` file with your key (see above), and run:

```bash
# Run the tests (no API calls; the audio tests use the bundled ffmpeg)
uv run pytest

# Lint and format
uv run ruff check . && uv run ruff format .

# Run the CLI
uv run transcribe input.mp3 output.txt
```
