# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.2.0] - 2026-10-15

### Changed

- `.srt` subtitles are split into readable cues at pauses, sentence ends and
  at about 6 seconds or 80 characters when the model gives word timestamps:
  MAI-Transcribe 2 gave segments up to 27 seconds long, pauses included.
- `--bias` on Microsoft's models goes straight to Azure's phrase list, and
  speaker labels use OpenRouter's `diarize`, as tried against the API:
  Azure refuses `keyterms`. No more first request that fails.

## [2.1.0] - 2026-10-14

### Added

- OpenRouter as a provider, with `microsoft/mai-transcribe-2` as the default
  model: used when `OPENROUTER_API_KEY` is set. Speaker labels
  (`--kind annotated`) and `--bias` go to OpenRouter as `diarize` and
  `keyterms`, or Azure's own options for Microsoft's models.
- `--provider openrouter|mistral` and `--model` options.
- API keys can live in `~/.config/transcribe/.env`, for runs from another
  directory.
- The cost of a run is printed when the provider reports it (OpenRouter).
- Network errors, rate limits and overloaded providers are retried on
  OpenRouter.
- Tests (`uv run pytest`).

### Changed

- Audio is always sent in pieces of the provider's length (5 minutes on
  OpenRouter, 10 on Mistral) instead of only above 20 MB.
- Audio without speech writes an empty transcription instead of failing.
- API errors from Mistral are reported as an error message instead of a
  traceback.

## [2.0.1] - 2026-09-17

### Added

- `--bias` option: load a glossary file (one term per line, blank lines and
  `#` comments ignored) and pass the terms to the API as `context_bias` for
  better spelling of proper nouns.

## [2.0.0] - 2026-04-15

### Added

- When saving files with `.srt` suffix, now saves them as SRT format.

### Changed

- Changed the default annotation to segmented.
- `ffmpeg` is now bundled as a dependency.
- Audio conversion changed to `.mp3` instead of `wav` for faster transcriptions.
- Clean up documentation.

### Fixed

- Large video files (2+ hours) are now supported.

## [1.1.0] - 2026-03-26

### Changed

- Change support from Python 3.14+ to 3.11+.

### Fixed

- Upgrade codebase to support MistralAI 2.0+ dependency.

## [1.0.0] - 2026-02-16

### Added

- Initial release of `transcribe` CLI tool
- Audio and video file transcription using Mistral's Voxtral API
- Three transcription modes:
  - `standard`: Full transcription without timestamps or speaker labels
  - `segmented`: Transcription with timestamps for each segment
  - `annotated`: Transcription with timestamps and speaker labels (diarization)
- Automatic audio conversion to WAV format using ffmpeg
- Error handling for missing files, conversion failures, and API errors
- CLI entry point `transcribe run` with options for input file, output file, and
  transcription kind

[2.2.0]: https://github.com/JoostVisser/transcribe/compare/2.1.0...2.2.0
[2.1.0]: https://github.com/JoostVisser/transcribe/compare/2.0.0...2.1.0
[2.0.1]: https://github.com/JoostVisser/transcribe/compare/2.0.0...2.0.1
[2.0.0]: https://github.com/JoostVisser/transcribe/compare/1.1.0...2.0.0
[1.1.0]: https://github.com/JoostVisser/transcribe/compare/1.0.0...1.1.0
[1.0.0]: https://github.com/JoostVisser/transcribe/releases/tag/1.0.0
