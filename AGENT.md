# transcribe - Agent Context

CLI tool for transcribing audio/video files via Mistral's Voxtral API.

## TranscriptionKind

- `standard` — plain text, no timestamps
- `segmented` — timestamps per segment, no speaker labels
- `annotated` — timestamps + speaker labels (diarization)

## Output formats

Determined by output file extension:
- `.txt` — annotated text (`[16.0s → 17.2s] speaker_1: …`)
- `.srt` — SRT subtitles; `segmented` omits speaker labels, `annotated` includes them

## Commands

```bash
uv sync                          # install deps
uv run transcribe INPUT OUTPUT [--kind standard|segmented|annotated]
uv run pytest                    # run tests
```

## Notes

- ffmpeg must be installed on the system
- `MISTRAL_API_KEY` must be set (`.env` file supported)
- Package manager: `uv`
