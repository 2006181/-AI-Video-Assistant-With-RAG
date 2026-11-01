

import os
import shutil
import subprocess
from pathlib import Path

import yt_dlp
from pydub import AudioSegment


# --------------------------------------------------
# DIRECTORIES
# --------------------------------------------------

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

BGUTIL_DIR = Path("/tmp/bgutil-ytdlp-pot-provider")
BGUTIL_SERVER_DIR = BGUTIL_DIR / "server"
BGUTIL_SCRIPT = BGUTIL_SERVER_DIR / "src" / "generate_once.ts"

_BGUTIL_READY = False


# --------------------------------------------------
# BGUTIL PO TOKEN PROVIDER SETUP
# --------------------------------------------------

def setup_bgutil_provider():
    global _BGUTIL_READY

    if _BGUTIL_READY:
        return

    # Clone provider if it is not available
    if not BGUTIL_SERVER_DIR.exists():

        print("Cloning BgUtils PO Token Provider...")

        # Remove incomplete previous clone, if any
        if BGUTIL_DIR.exists():
            shutil.rmtree(BGUTIL_DIR)

        subprocess.run(
            [
                "git",
                "clone",
                "--single-branch",
                "--branch",
                "2.0.2",
                "https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git",
                str(BGUTIL_DIR),
            ],
            check=True,
        )

    if not BGUTIL_SCRIPT.is_file():
        raise FileNotFoundError(
            f"BgUtils script not found: {BGUTIL_SCRIPT}"
        )

    print(f"BgUtils script found: {BGUTIL_SCRIPT}")

    # Install Deno dependencies
    print("Installing BgUtils Deno dependencies...")

    subprocess.run(
        [
            "deno",
            "install",
            "--allow-scripts=npm:canvas",
            "--frozen",
        ],
        cwd=str(BGUTIL_SERVER_DIR),
        check=True,
    )

    _BGUTIL_READY = True

    print("BgUtils PO Token Provider ready!")


# --------------------------------------------------
# YOUTUBE AUDIO DOWNLOAD
# --------------------------------------------------

def download_youtube_audio(url: str) -> str:

    setup_bgutil_provider()

    output_path = str(DOWNLOAD_DIR / "%(id)s.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",

        "outtmpl": output_path,

        "noplaylist": True,

        # JavaScript runtime
        "js_runtimes": {
            "deno": {}
        },

        # BgUtils PO Token Provider
        "extractor_args": {
            "youtube": {
                "player_client": ["mweb", "tv", "web_safari"]
            },

            "youtubepot-bgutilscript": {
                "script_path": str(BGUTIL_SCRIPT)
            },
        },

        # Convert downloaded audio to WAV
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],

        "quiet": False,
        "verbose": True,

        "retries": 3,
        "fragment_retries": 3,
        "extractor_retries": 3,
    }

    print("Downloading YouTube audio...")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:

        info = ydl.extract_info(url, download=True)

        # Get final WAV filename
        downloaded_file = Path(ydl.prepare_filename(info))
        wav_path = downloaded_file.with_suffix(".wav")

    if not wav_path.is_file():
        raise FileNotFoundError(
            f"Downloaded WAV file not found: {wav_path}"
        )

    print(f"Download completed: {wav_path}")

    return str(wav_path)


# --------------------------------------------------
# AUDIO CONVERSION
# --------------------------------------------------

def convert_to_wav(input_path: str) -> str:
    """
    Convert audio/video to mono WAV at 16 kHz.
    """

    input_file = Path(input_path)

    if not input_file.is_file():
        raise FileNotFoundError(
            f"Input file not found: {input_path}"
        )

    output_path = input_file.with_name(
        input_file.stem + "_converted.wav"
    )

    audio = AudioSegment.from_file(str(input_file))

    # Normalize audio for transcription
    audio = audio.set_channels(1)
    audio = audio.set_frame_rate(16000)

    audio.export(
        str(output_path),
        format="wav",
    )

    print(f"Audio converted: {output_path}")

    return str(output_path)


# --------------------------------------------------
# AUDIO CHUNKING
# --------------------------------------------------

def chunk_audio(
    wav_path: str,
    chunk_minutes: int = 10
) -> list:

    if chunk_minutes <= 0:
        raise ValueError("chunk_minutes must be greater than 0")

    if not os.path.isfile(wav_path):
        raise FileNotFoundError(
            f"WAV file not found: {wav_path}"
        )

    audio = AudioSegment.from_wav(wav_path)

    chunk_ms = chunk_minutes * 60 * 1000

    chunks = []

    for i, start in enumerate(
        range(0, len(audio), chunk_ms)
    ):

        chunk = audio[start:start + chunk_ms]

        chunk_path = (
            f"{os.path.splitext(wav_path)[0]}_chunk_{i}.wav"
        )

        chunk.export(
            chunk_path,
            format="wav",
        )

        chunks.append(chunk_path)

        print(f"Created chunk {i + 1}: {chunk_path}")

    return chunks


# --------------------------------------------------
# MAIN INPUT PROCESSOR
# --------------------------------------------------

def process_input(source: str) -> list:

    if not source:
        raise ValueError("Please provide a YouTube URL or file path.")

    source = str(source).strip()

    if source.startswith(("http://", "https://")):

        print("Detected YouTube URL.")

        downloaded_path = download_youtube_audio(source)

        # Normalize downloaded audio to mono 16 kHz
        wav_path = convert_to_wav(downloaded_path)

    else:

        print("Detected local audio/video file.")

        wav_path = convert_to_wav(source)

    print("Starting audio chunking...")

    chunks = chunk_audio(
        wav_path,
        chunk_minutes=10,
    )

    if not chunks:
        raise ValueError("No audio chunks were created.")

    print(
        f"Audio ready! Total chunks created: {len(chunks)}"
    )

    return chunks
