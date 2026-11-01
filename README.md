# 🎬 AI Video Assistant with RAG

Turn any meeting recording, lecture or video into a transcript, a summary, action items, decisions and open questions, and then **chat with it**.

Give it audio (or, when running locally, a YouTube link or video file). It transcribes the speech (English, Hindi and Hinglish), writes structured notes, and builds a searchable knowledge base so you can ask questions like *"Who is responsible for the deployment?"* and get answers grounded in what was actually said.

---

## 🧭 Two ways to run it

| | **Local (on your computer)** | **Hosted (Streamlit Cloud)** |
|---|---|---|
| YouTube link | ✅ | ❌ blocked by YouTube on cloud servers |
| Video file (mp4, mkv, mov, webm, avi) | ✅ | ❌ |
| Audio file (mp3, wav, m4a, aac, ogg, flac, wma) | ✅ | ✅ |

The app detects where it is running and shows only the options that work there. To force a mode, set the environment variable `APP_MODE=local` or `APP_MODE=hosted`.

---

## ✨ Features

- 🔗 **Flexible input:** YouTube URL, video file or audio file (locally), audio file (hosted)
- 🎙️ **English transcription:** local Whisper AI, free and runs on your machine
- 🇮🇳 **Hindi and Hinglish transcription:** powered by Sarvam AI
- 📋 **Bullet-point summary** of the full recording
- ✅ **Action items** with owner and deadline
- 🔑 **Key decisions** made in the meeting
- ❓ **Open questions and follow-ups**
- 💬 **Chat with your recording** using RAG + ChromaDB
- 📄 **Export the full report** as Markdown, and the transcript as TXT
- 🎨 **Dark Streamlit UI** with live progress, metrics, transcript search and suggested chat questions

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Language | Python |
| Speech-to-text (English) | OpenAI Whisper (local, free) |
| Speech-to-text (Hindi/Hinglish) | Sarvam AI |
| LLM pipeline | LangChain LCEL |
| LLM | Groq (default model `openai/gpt-oss-120b`, configurable) |
| Vector database | ChromaDB |
| Embeddings | HuggingFace (local, free) |
| Audio/video handling | yt-dlp, pydub, FFmpeg |
| UI | Streamlit |

---

## 🧭 How it works

```
YouTube URL / video / audio file
        │
        ▼
  Audio extraction + chunking
        │
        ▼
  Transcription ── English  → Whisper (local)
                └─ Hi/Hinglish → Sarvam AI
        │
        ▼
  LLM (LangChain LCEL)
   ├─ Title + summary
   ├─ Action items (owner, deadline)
   ├─ Key decisions
   └─ Open questions
        │
        ▼
  Transcript → embeddings → ChromaDB
        │
        ▼
  Chat with the recording (RAG)
```

---

## 📁 Project Structure

```
.
├── app.py                  # Streamlit UI (local + hosted modes)
├── core/
│   ├── transcriber.py      # Speech-to-text (Whisper / Sarvam)
│   ├── summarizer.py       # Title and summary
│   ├── extractor.py        # Action items, decisions, questions
│   ├── vector_store.py     # ChromaDB + embeddings
│   └── rag_engine.py       # RAG chain and chat
├── utils/
│   └── audio_processor.py  # Download, convert and chunk audio
├── requirements.txt
├── packages.txt            # System packages for Streamlit Cloud (ffmpeg)
└── .env                    # API keys (not committed)
```

---

## 🚀 Run locally (YouTube + video + audio)

### 1. Prerequisites

- Python 3.10 to 3.12 recommended
- [FFmpeg](https://ffmpeg.org/download.html) installed and added to your PATH
- API keys for Groq and Sarvam AI

### 2. Clone the repository

```bash
git clone https://github.com/2006181/-AI-Video-Assistant-With-RAG.git
cd -AI-Video-Assistant-With-RAG
```

### 3. Create a virtual environment

**Windows (PowerShell)**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS / Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Add your API keys

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_key_here
GROQ_MODEL=openai/gpt-oss-120b
SARVAM_API_KEY=your_sarvam_key_here
```

> Never commit your `.env` file. Add it to `.gitignore`.
> Groq's model list changes often. If you see a "model not found" error, check the available models in the Groq console and update `GROQ_MODEL`.

### 6. Start the app

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501` and shows the YouTube, video and audio options.

---

## ☁️ Deploy on Streamlit Cloud (audio only)

1. Push the repository to GitHub.
2. Make sure `packages.txt` exists in the repo root with this single line:
   ```
   ffmpeg
   ```
3. On [share.streamlit.io](https://share.streamlit.io), create a new app and choose `app.py` as the main file.
4. In **Advanced settings**, pick Python 3.11 or 3.12 and add your keys under **Secrets**:
   ```toml
   GROQ_API_KEY = "your_groq_key_here"
   GROQ_MODEL = "openai/gpt-oss-120b"
   SARVAM_API_KEY = "your_sarvam_key_here"
   ```
5. Deploy. The hosted app automatically switches to **audio-only** mode.

---

## 💡 Usage

1. Choose **YouTube link** or **Upload file** in the sidebar (hosted: upload an audio file).
2. Select the spoken language: `english` or `hinglish`.
3. Click **Analyze** and wait for the progress steps to finish.
4. Browse the **Overview**, **Actions and decisions** and **Transcript** tabs.
5. Open the **Chat** tab and ask questions about the recording.
6. Download the report or transcript.

---

## 🧩 Example questions to ask

- *What were the main topics discussed?*
- *Who is responsible for what?*
- *What deadlines were mentioned?*
- *What was decided about the budget?*

---

## ⚠️ Notes and troubleshooting

- **YouTube on the hosted app:** YouTube blocks downloads from cloud servers (you will see `HTTP Error 403`). Use the local version for YouTube links, or upload the audio file.
- **Local Whisper is slow on CPU** for long recordings. A smaller model is faster, and a GPU makes a big difference.
- **Rate limits:** free API tiers have limits. If you see a `429` error, wait a minute and try again. The app retries automatically a few times.
- **`No module named 'audioop'`:** on Python 3.13 and newer, add `audioop-lts` to `requirements.txt` (`audioop-lts>=0.2.1; python_version >= "3.13"`).
- **FFmpeg not found:** install FFmpeg locally, or add `ffmpeg` to `packages.txt` on Streamlit Cloud.

---

## 🗺️ Roadmap

- [ ] Speaker identification
- [ ] Timestamped transcript and jump-to-moment answers
- [ ] PDF export
- [ ] Cloud transcription option for faster hosted runs

---

## 👤 Author

**Rahul**
GitHub: [@2006181](https://github.com/2006181)

---

## 📜 License

Add a license of your choice (for example MIT) to this repository.