import streamlit as st
import streamlit.components.v1 as components
import fitz
import re
import json
from html import escape
from datetime import datetime, timezone, timedelta

from summarizer.summary import summarize
from ai_engine.gemini import ask_gemini
from history import (
    create_table,
    save_history,
    get_history,
    delete_history
)

st.set_page_config(
    page_title="Smart AI Study Buddy",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

create_table()

# Only the first MAX_CHARS characters of a PDF are sent to the AI.
# This keeps very large PDFs from causing errors. Raise it if you need more.
MAX_CHARS = 100_000

IST = timezone(timedelta(hours=5, minutes=30))

# ---------------- PROFESSIONAL UI ----------------
# Theme: deep midnight blue, dotted study-paper texture, violet accent.
# Change the whole palette in one place: the :root variables below.

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&family=Inter:wght@400;500;600&display=swap');

:root {
    color-scheme: dark;
    --bg: #0B0F1E;
    --panel: #131A30;
    --panel-hover: #1A2342;
    --line: #29335A;
    --ink: #EEF0FB;
    --muted: #A3ADD0;
    --accent: #8B5CF6;        /* violet: the main accent */
    --accent-light: #B79CFF;
    --accent-deep: #6D28D9;
    --indigo: #4F46E5;
    --ok: #5EEAD4;
    --info: #7CB0FF;
    --warn: #FBBF24;
    --bad: #FF8A8A;
    --radius: 16px;
}

/* ---------- Whole-site background ---------- */
html, body,
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
    background-color: var(--bg) !important;
    color: var(--ink);
}

.stApp,
[data-testid="stAppViewContainer"] {
    background-image:
        radial-gradient(700px 420px at 12% -5%, rgba(139, 92, 246, 0.28), transparent 70%),
        radial-gradient(640px 400px at 95% 8%, rgba(79, 70, 229, 0.22), transparent 70%),
        radial-gradient(600px 380px at 60% 105%, rgba(139, 92, 246, 0.14), transparent 70%),
        radial-gradient(rgba(163, 173, 208, 0.13) 1px, transparent 1.2px) !important;
    background-size: 100% 100%, 100% 100%, 100% 100%, 26px 26px !important;
    background-attachment: fixed !important;
    font-family: 'Inter', sans-serif;
}

[data-testid="stHeader"] {
    background: transparent !important;
}

[data-testid="stHeader"] * {
    color: var(--ink) !important;
}

/* Hide Deploy button and footer */
[data-testid="stAppDeployButton"],
.stDeployButton,
footer {
    display: none !important;
}

.block-container {
    max-width: 1000px;
    padding-top: 2.5rem;
    padding-bottom: 4rem;
}

/* ---------- Type ---------- */
h1, h2, h3, h4,
[data-testid="stHeading"],
[data-testid="stHeading"] * {
    font-family: 'Plus Jakarta Sans', sans-serif;
    color: var(--ink) !important;
    letter-spacing: -0.015em;
}

h2 { font-weight: 800; }
h3 { font-weight: 700; }

/* Violet accent bar before section headings */
[data-testid="stHeading"] h2::before,
[data-testid="stHeading"] h3::before {
    content: "";
    display: inline-block;
    width: 5px;
    height: 0.9em;
    margin-right: 0.55rem;
    border-radius: 4px;
    vertical-align: -0.1em;
    background: linear-gradient(180deg, var(--accent-light), var(--accent-deep));
}

p, label, li, span,
[data-testid="stMarkdownContainer"],
[data-testid="stMarkdownContainer"] *,
[data-testid="stWidgetLabel"],
[data-testid="stWidgetLabel"] * {
    color: var(--ink);
}

[data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] * {
    color: var(--muted) !important;
}

code {
    background: var(--panel) !important;
    color: var(--accent-light) !important;
}

hr {
    border-color: var(--line) !important;
}

/* ---------- Hero ---------- */
.hero {
    padding: 0.5rem 0 1.25rem 0;
}

.hero-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-weight: 800;
    font-size: clamp(2.2rem, 5vw, 3.6rem);
    line-height: 1.08;
    letter-spacing: -0.03em;
    color: #FFFFFF;
    margin: 0 0 0.9rem 0;
}

.hero-sub {
    margin: 0.6rem 0 1.1rem 0;
    font-size: 1.1rem;
    color: var(--muted) !important;
    max-width: 60ch;
    line-height: 1.6;
}

.chips {
    display: flex;
    flex-wrap: wrap;
    gap: 0.55rem;
}

.chip {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    border: 1px solid var(--line);
    background: rgba(19, 26, 48, 0.8);
    color: var(--ink);
    border-radius: 999px;
    padding: 0.35rem 0.9rem;
    font-size: 0.85rem;
    font-weight: 600;
}

.chip::before {
    content: "";
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: var(--accent);
    box-shadow: 0 0 8px var(--accent);
}

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"],
[data-testid="stSidebar"] > div {
    background: #080B17 !important;
}

[data-testid="stSidebar"] {
    border-right: 1px solid var(--line);
}

[data-testid="stSidebar"] h2 {
    font-size: 1.45rem;
    color: var(--ink) !important;
}

/* ---------- File uploader: dashed drop zone ---------- */
[data-testid="stFileUploader"] {
    background: transparent;
    border: none;
    padding: 0;
}

[data-testid="stFileUploaderDropzone"] {
    background: var(--panel) !important;
    border: 2px dashed var(--line);
    border-radius: var(--radius);
    padding: 1.25rem;
    transition: border-color 0.2s ease, background 0.2s ease, box-shadow 0.2s ease;
}

[data-testid="stFileUploaderDropzone"]:hover {
    border-color: var(--accent);
    background: var(--panel-hover) !important;
    box-shadow: 0 0 0 4px rgba(139, 92, 246, 0.15);
}

[data-testid="stFileUploaderDropzone"] *,
[data-testid="stFileUploader"] small,
[data-testid="stFileUploader"] label {
    color: var(--ink) !important;
}

[data-testid="stFileUploaderDropzone"] small {
    color: var(--muted) !important;
}

[data-testid="stFileUploaderDropzone"] button {
    background: transparent !important;
    border: 1px solid var(--accent) !important;
    border-radius: 10px;
    font-weight: 600;
}

[data-testid="stFileUploaderDropzone"] button * {
    color: var(--accent-light) !important;
}

[data-testid="stFileUploaderDropzone"] button:hover {
    background: var(--accent) !important;
}

[data-testid="stFileUploaderDropzone"] button:hover * {
    color: #FFFFFF !important;
}

/* ---------- Buttons ---------- */
.stButton > button,
.stDownloadButton > button {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 12px;
    min-height: 44px;
    font-weight: 600;
    transition: transform 0.15s ease, border-color 0.15s ease, background 0.15s ease, box-shadow 0.15s ease;
}

.stButton > button *,
.stDownloadButton > button * {
    color: var(--ink) !important;
}

.stButton > button:hover,
.stDownloadButton > button:hover {
    background: var(--panel-hover);
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.15);
}

.stButton > button:active,
.stDownloadButton > button:active {
    transform: translateY(1px);
}

.stButton > button:disabled {
    opacity: 0.4;
}

/* Primary action (Generate, Submit Quiz): purple gradient */
.stButton > button[kind="primary"],
.stButton > button[data-testid="stBaseButton-primary"] {
    background: linear-gradient(135deg, var(--indigo), var(--accent) 60%, #A78BFA);
    border: none;
    font-weight: 700;
    min-height: 54px;
    font-size: 1.05rem;
    border-radius: 14px;
    box-shadow: 0 8px 28px rgba(124, 58, 237, 0.45);
}

.stButton > button[kind="primary"] *,
.stButton > button[data-testid="stBaseButton-primary"] * {
    color: #FFFFFF !important;
}

.stButton > button[kind="primary"]:hover,
.stButton > button[data-testid="stBaseButton-primary"]:hover {
    background: linear-gradient(135deg, #5B54F0, #9A6FFF 60%, #B79CFF);
    transform: translateY(-2px);
    box-shadow: 0 12px 34px rgba(139, 92, 246, 0.55);
}

.stButton > button[kind="primary"]:active,
.stButton > button[data-testid="stBaseButton-primary"]:active {
    transform: translateY(0);
}

/* ---------- Selectbox ---------- */
[data-baseweb="select"] > div {
    background: var(--panel) !important;
    border: 1px solid var(--line);
    border-radius: 12px;
    min-height: 48px;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

[data-baseweb="select"] > div:hover,
[data-baseweb="select"] > div:focus-within {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.2);
}

[data-baseweb="select"] * {
    color: var(--ink) !important;
}

[data-baseweb="popover"],
[data-baseweb="popover"] > div,
[data-baseweb="popover"] ul,
[data-baseweb="menu"] {
    background: var(--panel) !important;
    border-radius: 12px;
}

[data-baseweb="popover"] li,
[data-baseweb="popover"] li * {
    background: transparent;
    color: var(--ink) !important;
}

[data-baseweb="popover"] li:hover,
[data-baseweb="menu"] li:hover {
    background: var(--panel-hover) !important;
}

/* ---------- Text input (history search) ---------- */
[data-baseweb="input"],
[data-baseweb="base-input"] {
    background: var(--panel) !important;
    border-radius: 12px;
}

[data-baseweb="input"] {
    border: 1px solid var(--line);
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

[data-baseweb="input"]:focus-within {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.2);
}

[data-testid="stTextInput"] input {
    color: var(--ink) !important;
    background: transparent !important;
}

/* ---------- Radio (quiz options) ---------- */
[data-testid="stRadio"] label {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 10px;
    padding: 0.45rem 0.8rem;
    margin-bottom: 0.3rem;
    transition: border-color 0.15s ease, background 0.15s ease;
}

[data-testid="stRadio"] label:hover {
    border-color: var(--accent);
    background: var(--panel-hover);
}

/* ---------- Panels: results, flashcards, history ---------- */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: linear-gradient(160deg, rgba(139, 92, 246, 0.10), rgba(19, 26, 48, 0.95) 45%);
    border: 1px solid var(--line);
    border-radius: 18px;
}

[data-testid="stExpander"] {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 14px;
}

[data-testid="stExpander"] details,
[data-testid="stExpander"] summary {
    background: transparent !important;
}

[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary * {
    color: var(--ink) !important;
}

[data-testid="stExpander"] summary:hover,
[data-testid="stExpander"] summary:hover * {
    color: var(--accent-light) !important;
}

/* ---------- Chat ---------- */
[data-testid="stChatMessage"] {
    background: var(--panel) !important;
    border: 1px solid var(--line);
    border-radius: var(--radius);
    padding: 1rem;
}

[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
    border-left: 4px solid var(--accent);
    background: linear-gradient(90deg, rgba(139, 92, 246, 0.14), var(--panel) 40%) !important;
}

[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
    border-left: 4px solid var(--info);
}

[data-testid="stChatInput"],
[data-testid="stChatInput"] > div {
    background: var(--panel) !important;
}

[data-testid="stChatInput"] {
    border: 1px solid var(--line);
    border-radius: 999px;
}

[data-testid="stChatInput"]:focus-within {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.22);
}

[data-testid="stChatInput"] textarea {
    color: var(--ink) !important;
    background: transparent !important;
}

[data-testid="stBottom"],
[data-testid="stBottom"] > div,
[data-testid="stBottomBlockContainer"] {
    background: transparent !important;
}

/* ---------- Alerts ---------- */
[data-testid="stAlert"] {
    background: var(--panel) !important;
    border: 1px solid var(--line);
    border-left-width: 4px;
    border-radius: 12px;
}

[data-testid="stAlert"] * { color: var(--ink) !important; }

[data-testid="stAlert"]:has([data-testid="stAlertContentSuccess"]) { border-left-color: var(--ok); }
[data-testid="stAlert"]:has([data-testid="stAlertContentInfo"])    { border-left-color: var(--info); }
[data-testid="stAlert"]:has([data-testid="stAlertContentWarning"]) { border-left-color: var(--warn); }
[data-testid="stAlert"]:has([data-testid="stAlertContentError"])   { border-left-color: var(--bad); }

/* ---------- Progress, spinner, scrollbar ---------- */
[data-testid="stProgressBar"] > div {
    background: var(--line) !important;
}

[data-testid="stProgressBar"] > div > div {
    background: linear-gradient(90deg, var(--indigo), var(--accent-light)) !important;
}

[data-testid="stSpinner"] * {
    color: var(--muted) !important;
}

::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--line); border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: #3C4878; }

/* ---------- How it works ---------- */
.steps {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 0.8rem;
    margin: 0.25rem 0 1.4rem 0;
}

.step {
    display: flex;
    align-items: flex-start;
    gap: 0.8rem;
    padding: 0.95rem 1rem;
    border: 1px solid var(--line);
    border-radius: var(--radius);
    background: rgba(19, 26, 48, 0.8);
}

.step-num {
    flex-shrink: 0;
    width: 30px;
    height: 30px;
    border-radius: 50%;
    display: grid;
    place-items: center;
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-weight: 800;
    font-size: 0.9rem;
    color: #FFFFFF !important;
    background: linear-gradient(135deg, var(--indigo), var(--accent));
}

.step-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-weight: 700;
    font-size: 0.98rem;
    color: var(--ink) !important;
}

.step-text {
    font-size: 0.85rem;
    margin-top: 0.15rem;
    color: var(--muted) !important;
}

/* ---------- Empty state ---------- */
.empty-card {
    text-align: center;
    padding: 2rem 1.25rem;
    margin: 0 0 1.5rem 0;
    border: 2px dashed var(--line);
    border-radius: 18px;
    background: linear-gradient(160deg, rgba(139, 92, 246, 0.10), rgba(19, 26, 48, 0.9) 60%);
}

.empty-icon {
    font-size: 2.2rem;
    margin-bottom: 0.4rem;
}

.empty-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-weight: 800;
    font-size: 1.25rem;
    color: var(--ink) !important;
}

.empty-text {
    margin-top: 0.3rem;
    color: var(--muted) !important;
}

/* ---------- Sidebar stat cards ---------- */
.file-name {
    margin: 0.6rem 0 0.5rem 0;
    padding: 0.55rem 0.8rem;
    border: 1px solid var(--line);
    border-radius: 12px;
    background: var(--panel);
    font-weight: 600;
    font-size: 0.9rem;
    word-break: break-word;
    color: var(--ink) !important;
}

.stat-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 0.5rem;
    margin-bottom: 0.5rem;
}

.stat {
    text-align: center;
    padding: 0.6rem 0.3rem;
    border: 1px solid var(--line);
    border-radius: 12px;
    background: var(--panel);
}

.stat-value {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-weight: 800;
    font-size: 1.3rem;
    color: var(--accent-light) !important;
}

.stat-label {
    font-size: 0.72rem;
    color: var(--muted) !important;
}

/* ---------- Quiz score card ---------- */
.score-card {
    display: flex;
    align-items: center;
    gap: 1.4rem;
    padding: 1.2rem 1.4rem;
    margin: 1rem 0;
    border: 1px solid var(--line);
    border-radius: 18px;
    background: linear-gradient(160deg, rgba(139, 92, 246, 0.14), rgba(19, 26, 48, 0.95) 55%);
}

.ring {
    position: relative;
    flex-shrink: 0;
    width: 104px;
    height: 104px;
    border-radius: 50%;
    display: grid;
    place-items: center;
    background: conic-gradient(var(--accent-light) calc(var(--p) * 1%), var(--line) 0);
}

.ring::before {
    content: "";
    position: absolute;
    inset: 9px;
    border-radius: 50%;
    background: var(--panel);
}

.ring span {
    position: relative;
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-weight: 800;
    font-size: 1.35rem;
    color: #FFFFFF !important;
}

.score-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-weight: 800;
    font-size: 1.3rem;
    color: var(--ink) !important;
}

.score-sub {
    margin-top: 0.2rem;
    color: var(--muted) !important;
}

/* ---------- Accessibility ---------- */
button:focus-visible,
[data-baseweb="select"] > div:focus-visible {
    outline: 2px solid var(--accent-light);
    outline-offset: 2px;
}

@media (prefers-reduced-motion: reduce) {
    * { transition: none !important; animation: none !important; }
}

@media (max-width: 640px) {
    .block-container { padding-left: 1rem; padding-right: 1rem; }
    .steps { grid-template-columns: 1fr; }
    .score-card { flex-direction: column; text-align: center; }
}
</style>
""", unsafe_allow_html=True)


# ---------------- HELPERS ----------------

@st.cache_data(show_spinner=False)
def extract_pdf(file_bytes):
    """Read the PDF once and cache it, so it is not re-read on every click."""
    pdf = fitz.open(stream=file_bytes, filetype="pdf")
    try:
        pages = pdf.page_count
        content = "\n".join(page.get_text() for page in pdf)
    finally:
        pdf.close()
    return content, pages


def to_ist(created_at):
    try:
        return datetime.strptime(
            created_at, "%Y-%m-%d %H:%M:%S"
        ).replace(tzinfo=timezone.utc).astimezone(IST)
    except (ValueError, TypeError):
        return None


def compute_streak(active_days):
    """Consecutive days of activity, ending today (or yesterday)."""
    today = datetime.now(IST).date()

    if today in active_days:
        day = today
    elif (today - timedelta(days=1)) in active_days:
        day = today - timedelta(days=1)
    else:
        return 0

    streak = 0
    while day in active_days:
        streak += 1
        day -= timedelta(days=1)
    return streak


def pdf_safe(value):
    """The built-in PDF fonts only support Latin-1, so swap common symbols."""
    replacements = {
        "\u2014": "-", "\u2013": "-", "\u2018": "'", "\u2019": "'",
        "\u201c": '"', "\u201d": '"', "\u2022": "-", "\u2026": "...",
        "\u00a0": " "
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    return value.encode("latin-1", "replace").decode("latin-1")


def make_pdf(title, body):
    """Return PDF bytes, or None if fpdf2 is not installed or fails."""
    try:
        from fpdf import FPDF
    except ImportError:
        return None

    try:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        pdf.set_font("Helvetica", "B", 18)
        pdf.multi_cell(0, 10, pdf_safe(title),
                       new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

        pdf.set_font("Helvetica", size=12)
        for line in pdf_safe(body).split("\n"):
            pdf.multi_cell(0, 7, line if line.strip() else " ",
                           new_x="LMARGIN", new_y="NEXT")

        return bytes(pdf.output())
    except Exception:
        return None


def tts_player(content):
    """Listen / Stop buttons using the browser's built-in speech engine."""
    payload = json.dumps(content[:8000]).replace("</", "<\\/")

    components.html("""
    <style>
        body { margin: 0; font-family: Inter, sans-serif; background: transparent; }
        .row { display: flex; gap: 10px; align-items: center; }
        button {
            cursor: pointer; border-radius: 12px; padding: 10px 18px;
            font-weight: 600; font-size: 14px; border: 1px solid #29335A;
            background: #131A30; color: #EEF0FB; transition: all .15s ease;
        }
        button:hover { border-color: #8B5CF6; }
        button.primary {
            border: none; color: #fff;
            background: linear-gradient(135deg, #4F46E5, #8B5CF6 60%, #A78BFA);
        }
        #msg { color: #A3ADD0; font-size: 13px; }
    </style>
    <div class="row">
        <button class="primary" onclick="speak()">&#9654; Listen</button>
        <button onclick="stopSpeech()">&#9632; Stop</button>
        <span id="msg"></span>
    </div>
    <script>
        const text = __TEXT__;
        const chunks = text.match(/[^.!?\\n]+[.!?]?/g) || [text];

        function speak() {
            if (!("speechSynthesis" in window)) {
                document.getElementById("msg").textContent =
                    "Speech is not supported in this browser.";
                return;
            }
            speechSynthesis.cancel();
            chunks.forEach(function (c) {
                if (c.trim()) {
                    speechSynthesis.speak(new SpeechSynthesisUtterance(c.trim()));
                }
            });
        }

        function stopSpeech() {
            if ("speechSynthesis" in window) { speechSynthesis.cancel(); }
        }
    </script>
    """.replace("__TEXT__", payload), height=56)


# ---------------- HEADER ----------------
st.markdown("""
<div class="hero">
    <div class="hero-title">📚 Smart AI Study Buddy</div>
    <p class="hero-sub">
        Your AI-powered learning assistant — summarize, practice,
        revise, and ask questions.
    </p>
    <div class="chips">
        <span class="chip">Summaries</span>
        <span class="chip">Quizzes</span>
        <span class="chip">Flashcards</span>
        <span class="chip">Chat with PDF</span>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="steps">
    <div class="step">
        <div class="step-num">1</div>
        <div>
            <div class="step-title">Upload</div>
            <div class="step-text">Add your study PDF in the sidebar.</div>
        </div>
    </div>
    <div class="step">
        <div class="step-num">2</div>
        <div>
            <div class="step-title">Choose a tool</div>
            <div class="step-text">Summary, quiz or flashcards.</div>
        </div>
    </div>
    <div class="step">
        <div class="step-num">3</div>
        <div>
            <div class="step-title">Generate</div>
            <div class="step-text">Study, download or chat with it.</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# ---------------- PDF UPLOAD ----------------
st.sidebar.header(":material/description: Study Material")

uploaded_file = st.sidebar.file_uploader(
    "Upload your PDF",
    type=["pdf"]
)

text = ""
ai_text = ""

if uploaded_file is not None:
    try:
        text, page_count = extract_pdf(uploaded_file.getvalue())

        st.sidebar.success("PDF uploaded successfully!")

        if not text.strip():
            st.sidebar.warning(
                "No readable text found in this PDF."
            )
        else:
            word_count = len(text.split())

            st.sidebar.markdown(f"""
<div class="file-name">{escape(uploaded_file.name)}</div>
<div class="stat-grid">
    <div class="stat"><div class="stat-value">{page_count}</div><div class="stat-label">Pages</div></div>
    <div class="stat"><div class="stat-value">{word_count:,}</div><div class="stat-label">Words</div></div>
    <div class="stat"><div class="stat-value">{max(1, round(word_count / 200))}</div><div class="stat-label">Min read</div></div>
</div>
""", unsafe_allow_html=True)

            ai_text = text[:MAX_CHARS]

            if len(text) > MAX_CHARS:
                st.sidebar.warning(
                    "This is a large PDF. The AI tools will use only the "
                    f"first {MAX_CHARS:,} characters."
                )

    except Exception as e:
        st.sidebar.error(f"Could not read PDF: {e}")


# ---------------- EMPTY STATE ----------------
if uploaded_file is None:
    st.markdown("""
<div class="empty-card">
    <div class="empty-icon">📄</div>
    <div class="empty-title">No PDF uploaded yet</div>
    <div class="empty-text">
        Upload a study PDF in the sidebar to unlock summaries, quizzes,
        flashcards and chat. On mobile, open the sidebar with the arrow
        at the top left.
    </div>
</div>
""", unsafe_allow_html=True)


# ---------------- FEATURE SELECTION ----------------
st.subheader(":material/target: Choose Your Learning Tool")

option = st.selectbox(
    "Select a feature",
    [
        "Summarize PDF",
        "Generate Quiz",
        "Generate Flashcards"
    ]
)

# Options that appear only for the selected tool
quiz_count = 5
difficulty = "Medium"
card_count = 5

if option == "Generate Quiz":
    opt_col1, opt_col2 = st.columns(2)
    with opt_col1:
        difficulty = st.selectbox(
            "Difficulty",
            ["Easy", "Medium", "Hard"],
            index=1
        )
    with opt_col2:
        quiz_count = st.selectbox(
            "Number of questions",
            [5, 10, 15]
        )

elif option == "Generate Flashcards":
    card_count = st.selectbox(
        "Number of flashcards",
        [5, 10, 15]
    )

if st.button(
    "Generate",
    icon=":material/auto_awesome:",
    use_container_width=True,
    type="primary"
):
    if uploaded_file is None:
        st.warning("Please upload a PDF first.")

    elif not text.strip():
        st.error("No readable text found in this PDF.")

    else:
        try:
            with st.spinner("Preparing your learning material..."):

                if option == "Summarize PDF":
                    result = summarize(ai_text)

                elif option == "Generate Quiz":
                    result = ask_gemini(
                        "Create exactly " + str(quiz_count) +
                        " multiple-choice questions at " +
                        difficulty.lower() + " difficulty "
                        "based only on this study material. Return ONLY "
                        "a valid JSON array, without markdown fences, "
                        "using this format:\n"
                        '[{"question":"Question text",'
                        '"options":["Option A","Option B",'
                        '"Option C","Option D"],'
                        '"answer":"Option A",'
                        '"explanation":"Reason"}]\n\n'
                        "The answer must exactly match one option.\n\n"
                        "Study material:\n" + ai_text
                    )

                else:
                    result = ask_gemini(
                        "Create " + str(card_count) +
                        " flashcards based on this material. "
                        "For each, use exactly this format:\n"
                        "Question: ...\nAnswer: ...\n\n"
                        "Separate each flashcard with a blank line.\n\n"
                        + ai_text
                    )

            st.session_state["last_result"] = result
            st.session_state["last_option"] = option
            st.session_state["quiz_answers"] = {}
            st.session_state["quiz_submitted"] = False
            st.session_state["flashcard_index"] = 0
            st.session_state["flashcard_flipped"] = False

            # Reset quiz selections for newly generated quiz
            for key in list(st.session_state.keys()):
                if key.startswith("quiz_answer_"):
                    del st.session_state[key]

            save_history(option, result)
            st.success("Your learning material is ready!")

        except Exception as e:
            st.error(f"Something went wrong: {e}")


# ---------------- DISPLAY RESULT ----------------
if "last_result" in st.session_state:
    result = st.session_state["last_result"]
    result_option = st.session_state["last_option"]

    st.divider()
    st.subheader(":material/menu_book: Your Learning Material")

    # ---------------- SUMMARY ----------------
    if result_option == "Summarize PDF":
        st.markdown(result)

        clean_summary = re.sub(
            r"^#{1,6}\s*", "", result, flags=re.MULTILINE
        )
        clean_summary = re.sub(
            r"\*\*(.*?)\*\*", r"\1", clean_summary
        )
        clean_summary = re.sub(
            r"\*(.*?)\*", r"\1", clean_summary
        )
        clean_summary = re.sub(
            r"(?m)^\s*[-*_]{3,}\s*$", "", clean_summary
        )
        clean_summary = re.sub(
            r"`([^`]+)`", r"\1", clean_summary
        )

        dl_col1, dl_col2 = st.columns(2)

        with dl_col1:
            st.download_button(
                label="Download Summary (.txt)",
                icon=":material/download:",
                data=clean_summary,
                file_name="study_summary.txt",
                mime="text/plain",
                use_container_width=True
            )

        summary_pdf = make_pdf("Study Summary", clean_summary)

        with dl_col2:
            if summary_pdf:
                st.download_button(
                    label="Download Summary (.pdf)",
                    icon=":material/picture_as_pdf:",
                    data=summary_pdf,
                    file_name="study_summary.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            else:
                st.caption(
                    "PDF export needs fpdf2: pip install fpdf2"
                )

        st.markdown("**Listen to your summary**")
        tts_player(clean_summary)

    # ---------------- QUIZ ----------------
    elif result_option == "Generate Quiz":
        st.download_button(
            label="Download Quiz",
            icon=":material/download:",
            data=result,
            file_name="study_quiz.json",
            mime="application/json"
        )

        try:
            quiz_text = result.strip()

            if quiz_text.startswith("```"):
                quiz_text = re.sub(
                    r"^```(?:json)?\s*|\s*```$",
                    "",
                    quiz_text
                )

            quiz = json.loads(quiz_text)

            if not isinstance(quiz, list) or not quiz:
                raise ValueError("The quiz is empty.")

            for i, item in enumerate(quiz):
                st.markdown(
                    f"**Question {i + 1}: {item['question']}**"
                )

                selected = st.radio(
                    "Choose your answer:",
                    item["options"],
                    key=f"quiz_answer_{i}",
                    index=None,
                    label_visibility="collapsed"
                )

                if selected is not None:
                    st.session_state["quiz_answers"][i] = selected

            if st.button(
                "Submit Quiz",
                icon=":material/check_circle:",
                type="primary"
            ):
                st.session_state["quiz_submitted"] = True

            if st.session_state.get("quiz_submitted", False):
                answers = st.session_state["quiz_answers"]

                score = sum(
                    1 for i, item in enumerate(quiz)
                    if answers.get(i) == item["answer"]
                )
                total = len(quiz)
                pct = round(score / total * 100)

                if pct >= 80:
                    verdict = "Excellent work!"
                elif pct >= 50:
                    verdict = "Good effort, keep going!"
                else:
                    verdict = "Review the material and try again."

                st.markdown(f"""
<div class="score-card">
    <div class="ring" style="--p:{pct}"><span>{score}/{total}</span></div>
    <div>
        <div class="score-title">{verdict}</div>
        <div class="score-sub">You answered {score} of {total} questions correctly ({pct}%).</div>
    </div>
</div>
""", unsafe_allow_html=True)

                if st.button(
                    "Retake quiz",
                    icon=":material/replay:",
                    key="retake_quiz"
                ):
                    st.session_state["quiz_answers"] = {}
                    st.session_state["quiz_submitted"] = False
                    for key in list(st.session_state.keys()):
                        if key.startswith("quiz_answer_"):
                            del st.session_state[key]
                    st.rerun()

                for i, item in enumerate(quiz):
                    chosen = answers.get(i)

                    if chosen == item["answer"]:
                        st.success(f"Question {i + 1}: Correct!")
                    else:
                        st.error(f"Question {i + 1}: Incorrect")
                        st.write(
                            f"Correct answer: {item['answer']}"
                        )

                    explanation = item.get("explanation", "")
                    if explanation:
                        st.info(explanation)

        except (
            json.JSONDecodeError,
            TypeError,
            KeyError,
            ValueError
        ):
            st.error(
                "The AI returned an invalid quiz format. "
                "Please generate the quiz again."
            )

    # ---------------- INTERACTIVE FLASHCARDS ----------------
    elif result_option == "Generate Flashcards":
        matches = re.findall(
            r"Question:\s*(.*?)\s*Answer:\s*(.*?)(?="
            r"\n\s*Question:|\Z)",
            result,
            re.DOTALL | re.IGNORECASE
        )

        matches = [
            (question.strip(), answer.strip())
            for question, answer in matches
            if question.strip() and answer.strip()
        ]

        if matches:
            if "flashcard_index" not in st.session_state:
                st.session_state["flashcard_index"] = 0

            if "flashcard_flipped" not in st.session_state:
                st.session_state["flashcard_flipped"] = False

            index = min(
                st.session_state["flashcard_index"],
                len(matches) - 1
            )
            st.session_state["flashcard_index"] = index

            question, answer = matches[index]

            st.progress((index + 1) / len(matches))
            st.caption(
                f"Flashcard {index + 1} of {len(matches)}"
            )

            with st.container(border=True):
                if st.session_state["flashcard_flipped"]:
                    st.success("ANSWER", icon=":material/check_circle:")
                    st.markdown(f"### {answer}")
                else:
                    st.info("QUESTION", icon=":material/help:")
                    st.markdown(f"### {question}")

            if st.button(
                "Flip Card",
                icon=":material/flip:",
                key="flip_card"
            ):
                st.session_state["flashcard_flipped"] = (
                    not st.session_state["flashcard_flipped"]
                )
                st.rerun()

            col1, col2 = st.columns(2)

            with col1:
                if st.button(
                    "Previous",
                    icon=":material/arrow_back:",
                    disabled=(index == 0),
                    key="previous_card"
                ):
                    st.session_state["flashcard_index"] -= 1
                    st.session_state["flashcard_flipped"] = False
                    st.rerun()

            with col2:
                if st.button(
                    "Next",
                    icon=":material/arrow_forward:",
                    disabled=(index == len(matches) - 1),
                    key="next_card"
                ):
                    st.session_state["flashcard_index"] += 1
                    st.session_state["flashcard_flipped"] = False
                    st.rerun()

            # Export all flashcards
            cards_text = "\n\n".join(
                f"Q{n}: {q}\nA{n}: {a}"
                for n, (q, a) in enumerate(matches, start=1)
            )

            fc_col1, fc_col2 = st.columns(2)

            with fc_col1:
                st.download_button(
                    label="Download Flashcards (.txt)",
                    icon=":material/download:",
                    data=cards_text,
                    file_name="study_flashcards.txt",
                    mime="text/plain",
                    use_container_width=True
                )

            cards_pdf = make_pdf("Study Flashcards", cards_text)

            with fc_col2:
                if cards_pdf:
                    st.download_button(
                        label="Download Flashcards (.pdf)",
                        icon=":material/picture_as_pdf:",
                        data=cards_pdf,
                        file_name="study_flashcards.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                else:
                    st.caption(
                        "PDF export needs fpdf2: pip install fpdf2"
                    )

        else:
            st.warning(
                "Flashcards could not be identified. "
                "Please generate them again."
            )
            st.write(result)


# ---------------- CHAT WITH PDF ----------------
st.divider()
st.header(":material/forum: Chat with PDF")
st.write("Ask questions about your uploaded study material.")

if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

if uploaded_file is not None and text.strip():

    for message in st.session_state["chat_history"]:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    question = st.chat_input("Ask a question about your PDF...")

    if question:
        st.session_state["chat_history"].append(
            {"role": "user", "content": question}
        )
        save_history("Chat - User", question)

        with st.chat_message("user"):
            st.write(question)

        with st.chat_message("assistant"):
            with st.spinner("Finding an answer..."):
                try:
                    answer = ask_gemini(
                        "You are a careful study assistant. Answer the "
                        "question using ONLY information explicitly "
                        "stated in the PDF text below.\n\n"
                        "Rules:\n"
                        "1. Do not invent facts or use outside knowledge.\n"
                        "2. If the answer is absent, say: 'This information "
                        "is not available in the provided PDF.'\n"
                        "3. If the PDF is unclear or contradictory, "
                        "mention this.\n"
                        "4. Keep the answer clear and concise.\n\n"
                        "PDF CONTENT:\n" + ai_text +
                        "\n\nUSER QUESTION:\n" + question
                    )

                    st.write(answer)

                    st.session_state["chat_history"].append(
                        {"role": "assistant", "content": answer}
                    )
                    save_history("Chat - AI", answer)

                except Exception as e:
                    st.error(f"Could not generate an answer: {e}")

    if st.button("Clear Chat", icon=":material/delete_sweep:"):
        st.session_state["chat_history"] = []
        st.rerun()

else:
    st.info("Upload a PDF in the sidebar to start chatting.")


# ---------------- SAVED HISTORY ----------------
st.divider()
st.header(":material/history: Saved History")

records = get_history()

if records:
    st.caption(
        "Your previous summaries, quizzes, flashcards, and chat messages."
    )

    search = st.text_input(
        "Search history",
        placeholder="Search your saved history...",
        label_visibility="collapsed"
    )

    query = search.strip().lower()

    filtered = [
        r for r in records
        if not query
        or query in str(r[1]).lower()
        or query in str(r[2]).lower()
    ]

    top_col1, top_col2 = st.columns([3, 1])

    with top_col1:
        st.caption(f"Showing {len(filtered)} of {len(records)} items")

    with top_col2:
        if not st.session_state.get("confirm_clear", False):
            if st.button(
                "Clear all",
                icon=":material/delete_forever:",
                key="clear_all_history",
                use_container_width=True
            ):
                st.session_state["confirm_clear"] = True
                st.rerun()

    if st.session_state.get("confirm_clear", False):
        st.warning(
            "Delete ALL saved history? This cannot be undone."
        )
        yes_col, no_col = st.columns(2)

        with yes_col:
            if st.button(
                "Yes, delete all",
                key="confirm_clear_yes",
                type="primary",
                use_container_width=True
            ):
                for r in records:
                    delete_history(r[0])
                st.session_state["confirm_clear"] = False
                st.rerun()

        with no_col:
            if st.button(
                "Cancel",
                key="confirm_clear_no",
                use_container_width=True
            ):
                st.session_state["confirm_clear"] = False
                st.rerun()

    if not filtered:
        st.info("No history matches your search.")

    for record_id, feature, content, created_at in filtered:
        ist_time = to_ist(created_at)

        if ist_time is not None:
            time_label = ist_time.strftime("%d-%m-%Y %I:%M:%S %p IST")
        else:
            time_label = str(created_at)

        with st.expander(f"{feature} — {time_label}"):
            st.write(content)

            if st.button(
                "Delete",
                icon=":material/delete:",
                key=f"delete_{record_id}"
            ):
                delete_history(record_id)
                st.success("History deleted!")
                st.rerun()

else:
    st.info(
        "No saved history yet. Generate a result or chat with your PDF."
    )


# ---------------- SIDEBAR: STUDY PROGRESS ----------------
active_days = set()
today_count = 0
today_date = datetime.now(IST).date()

for record in records:
    ist_time = to_ist(record[3])
    if ist_time is not None:
        active_days.add(ist_time.date())
        if ist_time.date() == today_date:
            today_count += 1

streak = compute_streak(active_days)

st.sidebar.divider()
st.sidebar.subheader(":material/local_fire_department: Study Progress")
st.sidebar.markdown(f"""
<div class="stat-grid">
    <div class="stat"><div class="stat-value">{streak}</div><div class="stat-label">Day streak</div></div>
    <div class="stat"><div class="stat-value">{today_count}</div><div class="stat-label">Today</div></div>
    <div class="stat"><div class="stat-value">{len(records)}</div><div class="stat-label">Saved</div></div>
</div>
""", unsafe_allow_html=True)