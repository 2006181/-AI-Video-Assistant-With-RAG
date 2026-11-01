"""
AI Video Assistant - Streamlit UI
Run with:  streamlit run app.py

Modes
-----
Local  : YouTube link, video file or audio file
Hosted : audio file only (YouTube downloads are blocked on cloud servers,
         and video files are large)

The mode is detected automatically (Streamlit Cloud = hosted).
Force a mode with the environment variable APP_MODE=local or APP_MODE=hosted.
"""
import os
import re
import tempfile
import time

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.summarizer import summarize, generate_title
from core.extractor import (
    extract_action_items,
    extract_key_decisions,
    extract_questions,
)
from core.rag_engine import build_rag_chain, ask_question

# ------------------------------------------------------------------ mode
AUDIO_TYPES = ["mp3", "wav", "m4a", "aac", "ogg", "flac", "wma"]
VIDEO_TYPES = ["mp4", "mkv", "mov", "webm", "avi"]


def detect_hosted() -> bool:
    """True when running on a hosted server (e.g. Streamlit Cloud)."""
    mode = os.getenv("APP_MODE", "").strip().lower()
    if mode in ("hosted", "local"):
        return mode == "hosted"
    return os.path.exists("/mount/src") or os.getenv("HOME", "") == "/home/adminuser"


IS_HOSTED = detect_hosted()

# ------------------------------------------------------------------ page setup
st.set_page_config(
    page_title="AI Video Assistant",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------------------------------------ styling
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@500;700;800&family=Inter:wght@400;500;600&display=swap');

:root {
  --bg: #0E1320;
  --surface: #161D30;
  --surface-2: #1D2640;
  --line: #2A3555;
  --text: #E8ECF6;
  --muted: #94A0BF;
  --accent: #7C93FF;
  --amber: #FFB86B;
  --mint: #5EE0B5;
  --rose: #FF7A93;
}

html, body, [class*="css"], .stApp { font-family: 'Inter', sans-serif; color: var(--text); }
.stApp { background: radial-gradient(1200px 500px at 85% -10%, #1C2750 0%, var(--bg) 60%); }

/* hide menu/footer but keep the header so the sidebar toggle always works */
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"],
[data-testid="stExpandSidebarButton"] { visibility: visible !important; color: var(--text) !important; }
[data-testid="stSidebarCollapsedControl"] button,
[data-testid="collapsedControl"] button,
[data-testid="stExpandSidebarButton"] { background: var(--surface-2) !important; border-radius: 10px; }

.block-container { padding-top: 3.5rem; max-width: 1200px; }

h1, h2, h3, .hero-title { font-family: 'Sora', sans-serif !important; letter-spacing: -0.02em; }

/* sidebar */
section[data-testid="stSidebar"] { background: var(--surface); border-right: 1px solid var(--line); }
section[data-testid="stSidebar"] * { color: var(--text); }
.brand { font-family: 'Sora', sans-serif; font-weight: 800; font-size: 1.3rem; margin-bottom: .2rem; }
.brand span { color: var(--accent); }
.tagline { color: var(--muted); font-size: .85rem; margin-bottom: 1rem; }
.mode-pill { display: inline-block; padding: 3px 12px; border-radius: 999px; font-size: .78rem;
             border: 1px solid var(--line); background: var(--surface-2); margin-bottom: 1rem; }
.mode-note { color: var(--muted); font-size: .82rem; margin: .2rem 0 1rem 0; line-height: 1.5; }

/* hero */
.hero { padding: 2.2rem 2.4rem; border: 1px solid var(--line); border-radius: 20px;
        background: linear-gradient(135deg, var(--surface) 0%, var(--surface-2) 100%); margin-bottom: 1.4rem; }
.hero-title { font-size: 2.6rem; font-weight: 800; line-height: 1.1; margin: 0 0 .6rem 0; }
.hero-sub { color: var(--muted); font-size: 1.05rem; max-width: 640px; }

/* feature cards on landing */
.feature-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 14px; margin-top: 1rem; }
.feature { background: var(--surface); border: 1px solid var(--line); border-radius: 14px; padding: 1.1rem 1.2rem; }
.feature b { font-family: 'Sora', sans-serif; display:block; margin-bottom:.3rem; }
.feature span { color: var(--muted); font-size: .9rem; }

/* result header */
.result-title { font-family: 'Sora', sans-serif; font-size: 2rem; font-weight: 800; margin: 0 0 .3rem 0; }
.result-meta { color: var(--muted); font-size: .9rem; margin-bottom: 1.2rem; }

/* metrics */
.metric-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 1.4rem; }
.metric { background: var(--surface); border: 1px solid var(--line); border-radius: 14px; padding: 1rem 1.2rem; }
.metric .num { font-family: 'Sora', sans-serif; font-size: 1.8rem; font-weight: 700; }
.metric .lbl { color: var(--muted); font-size: .85rem; }
.metric.m1 .num { color: var(--accent); } .metric.m2 .num { color: var(--amber); }
.metric.m3 .num { color: var(--mint); }   .metric.m4 .num { color: var(--rose); }
@media (max-width: 800px) { .metric-grid { grid-template-columns: repeat(2, 1fr); } .hero-title{font-size:2rem;} }

/* content cards */
.card { background: var(--surface); border: 1px solid var(--line); border-radius: 16px; padding: 1.3rem 1.5rem; }
.card h4 { font-family: 'Sora', sans-serif; margin: 0; font-size: 1.05rem; }
.card.accent { border-left: 4px solid var(--accent); }
.card.amber  { border-left: 4px solid var(--amber); }
.card.mint   { border-left: 4px solid var(--mint); }
.card.rose   { border-left: 4px solid var(--rose); }

/* tabs */
.stTabs [data-baseweb="tab-list"] { gap: 6px; border-bottom: 1px solid var(--line); }
.stTabs [data-baseweb="tab"] { background: transparent; border-radius: 10px 10px 0 0; padding: 10px 18px; color: var(--muted); }
.stTabs [aria-selected="true"] { color: var(--text) !important; background: var(--surface); }

/* buttons */
.stButton > button, .stDownloadButton > button {
  background: var(--accent); color: #0E1320; font-weight: 600; border: 0; border-radius: 10px; padding: .55rem 1.1rem;
}
section[data-testid="stSidebar"] .stButton > button { width: 100%; }
.stButton > button:hover, .stDownloadButton > button:hover { background: #9AAEFF; color: #0E1320; }
.stButton > button:focus-visible { outline: 2px solid var(--amber); outline-offset: 2px; }

/* inputs */
.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
  background: var(--surface-2) !important; border: 1px solid var(--line) !important; color: var(--text) !important; border-radius: 10px !important;
}

/* chat */
[data-testid="stChatMessage"] { background: var(--surface); border: 1px solid var(--line); border-radius: 14px; padding: .8rem 1rem; }

/* transcript box */
.transcript { background: var(--surface); border: 1px solid var(--line); border-radius: 14px; padding: 1.2rem 1.4rem;
              max-height: 480px; overflow-y: auto; line-height: 1.75; color: #CBD3E8; font-size: .95rem; }
mark { background: var(--amber); color: #0E1320; border-radius: 3px; padding: 0 3px; }

@media (prefers-reduced-motion: reduce) { * { animation: none !important; transition: none !important; } }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ------------------------------------------------------------------ helpers
SUGGESTED = [
    "What were the main topics discussed?",
    "Who is responsible for what?",
    "What deadlines were mentioned?",
]


def count_items(text: str) -> int:
    """Roughly count bullet / numbered lines in an LLM-generated list."""
    if not text:
        return 0
    lines = [l.strip() for l in str(text).splitlines()]
    n = sum(1 for l in lines if re.match(r"^([-*•]|\d+[.)])\s+", l))
    return n or (1 if str(text).strip() else 0)


def build_report_md(r: dict) -> str:
    return (
        f"# {r['title']}\n\n"
        f"## Summary\n{r['summary']}\n\n"
        f"## Action items\n{r['action_items']}\n\n"
        f"## Key decisions\n{r['key_decisions']}\n\n"
        f"## Open questions\n{r['open_questions']}\n\n"
        f"## Transcript\n{r['transcript']}\n"
    )


def card(title: str, body: str, tone: str = "accent"):
    st.markdown(f'<div class="card {tone}"><h4>{title}</h4></div>', unsafe_allow_html=True)
    st.markdown(body if str(body).strip() else "_Nothing found._")


def with_retry(fn, *args, tries: int = 5, base_delay: float = 2.0):
    """Retry on rate limits (429) with exponential backoff."""
    for attempt in range(tries):
        try:
            return fn(*args)
        except Exception as e:
            if "429" in str(e) and attempt < tries - 1:
                time.sleep(base_delay * (2 ** attempt))
            else:
                raise


def friendly_error(e: Exception) -> str:
    msg = str(e)
    if "403" in msg or "Forbidden" in msg or "Sign in to confirm" in msg:
        return (
            "YouTube blocked this download. Run the app locally to use YouTube links, "
            "or upload the audio file instead."
        )
    if "429" in msg or "Rate limit" in msg or "rate_limit" in msg:
        return "The API rate limit was reached. Wait 1-2 minutes and press Analyze again."
    if "model_not_found" in msg or "does not exist" in msg:
        return "The LLM model name is not available. Set a valid GROQ_MODEL in your .env or secrets."
    if "ffmpeg" in msg.lower() or "ffprobe" in msg.lower():
        return "FFmpeg was not found. Install FFmpeg (locally) or add it to packages.txt (hosted)."
    return f"Could not process this input: {msg}"


def run_pipeline_ui(source: str, language: str) -> dict:
    """Same pipeline as the CLI, with live progress."""
    steps = [
        "Preparing and splitting audio",
        "Transcribing speech",
        "Writing title and summary",
        "Finding action items, decisions and questions",
        "Indexing transcript for chat",
    ]
    with st.status("Analyzing your audio…", expanded=True) as status:
        st.write(f"⏳ {steps[0]}")
        chunks = process_input(source)

        st.write(f"⏳ {steps[1]}")
        transcript = transcribe_all(chunks, language)

        st.write(f"⏳ {steps[2]}")
        title = with_retry(generate_title, transcript)
        time.sleep(1.0)
        summary = with_retry(summarize, transcript)

        st.write(f"⏳ {steps[3]}")
        time.sleep(1.0)
        actions = with_retry(extract_action_items, transcript)
        time.sleep(1.0)
        decisions = with_retry(extract_key_decisions, transcript)
        time.sleep(1.0)
        questions = with_retry(extract_questions, transcript)

        st.write(f"⏳ {steps[4]}")
        rag_chain = build_rag_chain(transcript)

        status.update(label="Analysis complete", state="complete", expanded=False)

    return {
        "title": title,
        "transcript": transcript,
        "summary": summary,
        "action_items": actions,
        "key_decisions": decisions,
        "open_questions": questions,
        "rag_chain": rag_chain,
        "source": source,
        "language": language,
        "created": time.strftime("%d %b %Y, %I:%M %p"),
    }


# ------------------------------------------------------------------ session state
st.session_state.setdefault("result", None)
st.session_state.setdefault("messages", [])
st.session_state.setdefault("pending_q", None)

# ------------------------------------------------------------------ sidebar
with st.sidebar:
    st.markdown('<div class="brand">AI Video <span>Assistant</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="tagline">Turn any recording into notes you can chat with.</div>', unsafe_allow_html=True)

    if IS_HOSTED:
        st.markdown('<div class="mode-pill">Hosted · audio only</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="mode-note">This hosted version accepts audio files. '
            'For YouTube links and video files, run the app locally.</div>',
            unsafe_allow_html=True,
        )
        input_mode = "Upload file"
        accepted_types = AUDIO_TYPES
        upload_label = "Audio file"
    else:
        st.markdown('<div class="mode-pill">Local · YouTube, video and audio</div>', unsafe_allow_html=True)
        input_mode = st.radio("Source", ["YouTube link", "Upload file"], horizontal=True)
        accepted_types = AUDIO_TYPES + VIDEO_TYPES
        upload_label = "Audio or video file"

    youtube_url, uploaded = "", None

    if input_mode == "YouTube link":
        youtube_url = st.text_input("YouTube URL", placeholder="https://www.youtube.com/watch?v=…").strip()
    else:
        uploaded = st.file_uploader(upload_label, type=accepted_types)

    language = st.selectbox("Spoken language", ["english", "hinglish"])

    has_input = bool(youtube_url) if input_mode == "YouTube link" else uploaded is not None
    go = st.button("Analyze", disabled=not has_input)

    if st.session_state.result:
        st.divider()
        if st.button("Start over"):
            st.session_state.result = None
            st.session_state.messages = []
            st.rerun()

# ------------------------------------------------------------------ run analysis
if go and has_input:
    tmp_path = None
    try:
        if input_mode == "YouTube link":
            source = youtube_url
        else:
            ext = os.path.splitext(uploaded.name)[1].lower().lstrip(".")
            if IS_HOSTED and ext not in AUDIO_TYPES:
                raise ValueError("The hosted version accepts audio files only (mp3, wav, m4a, aac, ogg, flac, wma).")
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as f:
                f.write(uploaded.getbuffer())
                tmp_path = f.name
            source = tmp_path

        st.session_state.result = run_pipeline_ui(source, language)
        st.session_state.messages = []
    except Exception as e:
        st.error(friendly_error(e))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass

result = st.session_state.result

# ------------------------------------------------------------------ landing
if not result:
    if IS_HOSTED:
        sub = (
            "Upload an audio recording. You get a transcript, a summary, the action items and "
            "decisions, and a chat that answers questions from what was actually said."
        )
    else:
        sub = (
            "Paste a YouTube link or upload an audio or video file. You get a transcript, a summary, "
            "the action items and decisions, and a chat that answers questions from what was actually said."
        )
    st.markdown(
        f"""
        <div class="hero">
          <div class="hero-title">Listen less. Know more.</div>
          <div class="hero-sub">{sub}</div>
        </div>
        <div class="feature-row">
          <div class="feature"><b>Summary</b><span>The whole recording in a few clear points.</span></div>
          <div class="feature"><b>Action items</b><span>Who needs to do what, and by when.</span></div>
          <div class="feature"><b>Decisions and questions</b><span>What was settled and what is still open.</span></div>
          <div class="feature"><b>Chat with the recording</b><span>Ask anything, answers come from the transcript.</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

# ------------------------------------------------------------------ results
words = len(result["transcript"].split())
read_min = max(1, round(words / 220))

st.markdown(f'<div class="result-title">{result["title"]}</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="result-meta">Analyzed {result["created"]} · language: {result["language"]}</div>',
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="metric-grid">
      <div class="metric m1"><div class="num">{words:,}</div><div class="lbl">Words transcribed</div></div>
      <div class="metric m2"><div class="num">{count_items(result['action_items'])}</div><div class="lbl">Action items</div></div>
      <div class="metric m3"><div class="num">{count_items(result['key_decisions'])}</div><div class="lbl">Key decisions</div></div>
      <div class="metric m4"><div class="num">{count_items(result['open_questions'])}</div><div class="lbl">Open questions</div></div>
    </div>
    """,
    unsafe_allow_html=True,
)

tab_overview, tab_outcomes, tab_transcript, tab_chat = st.tabs(
    ["Overview", "Actions and decisions", "Transcript", "Chat"]
)

with tab_overview:
    card("Summary", result["summary"], "accent")
    st.caption(f"About {read_min} min to read the full transcript.")
    st.download_button(
        "Download report (.md)",
        data=build_report_md(result),
        file_name="meeting-report.md",
        mime="text/markdown",
    )

with tab_outcomes:
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        card("Action items", result["action_items"], "amber")
    with c2:
        card("Key decisions", result["key_decisions"], "mint")
    st.write("")
    card("Open questions", result["open_questions"], "rose")

with tab_transcript:
    query = st.text_input("Search the transcript", placeholder="Type a word or phrase")
    text = result["transcript"]
    safe = text.replace("<", "&lt;").replace(">", "&gt;")
    if query:
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        hits = len(pattern.findall(safe))
        safe = pattern.sub(lambda m: f"<mark>{m.group(0)}</mark>", safe)
        st.caption(f"{hits} match{'es' if hits != 1 else ''}")
    st.markdown(f'<div class="transcript">{safe}</div>', unsafe_allow_html=True)
    st.write("")
    st.download_button("Download transcript (.txt)", data=text, file_name="transcript.txt")

with tab_chat:
    st.markdown("Ask a question. Answers come from this recording's transcript.")

    if not st.session_state.messages:
        cols = st.columns(len(SUGGESTED))
        for col, q in zip(cols, SUGGESTED):
            if col.button(q, key=f"sugg_{q}"):
                st.session_state.pending_q = q
                st.rerun()

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    typed = st.chat_input("Ask about the recording…")
    question = typed or st.session_state.pending_q
    st.session_state.pending_q = None

    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            with st.spinner("Searching the transcript…"):
                try:
                    answer = with_retry(ask_question, result["rag_chain"], question)
                except Exception as e:
                    answer = friendly_error(e)
            st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})