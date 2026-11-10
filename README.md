# Video Voice Translator (English to Urdu)

An AI-powered video translation tool that takes an English video and provides:
1. **Urdu Subtitles (`.srt`)**: Automatically generated subtitles synchronized with the video.
2. **Urdu Dubbed Audio (`.mp4`)**: An AI-generated Urdu voiceover merged into the video using natural text-to-speech.

## Features
- **Speech Recognition**: Uses [faster-whisper](https://github.com/SYSTRAN/faster-whisper) for fast and accurate English speech-to-text.
- **Language Translation**: Translates transcribed text to Urdu with chunking and fallback support.
- **Urdu Voiceover (TTS)**: Synthesizes Pakistani Urdu speech using Microsoft Edge TTS (`ur-PK-AsadNeural`).
- **Audio/Video Remuxing**: Seamlessly replaces or integrates audio using FFmpeg without re-encoding video.

## Prerequisites
- Python 3.10+
- [FFmpeg](https://ffmpeg.org/) installed and available in your system `PATH`.

## Installation
```bash
pip install -r requirements.txt
```

## Usage
Place your video in the project directory as `sample_video.mp4` (or change the path in `video_translator.py`), then run:

```bash
python video_translator.py
```

Choose your desired mode:
- `1` : Generate Urdu Subtitles (`sample_video.srt`)
- `2` : Generate Urdu Dubbed Video (`urdu_dubbed.mp4`)

You can also pass the mode directly as a command-line argument:
```bash
python video_translator.py 1
# or
python video_translator.py 2
```
