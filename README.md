# 🎬 AI Video Assistant with RAG

Turn any meeting recording or YouTube video into a transcript, a summary, action items, decisions and open questions, and then **chat with it**.

Give it a YouTube link or an audio/video file. It transcribes the speech (English, Hindi and Hinglish), writes structured meeting notes, and builds a searchable knowledge base so you can ask questions like *"Who is responsible for the deployment?"* and get answers grounded in what was actually said.

---

## ✨ Features

- 🔗 **Flexible input:** paste a YouTube URL or upload an audio/video file
- 🎙️ **English transcription:** local Whisper AI, free and runs on your machine
- 🇮🇳 **Hindi and Hinglish transcription:** powered by Sarvam AI
- 📋 **Bullet-point summary** of the full meeting
- ✅ **Action items** with owner and deadline
- 🔑 **Key decisions** made in the meeting
- ❓ **Open questions and follow-ups**
- 💬 **Chat with your meeting** using RAG + ChromaDB
- 📄 **Export the full report** as PDF or TXT

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Language | Python |
| Speech-to-text (English) | OpenAI Whisper (local, free) |
| Speech-to-text (Hindi/Hinglish) | Sarvam AI |
| LLM pipeline | LangChain LCEL |
| LLM | GROQ (free API) |
| Vector database | ChromaDB |
| Embeddings | HuggingFace (local, free) |
| UI | Streamlit |

---

## 🧭 How it works

```
YouTube URL / file
        │
        ▼
  Audio download + chunking
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
  Chat with the meeting (RAG)
```

---

## 📁 Project Structure

```
.
├── app.py                  # Streamlit UI
├── core/
│   ├── transcriber.py      # Speech-to-text (Whisper / Sarvam)
│   ├── summarizer.py       # Title and summary
│   ├── extractor.py        # Action items, decisions, questions
│   └── rag_engine.py       # ChromaDB + RAG chat
├── utils/
│   └── audio_processor.py  # Download, convert and chunk audio
├── requirements.txt
└── .env                    # API keys (not committed)
```

---

## 🚀 Getting Started

### 1. Prerequisites

- Python 3.10 or newer
- [FFmpeg](https://ffmpeg.org/download.html) installed and added to your PATH
- API keys for GROQ and Sarvam AI

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
MISTRAL_API_KEY=your_mistral_key_here
SARVAM_API_KEY=your_sarvam_key_here
```

> Never commit your `.env` file. Add it to `.gitignore`.

### 6. Run the app

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`.

---

## 💡 Usage

1. Choose **YouTube link** or **Upload file** in the sidebar.
2. Select the spoken language: `english` or `hinglish`.
3. Click **Analyze** and wait for the progress steps to finish.
4. Browse the **Overview**, **Actions and decisions** and **Transcript** tabs.
5. Open the **Chat** tab and ask questions about the meeting.
6. Download the report as PDF or TXT.

---

## 🧩 Example questions to ask

- *What were the main topics discussed?*
- *Who is responsible for what?*
- *What deadlines were mentioned?*
- *What was decided about the budget?*

---

## ⚠️ Notes

- Local Whisper is slow on CPU for long videos. A smaller model (`base` or `small`) is faster, and a GPU makes a big difference.
- Free API tiers have rate limits. If you see a `429` error, wait a minute and try again.
- Downloading from YouTube can fail on some networks or hosted servers. Uploading a file is the more reliable option.

---

## 🗺️ Roadmap

- [ ] Speaker identification
- [ ] Timestamped transcript and jump-to-moment answers
- [ ] More export formats
- [ ] Hosted demo

---

## 👤 Author

**Rahul**
GitHub: [@2006181](https://github.com/2006181)

---

## 📜 License

Add a license of your choice (for example MIT) to this repository.
