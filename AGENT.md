# transcribe - Agent Context

CLI tool for transcribing audio/video files via OpenRouter's speech-to-text
API (default model `microsoft/mai-transcribe-2`) or Mistral's Voxtral API.

## Layout

- `cli.py` — Typer command, glossary loading
- `providers.py` — picks the provider from `--provider` or the keys set
- `openrouter.py` / `mistral.py` — one class per API with the `Provider`
  interface from `types.py`: `standard()` and `segments()` per audio chunk,
  `chunk_seconds`, `max_bias_terms`, `cost`
- `transcribe.py` — convert to MP3, split into the provider's chunks, shift
  each chunk's timestamps by its start, write `.txt` or `.srt`
- `audio.py` — ffmpeg (bundled via `static-ffmpeg`)
- `formats.py` — annotated text, SRT, subtitle cues from word timestamps
- `settings.py` — API keys from the environment, `.env`, or
  `~/.config/transcribe/.env`

## TranscriptionKind

- `standard` — plain text, no timestamps
- `segmented` — timestamps per segment, no speaker labels
- `annotated` — timestamps + speaker labels (diarization)

## Output formats

Determined by output file extension:
- `.txt` — annotated text (`[16.0s → 17.2s] speaker_1: …`)
- `.srt` — SRT subtitles; `segmented` omits speaker labels, `annotated` includes them

## OpenRouter notes

- `POST https://openrouter.ai/api/v1/audio/transcriptions`, JSON with base64
  `input_audio`; `verbose_json` for segments. Upstream timeout 60 s per
  request, hence 5-minute chunks.
- Speaker labels use the generic `diarize` field (works on Azure). Biasing
  uses `keyterms`, except on Azure models (`microsoft/*`), which answer 400
  "does not support keyterms": they get `provider.options.azure.phraseList.phrases`
  (checked against the real API).
- `segments` always asks for word timestamps; `formats.to_cues` splits long
  segments into subtitle cues at pauses (≥ 1 s), sentence ends (after
  1.5 s) and limits (6 s, 80 chars). MAI-Transcribe 2 gives segments up to
  ~30 s long, pauses included.
- Speakers come as `speaker` (0-based) or `speaker_label`, on segments or
  only on words; labels are `speaker_1`, `speaker_2`, … as with Mistral.
- 408/429/5xx/524/529 and network errors are retried with backoff.

## Commands

```bash
uv sync                          # install deps
uv run pytest                    # tests; no API calls
uv run ruff check . && uv run ruff format .
uv run transcribe INPUT OUTPUT [--kind standard|segmented|annotated] [--bias FILE] [--provider openrouter|mistral] [--model MODEL]
```

## Notes

- `OPENROUTER_API_KEY` or `MISTRAL_API_KEY` must be set (environment, `.env`,
  or `~/.config/transcribe/.env`)
- Package manager: `uv`
- Tests use `httpx.MockTransport` for OpenRouter and a fake provider for the
  pipeline; never call a real API from tests.
