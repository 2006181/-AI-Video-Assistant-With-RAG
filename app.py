"""
AI Video Assistant - Streamlit UI
Run with:  streamlit run app.py
Place this file in the same folder as your existing main file
(next to the `core/` and `utils/` folders).
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
#MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; height: 0; }
.block-container { padding-top: 2rem; max-width: 1200px; }

h1, h2, h3, .hero-title { font-family: 'Sora', sans-serif !important; letter-spacing: -0.02em; }

/* sidebar */
section[data-testid="stSidebar"] { background: var(--surface); border-right: 1px solid var(--line); }
section[data-testid="stSidebar"] * { color: var(--text); }
.brand { font-family: 'Sora', sans-serif; font-weight: 800; font-size: 1.3rem; margin-bottom: .2rem; }
.brand span { color: var(--accent); }
.tagline { color: var(--muted); font-size: .85rem; margin-bottom: 1.2rem; }

/* hero */
.hero { padding: 2.2rem 2.4rem; border: 1px solid var(--line); border-radius: 20px;
        background: linear-gradient(135deg, var(--surface) 0%, var(--surface-2) 100%); margin-bottom: 1.4rem; }
.hero-title { font-size: 2.6rem; font-weight: 800; line-height: 1.1; margin: 0 0 .6rem 0; }
.hero-sub { color: var(--muted); font-size: 1.05rem; max-width: 620px; }

/* feature chips on landing */
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
.card { background: var(--surface); border: 1px solid var(--line); border-radius: 16px; padding: 1.3rem 1.5rem; height: 100%; }
.card h4 { font-family: 'Sora', sans-serif; margin: 0 0 .7rem 0; font-size: 1.05rem; }
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
    # Render body as real markdown (lists etc.) just below the card header
    st.markdown(body if str(body).strip() else "_Nothing found._")


def run_pipeline_ui(source: str, language: str) -> dict:
    """Same pipeline as the CLI, with live progress."""
    steps = [
        "Downloading and splitting audio",
        "Transcribing speech",
        "Writing title and summary",
        "Finding action items, decisions and questions",
        "Indexing transcript for chat",
    ]
    with st.status("Analyzing your video…", expanded=True) as status:
        st.write(f"⏳ {steps[0]}")
        chunks = process_input(source)

        st.write(f"⏳ {steps[1]}")
        transcript = transcribe_all(chunks, language)

        st.write(f"⏳ {steps[2]}")
        title = generate_title(transcript)
        summary = summarize(transcript)

        st.write(f"⏳ {steps[3]}")
        actions = extract_action_items(transcript)
        decisions = extract_key_decisions(transcript)
        questions = extract_questions(transcript)

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
    st.markdown('<div class="tagline">Turn any video or meeting into notes you can chat with.</div>', unsafe_allow_html=True)

    input_mode = st.radio("Source", ["YouTube link", "Upload file"], horizontal=True)
    source, tmp_path = None, None

    if input_mode == "YouTube link":
        source = st.text_input("YouTube URL", placeholder="https://www.youtube.com/watch?v=…").strip()
    else:
        up = st.file_uploader(
            "Audio or video file",
            type=["mp3", "wav", "m4a", "mp4", "mkv", "mov", "webm"],
        )
        if up is not None:
            suffix = os.path.splitext(up.name)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
                f.write(up.getbuffer())
                tmp_path = f.name
            source = tmp_path

    language = st.selectbox("Spoken language", ["english", "hinglish"])

    go = st.button("Analyze", use_container_width=True, disabled=not source)

    if st.session_state.result:
        st.divider()
        if st.button("Start over", use_container_width=True):
            st.session_state.result = None
            st.session_state.messages = []
            st.rerun()

# ------------------------------------------------------------------ run analysis
if go and source:
    try:
        st.session_state.result = run_pipeline_ui(source, language)
        st.session_state.messages = []
    except Exception as e:
        st.error(
            f"Could not process this input: {e}\n\n"
            "Check the link or file, then press Analyze again."
        )

result = st.session_state.result

# ------------------------------------------------------------------ landing
if not result:
    st.markdown(
        """
        <div class="hero">
          <div class="hero-title">Watch less. Know more.</div>
          <div class="hero-sub">Paste a YouTube link or upload a recording. You get a transcript,
          a summary, the action items and decisions, and a chat that answers questions from what was actually said.</div>
        </div>
        <div class="feature-row">
          <div class="feature"><b>Summary</b><span>The whole video in a few clear paragraphs.</span></div>
          <div class="feature"><b>Action items</b><span>Who needs to do what, pulled from the talk.</span></div>
          <div class="feature"><b>Decisions and questions</b><span>What was settled and what is still open.</span></div>
          <div class="feature"><b>Chat with the video</b><span>Ask anything, answers come from the transcript.</span></div>
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
        file_name="video-report.md",
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
    st.markdown("Ask a question. Answers come from this video's transcript.")

    if not st.session_state.messages:
        cols = st.columns(len(SUGGESTED))
        for col, q in zip(cols, SUGGESTED):
            if col.button(q, key=f"sugg_{q}"):
                st.session_state.pending_q = q
                st.rerun()

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    typed = st.chat_input("Ask about the video…")
    question = typed or st.session_state.pending_q
    st.session_state.pending_q = None

    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            with st.spinner("Searching the transcript…"):
                try:
                    answer = ask_question(result["rag_chain"], question)
                except Exception as e:
                    answer = f"I couldn't get an answer: {e}"
            st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})