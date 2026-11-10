import asyncio
import subprocess
import os
import sys
import re

import av
# Fix compatibility between PyAV and faster-whisper
_orig_av_open = av.open
def _patched_av_open(*args, **kwargs):
    kwargs.pop("metadata_errors", None)
    return _orig_av_open(*args, **kwargs)
av.open = _patched_av_open

from faster_whisper import WhisperModel
from deep_translator import GoogleTranslator, MyMemoryTranslator
import edge_tts

VIDEO_FILE = "sample_video.mp4"

def format_timestamp(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def translate_chunk(text):
    text = text.strip()
    if not text:
        return ""
    try:
        return GoogleTranslator(source="en", target="ur").translate(text)
    except Exception:
        try:
            return MyMemoryTranslator(source="en-GB", target="ur-PK", email="videotranslator@antigravity.local").translate(text)
        except Exception as e:
            print(f"Warning: translation failed for '{text[:30]}...': {e}", flush=True)
            return text

def translate_long_text(text):
    if not text or not text.strip():
        return ""
    sentences = re.split(r'(?<=[.?!])\s+', text.strip())
    translated_parts = []
    current_chunk = ""
    for s in sentences:
        if len(current_chunk) + len(s) < 350:
            current_chunk += (" " if current_chunk else "") + s
        else:
            if current_chunk:
                translated_parts.append(translate_chunk(current_chunk))
            current_chunk = s
    if current_chunk:
        translated_parts.append(translate_chunk(current_chunk))
    return " ".join(translated_parts)

async def process_video(video_path, mode="1"):
    if not os.path.exists(video_path):
        print(f"Error: Could not find '{video_path}' in the current folder.")
        return

    print("1. Loading Whisper AI model (downloads ~140MB on first run)...", flush=True)
    model = WhisperModel("base", device="cpu", compute_type="int8")

    print("2. Transcribing English audio from video...", flush=True)
    segments, info = model.transcribe(video_path, beam_size=5)
    print(f"   Detected language: {info.language} (probability: {info.language_probability:.2f})", flush=True)

    if mode == "1":
        output_srt = "sample_video.srt"
        print("3. Translating to Urdu subtitles...", flush=True)
        with open(output_srt, "w", encoding="utf-8") as srt_file:
            for i, segment in enumerate(segments, start=1):
                start_time = format_timestamp(segment.start)
                end_time = format_timestamp(segment.end)
                eng_text = segment.text.strip()
                urdu_text = translate_long_text(eng_text)
                
                print(f"[{start_time}] {urdu_text}", flush=True)
                srt_file.write(f"{i}\n{start_time} --> {end_time}\n{urdu_text}\n\n")
                srt_file.flush()
        print(f"\nDone! Open '{video_path}' in VLC Media Player and '{output_srt}' will load automatically.")

    elif mode == "2":
        print("3. Collecting transcription segments...", flush=True)
        eng_sentences = []
        for i, seg in enumerate(segments, start=1):
            t = seg.text.strip()
            if t:
                eng_sentences.append(t)
            if i % 25 == 0:
                print(f"   [Transcription progress] {i} segments decoded (at video time {format_timestamp(seg.end)})...", flush=True)

        full_english = " ".join(eng_sentences)
        print(f"   Transcription complete! Total words: {len(full_english.split())}", flush=True)

        print("4. Translating script to Urdu...", flush=True)
        sentences = re.split(r'(?<=[.?!])\s+', full_english)
        chunks = []
        curr = ""
        for s in sentences:
            if len(curr) + len(s) < 350:
                curr += (" " if curr else "") + s
            else:
                if curr:
                    chunks.append(curr)
                curr = s
        if curr:
            chunks.append(curr)

        urdu_chunks = []
        for idx, chunk in enumerate(chunks, 1):
            urdu_translated = translate_chunk(chunk)
            urdu_chunks.append(urdu_translated)
            if idx % 10 == 0 or idx == len(chunks):
                print(f"   [Translation progress] {idx}/{len(chunks)} chunks translated...", flush=True)

        urdu_script = " ".join(urdu_chunks)

        print("5. Generating Pakistani Urdu AI voiceover...", flush=True)
        output_audio = "urdu_audio.mp3"
        if os.path.exists(output_audio):
            os.remove(output_audio)

        tts_parts = []
        temp_part = ""
        for word in urdu_script.split():
            if len(temp_part) + len(word) < 2000:
                temp_part += (" " if temp_part else "") + word
            else:
                if temp_part:
                    tts_parts.append(temp_part)
                temp_part = word
        if temp_part:
            tts_parts.append(temp_part)

        with open(output_audio, "wb") as audio_file:
            for p_idx, part in enumerate(tts_parts, 1):
                tts = edge_tts.Communicate(part, "ur-PK-AsadNeural")
                async for chunk in tts.stream():
                    if chunk["type"] == "audio":
                        audio_file.write(chunk["data"])
                if p_idx % 5 == 0 or p_idx == len(tts_parts):
                    print(f"   [TTS progress] {p_idx}/{len(tts_parts)} audio blocks synthesized...", flush=True)

        print("6. Merging Urdu audio into video with FFmpeg...", flush=True)
        output_video = "urdu_dubbed.mp4"
        subprocess.run([
            "ffmpeg", "-y", "-i", video_path, "-i", output_audio,
            "-c:v", "copy", "-map", "0:v:0", "-map", "1:a:0", "-shortest", output_video
        ], check=True)
        print(f"\nDone! Saved dubbed video as '{output_video}'.", flush=True)

if __name__ == "__main__":
    print("Choose output mode:")
    print("1 = Generate Urdu Subtitles (.srt)")
    print("2 = Generate Urdu Voice Dubbed Video (.mp4)")
    if len(sys.argv) > 1:
        choice = sys.argv[1].strip()
        print(f"Enter 1 or 2: {choice}")
    else:
        choice = input("Enter 1 or 2: ").strip()
    asyncio.run(process_video(VIDEO_FILE, choice))
