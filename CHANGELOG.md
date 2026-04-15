# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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


[1.1.0]: https://github.com/JoostVisser/transcribe/compare/1.0.0...1.1.0
[1.0.0]: https://github.com/JoostVisser/transcribe/releases/tag/1.0.0
