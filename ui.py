"""
English Learning Platform — Professional Streamlit UI
Covers: Listening · Reading · Speaking · Writing · Practice (Conversation)
"""

import streamlit as st
import requests
import base64
import json
import io
import time
from typing import Optional

# ─────────────────────────── CEFR CONFIG ──────────────────────────
CEFR_OPTIONS = {
    "A1 (Beginner)": "A1",
    "A2 (Elementary)": "A2",
    "A1-A2 (Beginner - Elementary)": "A1-A2",
    "B1 (Pre-Intermediate)": "B1",
    "B2 (Intermediate)": "B2",
    "A2-B1 (Elementary - Pre-Int.)": "A2-B1",
    "B1-B2 (Pre-Int. - Intermediate)": "B1-B2",
    "C1 (Upper-Intermediate)": "C1",
    "C2 (Advanced)": "C2",
    "B2-C1 (Intermediate - Upper-Int.)": "B2-C1",
    "C1-C2 (Upper-Int. - Advanced)": "C1-C2",
}
CEFR_LABELS = list(CEFR_OPTIONS.keys())
CEFR_DEFAULT_INDEX = 3  # B1

def cefr_value(label: str) -> str:
    """Convert CEFR label to value for API."""
    return CEFR_OPTIONS.get(label, label)

# ─────────────────────────── GRADE CONFIG ─────────────────────────
GRADE_OPTIONS = {
    "(Yok)": "",
    "2. Sınıf": "2",
    "3. Sınıf": "3",
    "4. Sınıf": "4",
    "5. Sınıf": "5",
    "6. Sınıf": "6",
    "7. Sınıf": "7",
    "8. Sınıf": "8",
    "9. Sınıf (Lise 1)": "9",
    "10. Sınıf (Lise 2)": "10",
    "11. Sınıf (Lise 3)": "11",
    "12. Sınıf (Lise 4)": "12",
}
GRADE_LABELS = list(GRADE_OPTIONS.keys())

def grade_value(label: str) -> str:
    """Convert grade label to value for API."""
    return GRADE_OPTIONS.get(label, "")

# ─────────────────────────── CONFIG ───────────────────────────
API_BASE = "http://127.0.0.1:8000/api/v1"
st.set_page_config(
    page_title="English Learning Platform",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────── CUSTOM CSS ───────────────────────
st.markdown("""
<style>
/* ---------- Import Google Fonts ---------- */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ---------- Root Variables ---------- */
:root {
    --primary: #6C63FF;
    --primary-light: #8B83FF;
    --primary-dark: #4F46E5;
    --secondary: #10B981;
    --accent: #F59E0B;
    --bg-dark: #0F172A;
    --bg-card: #1E293B;
    --bg-card-hover: #263548;
    --text-primary: #F1F5F9;
    --text-secondary: #94A3B8;
    --border: #334155;
    --success: #10B981;
    --warning: #F59E0B;
    --error: #EF4444;
    --info: #3B82F6;
    --radius: 12px;
    --shadow: 0 4px 24px rgba(0,0,0,0.25);
}

/* ---------- Global ---------- */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
}

.stApp {
    background: linear-gradient(135deg, #0F172A 0%, #1a1a2e 50%, #16213e 100%) !important;
}

/* ---------- Scrollbar ---------- */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg-dark); }
::-webkit-scrollbar-thumb { background: var(--primary); border-radius: 3px; }

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1E293B 0%, #0F172A 100%) !important;
    border-right: 1px solid var(--border);
}
section[data-testid="stSidebar"] .stRadio > label {
    color: var(--text-secondary) !important;
    font-weight: 600;
    font-size: 0.75rem;
    letter-spacing: 1.5px;
    text-transform: uppercase;
}

/* ---------- Cards ---------- */
.skill-card {
    background: linear-gradient(145deg, #1E293B, #263548);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.5rem;
    margin-bottom: 1rem;
    transition: all 0.3s ease;
    box-shadow: var(--shadow);
}
.skill-card:hover {
    border-color: var(--primary);
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(108,99,255,0.2);
}

/* ---------- Hero / Header ---------- */
.hero-section {
    text-align: center;
    padding: 2.5rem 1rem 1.5rem;
}
.hero-section h1 {
    font-size: 2.5rem;
    font-weight: 800;
    background: linear-gradient(135deg, #6C63FF, #10B981);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.5rem;
}
.hero-section p {
    color: var(--text-secondary);
    font-size: 1.1rem;
    max-width: 640px;
    margin: 0 auto;
}

/* ---------- Section Headers ---------- */
.section-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin: 1.5rem 0 1rem;
}
.section-header .icon {
    font-size: 1.5rem;
    width: 44px;
    height: 44px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 10px;
}
.section-header h2 {
    font-weight: 700;
    font-size: 1.35rem;
    color: var(--text-primary);
    margin: 0;
}
.section-header p {
    color: var(--text-secondary);
    font-size: 0.85rem;
    margin: 2px 0 0;
}

/* ---------- Stat Badges ---------- */
.stat-row {
    display: flex;
    gap: 0.75rem;
    flex-wrap: wrap;
    margin: 1rem 0;
}
.stat-badge {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.6rem 1.2rem;
    text-align: center;
    min-width: 110px;
}
.stat-badge .value {
    font-size: 1.4rem;
    font-weight: 700;
    color: var(--primary-light);
}
.stat-badge .label {
    font-size: 0.7rem;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* ---------- Score Bars ---------- */
.score-row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
}
.score-label {
    min-width: 130px;
    font-size: 0.82rem;
    color: var(--text-secondary);
    font-weight: 500;
}
.score-bar-bg {
    flex: 1;
    height: 10px;
    background: var(--bg-dark);
    border-radius: 5px;
    overflow: hidden;
}
.score-bar-fill {
    height: 100%;
    border-radius: 5px;
    transition: width 0.8s ease;
}
.score-value {
    min-width: 36px;
    text-align: right;
    font-weight: 700;
    font-size: 0.85rem;
}

/* ---------- Dialogue Bubbles ---------- */
.dialogue-container {
    max-height: 500px;
    overflow-y: auto;
    padding: 1rem;
    border-radius: var(--radius);
    background: var(--bg-dark);
    border: 1px solid var(--border);
}
.dialogue-line {
    display: flex;
    gap: 0.75rem;
    margin-bottom: 0.85rem;
    animation: fadeInUp 0.3s ease-out;
}
@keyframes fadeInUp {
    from { opacity:0; transform:translateY(8px); }
    to   { opacity:1; transform:translateY(0); }
}
.speaker-badge {
    font-weight: 700;
    font-size: 0.75rem;
    padding: 4px 10px;
    border-radius: 6px;
    white-space: nowrap;
    height: fit-content;
}
.speaker-1 { background: rgba(108,99,255,0.2); color: #8B83FF; }
.speaker-2 { background: rgba(16,185,129,0.2); color: #34D399; }

.dialogue-text {
    background: var(--bg-card);
    padding: 0.65rem 1rem;
    border-radius: 10px;
    color: var(--text-primary);
    font-size: 0.92rem;
    line-height: 1.5;
    flex: 1;
}

/* ---------- Question Card ---------- */
.question-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.25rem;
    margin-bottom: 1rem;
}
.question-card h4 {
    color: var(--text-primary);
    margin: 0 0 0.75rem;
    font-size: 0.95rem;
}
.correct-answer {
    background: rgba(16,185,129,0.15);
    border: 1px solid rgba(16,185,129,0.3);
    border-radius: 8px;
    padding: 0.5rem 0.75rem;
    color: #34D399;
    font-weight: 600;
    margin-top: 0.5rem;
    font-size: 0.85rem;
}
.explanation-box {
    background: rgba(59,130,246,0.1);
    border-left: 3px solid var(--info);
    padding: 0.5rem 0.75rem;
    margin-top: 0.5rem;
    border-radius: 0 8px 8px 0;
    color: var(--text-secondary);
    font-size: 0.82rem;
}

/* ---------- Error Card (Writing) ---------- */
.error-card {
    background: rgba(239,68,68,0.08);
    border: 1px solid rgba(239,68,68,0.25);
    border-radius: var(--radius);
    padding: 1rem;
    margin-bottom: 0.75rem;
}
.error-card .error-type {
    display: inline-block;
    background: rgba(239,68,68,0.2);
    color: #FCA5A5;
    font-size: 0.7rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 4px;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}
.error-card .original {
    color: var(--text-secondary);
    font-size: 0.85rem;
    margin-bottom: 0.3rem;
}
.error-card .corrected {
    color: var(--success);
    font-size: 0.85rem;
    margin-bottom: 0.3rem;
}
.error-card .note {
    color: var(--text-secondary);
    font-size: 0.78rem;
    font-style: italic;
}

/* ---------- Chat ---------- */
.chat-container {
    max-height: 500px;
    overflow-y: auto;
    padding: 1rem;
    border-radius: var(--radius);
    background: var(--bg-dark);
    border: 1px solid var(--border);
}
.chat-bubble {
    padding: 0.75rem 1rem;
    border-radius: 12px;
    margin-bottom: 0.75rem;
    max-width: 80%;
    font-size: 0.92rem;
    line-height: 1.5;
    animation: fadeInUp 0.3s ease;
}
.chat-bubble.user {
    background: linear-gradient(135deg, var(--primary), var(--primary-dark));
    color: white;
    margin-left: auto;
    border-bottom-right-radius: 4px;
}
.chat-bubble.ai {
    background: var(--bg-card);
    color: var(--text-primary);
    border: 1px solid var(--border);
    margin-right: auto;
    border-bottom-left-radius: 4px;
}
.chat-meta {
    font-size: 0.7rem;
    color: var(--text-secondary);
    margin-bottom: 0.25rem;
    font-weight: 600;
}

/* ---------- Reading Text Display ---------- */
.reading-text-box {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.5rem;
    color: var(--text-primary);
    font-size: 1rem;
    line-height: 1.8;
    max-height: 500px;
    overflow-y: auto;
}
.reading-text-box h3 {
    color: var(--primary-light);
    margin-bottom: 1rem;
}

/* ---------- Word Pronunciation Card ---------- */
.word-pron-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.25rem;
    margin-bottom: 0.75rem;
    display: flex;
    align-items: center;
    gap: 1rem;
}
.word-pron-card .word-main {
    font-size: 1.3rem;
    font-weight: 700;
    color: var(--primary-light);
}
.word-pron-card .ipa {
    font-size: 0.95rem;
    color: var(--secondary);
    font-family: monospace;
}
.word-pron-card .simple-ph {
    color: var(--text-secondary);
    font-size: 0.82rem;
}
.word-pron-card .syllables {
    color: var(--accent);
    font-size: 0.78rem;
    font-weight: 600;
}

/* ---------- Vocab Quiz Card ---------- */
.vocab-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.25rem;
    margin-bottom: 1rem;
}
.vocab-word {
    font-size: 1.4rem;
    font-weight: 700;
    color: var(--primary-light);
}
.vocab-phonetic {
    font-family: monospace;
    color: var(--secondary);
    font-size: 0.9rem;
}
.vocab-type {
    display: inline-block;
    background: rgba(245,158,11,0.15);
    color: var(--accent);
    font-size: 0.7rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 4px;
    text-transform: uppercase;
}
.vocab-example {
    color: var(--text-secondary);
    font-size: 0.85rem;
    font-style: italic;
    margin-top: 0.5rem;
    padding-left: 0.75rem;
    border-left: 2px solid var(--border);
}

/* ---------- Sidebar Menu ---------- */
.nav-item {
    padding: 0.6rem 1rem;
    border-radius: 8px;
    margin-bottom: 4px;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    color: var(--text-secondary);
}
.nav-item:hover { background: rgba(108,99,255,0.1); color: var(--text-primary); }
.nav-item.active { background: rgba(108,99,255,0.2); color: var(--primary-light); font-weight: 600; }

/* ---------- Misc ---------- */
.divider {
    height: 1px;
    background: var(--border);
    margin: 1.5rem 0;
}
.tag {
    display: inline-block;
    background: rgba(108,99,255,0.15);
    color: var(--primary-light);
    padding: 3px 10px;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
    margin: 2px;
}

/* ---------- Buttons Override ---------- */
.stButton > button {
    background: linear-gradient(135deg, var(--primary), var(--primary-dark)) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 0.5rem 1.5rem !important;
    transition: all 0.3s ease !important;
}
.stButton > button:hover {
    box-shadow: 0 4px 20px rgba(108,99,255,0.4) !important;
    transform: translateY(-1px) !important;
}
.stButton > button:active {
    transform: translateY(0) !important;
}

/* ---------- Input Override ---------- */
.stTextInput input, .stTextArea textarea, .stSelectbox > div > div {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    color: var(--text-primary) !important;
    border-radius: 8px !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 2px rgba(108,99,255,0.2) !important;
}

/* tabs override */
.stTabs [data-baseweb="tab-list"] {
    gap: 2px;
    background: var(--bg-card);
    border-radius: 10px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
    color: var(--text-secondary);
}
.stTabs [aria-selected="true"] {
    background: var(--primary) !important;
    color: white !important;
}

/* expander */
.streamlit-expanderHeader {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}

/* ---------- Sentence Builder ---------- */
.scrambled-words {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin: 0.75rem 0;
}
.scrambled-word {
    background: rgba(108,99,255,0.15);
    color: var(--primary-light);
    padding: 6px 14px;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.9rem;
}

/* ---------- Fill Blank ---------- */
.blank-sentence {
    background: var(--bg-card);
    padding: 1rem;
    border-radius: 8px;
    border-left: 3px solid var(--accent);
    font-size: 1rem;
    color: var(--text-primary);
    line-height: 1.6;
    margin: 0.5rem 0;
}

/* Progress indicator */
.step-indicator {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 1rem;
}
.step-dot {
    width: 10px; height: 10px;
    border-radius: 50%;
    background: var(--border);
}
.step-dot.active { background: var(--primary); }
.step-dot.done { background: var(--success); }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════ HELPERS ═══════════════════════════

def api_get(path: str):
    """GET request wrapper."""
    try:
        r = requests.get(f"{API_BASE}{path}", timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API Error: {e}")
        return None


def api_post(path: str, data: dict, timeout: int = 120):
    """POST request wrapper."""
    try:
        r = requests.post(f"{API_BASE}{path}", json=data, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.Timeout:
        st.error("Request timed out. The server may be processing a large request. Please try again.")
        return None
    except Exception as e:
        st.error(f"API Error: {e}")
        return None


def play_audio_base64(audio_b64: str, fmt: str = "wav"):
    """Render an audio player from base64 data."""
    if audio_b64:
        audio_bytes = base64.b64decode(audio_b64)
        st.audio(audio_bytes, format=f"audio/{fmt}")


def score_color(score: int) -> str:
    if score >= 80:
        return "#10B981"
    elif score >= 60:
        return "#F59E0B"
    elif score >= 40:
        return "#F97316"
    else:
        return "#EF4444"


def render_score_bar(label: str, score: int):
    color = score_color(score)
    st.markdown(f"""
    <div class="score-row">
        <span class="score-label">{label}</span>
        <div class="score-bar-bg">
            <div class="score-bar-fill" style="width:{score}%; background:{color};"></div>
        </div>
        <span class="score-value" style="color:{color};">{score}</span>
    </div>
    """, unsafe_allow_html=True)


def render_dialogue(dialogue: list, char1: str, char2: str):
    """Render dialogue with speaker bubbles."""
    html = '<div class="dialogue-container">'
    for line in dialogue:
        speaker = line.get("speaker", "")
        text = line.get("text", "")
        cls = "speaker-1" if speaker == char1 else "speaker-2"
        html += f"""
        <div class="dialogue-line">
            <span class="speaker-badge {cls}">{speaker}</span>
            <div class="dialogue-text">{text}</div>
        </div>"""
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def render_mc_questions(questions: list):
    """Render multiple-choice questions."""
    for q in questions:
        qnum = q.get("question_number", "")
        qtext = q.get("question_text", "")
        options = q.get("options", [])
        correct = q.get("correct_answer", "")
        explanation = q.get("explanation", "")

        with st.expander(f"Question {qnum}: {qtext}", expanded=False):
            for opt in options:
                label = opt.get("label", "")
                text = opt.get("text", "")
                is_correct = opt.get("is_correct", False)
                icon = "✅" if is_correct else "⬜"
                st.markdown(f"**{label})** {text} {icon if is_correct else ''}")
            st.markdown(f'<div class="correct-answer">✅ Correct: {correct}</div>', unsafe_allow_html=True)
            if explanation:
                st.markdown(f'<div class="explanation-box">💡 {explanation}</div>', unsafe_allow_html=True)


def render_fill_blank_questions(questions: list, is_listening: bool = False):
    """Render fill-in-the-blank questions."""
    for q in questions:
        qnum = q.get("question_number", "")
        if is_listening:
            sentence = q.get("sentence_with_blanks", "")
            original = q.get("original_sentence", "")
            correct_words = q.get("correct_words", [])
            word_options = q.get("word_options", [])
            with st.expander(f"Question {qnum}", expanded=False):
                st.markdown(f'<div class="blank-sentence">{sentence}</div>', unsafe_allow_html=True)
                if word_options:
                    opts_html = " ".join([f'<span class="tag">{w}</span>' for w in word_options])
                    st.markdown(f"**Options:** {opts_html}", unsafe_allow_html=True)
                correct_str = ", ".join(correct_words) if correct_words else ""
                st.markdown(f'<div class="correct-answer">✅ Answer: {correct_str}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="explanation-box">📝 Original: {original}</div>', unsafe_allow_html=True)
        else:
            sentence = q.get("sentence_with_blank", "")
            correct_word = q.get("correct_word", "")
            complete = q.get("complete_sentence", "")
            explanation = q.get("explanation", "")
            options = q.get("options", [])
            with st.expander(f"Question {qnum}", expanded=False):
                st.markdown(f'<div class="blank-sentence">{sentence}</div>', unsafe_allow_html=True)
                for opt in options:
                    lbl = opt.get("label", "")
                    txt = opt.get("text", "")
                    ic = opt.get("is_correct", False)
                    st.markdown(f"**{lbl})** {txt} {'✅' if ic else ''}")
                st.markdown(f'<div class="correct-answer">✅ Answer: {correct_word}</div>', unsafe_allow_html=True)
                if explanation:
                    st.markdown(f'<div class="explanation-box">💡 {explanation}</div>', unsafe_allow_html=True)


def render_sentence_builder(questions: list):
    """Render sentence-builder questions."""
    for q in questions:
        qnum = q.get("question_number", "")
        scrambled = q.get("scrambled_words", [])
        correct = q.get("correct_sentence", q.get("original_sentence", ""))
        hint = q.get("hint", "")
        with st.expander(f"Question {qnum}", expanded=False):
            words_html = "".join([f'<span class="scrambled-word">{w}</span>' for w in scrambled])
            st.markdown(f'<div class="scrambled-words">{words_html}</div>', unsafe_allow_html=True)
            if hint:
                st.caption(f"💡 Hint: {hint}")
            st.markdown(f'<div class="correct-answer">✅ {correct}</div>', unsafe_allow_html=True)


def render_vocab_quiz(questions: list):
    """Render vocabulary quiz questions with audio."""
    for q in questions:
        word = q.get("english_word", "")
        phonetic = q.get("phonetic", "")
        audio_b64 = q.get("audio_base64", "")
        audio_fmt = q.get("audio_format", "mp3")
        word_type = q.get("word_type", "")
        example = q.get("example_sentence", "")
        correct_meaning = q.get("correct_meaning", "")
        correct_answer = q.get("correct_answer", "")
        options = q.get("options", [])

        with st.expander(f"🔤 {word}", expanded=False):
            c1, c2 = st.columns([2, 1])
            with c1:
                st.markdown(f'<span class="vocab-word">{word}</span> <span class="vocab-phonetic">{phonetic}</span>', unsafe_allow_html=True)
                if word_type:
                    st.markdown(f'<span class="vocab-type">{word_type}</span>', unsafe_allow_html=True)
            with c2:
                if audio_b64:
                    play_audio_base64(audio_b64, audio_fmt)

            for opt in options:
                lbl = opt.get("label", "")
                txt = opt.get("text", "")
                ic = opt.get("is_correct", False)
                st.markdown(f"**{lbl})** {txt} {'✅' if ic else ''}")

            st.markdown(f'<div class="correct-answer">✅ {correct_answer} — {correct_meaning}</div>', unsafe_allow_html=True)
            if example:
                st.markdown(f'<div class="vocab-example">"{example}"</div>', unsafe_allow_html=True)


# ═══════════════════════════ SIDEBAR ═══════════════════════════

with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding:1.5rem 0 1rem;">
        <div style="font-size:2.5rem;">🎓</div>
        <h2 style="margin:0.3rem 0 0; font-size:1.15rem; font-weight:800;
            background:linear-gradient(135deg,#6C63FF,#10B981);
            -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
            English Learning Platform
        </h2>
        <p style="color:#94A3B8; font-size:0.75rem; margin-top:0.2rem;">AI-Powered Language Practice</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    page = st.radio(
        "MODULES",
        [
            "🏠  Home",
            "🎧  Listening",
            "📖  Reading",
            "🗣️  Speaking",
            "✍️  Writing",
            "💬  Practice",
            "📚  Textbook",
        ],
        label_visibility="collapsed",
    )

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    st.markdown("""
    <div style="padding:0.75rem; background:rgba(108,99,255,0.08); border-radius:8px;
        border:1px solid rgba(108,99,255,0.2); margin-top:0.5rem;">
        <p style="color:#94A3B8; font-size:0.72rem; margin:0;">
            <strong style="color:#8B83FF;">💡 Tip:</strong> Make sure the FastAPI server is
            running at <code>127.0.0.1:8000</code> before using the platform.
        </p>
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════ PAGES ═══════════════════════════

# ───────────── HOME ─────────────
if "Home" in page:
    st.markdown("""
    <div class="hero-section">
        <h1>English Learning Platform</h1>
        <p>Master English with AI-powered exercises across all language skills.
           Choose a module from the sidebar to get started.</p>
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(5)
    modules = [
        ("🎧", "Listening", "Generate conversations & comprehension exercises", "#6C63FF"),
        ("📖", "Reading", "Create reading texts with questions & quizzes", "#10B981"),
        ("🗣️", "Speaking", "Practice pronunciation with audio feedback", "#F59E0B"),
        ("✍️", "Writing", "Get AI-powered writing tasks & analysis", "#EF4444"),
        ("💬", "Practice", "Chat with AI partners in real-time", "#3B82F6"),
    ]
    for col, (icon, title, desc, color) in zip(cols, modules):
        with col:
            st.markdown(f"""
            <div class="skill-card" style="border-top:3px solid {color};">
                <div style="font-size:2rem; margin-bottom:0.5rem;">{icon}</div>
                <h3 style="color:{color}; font-size:1rem; margin:0 0 0.4rem;">{title}</h3>
                <p style="color:#94A3B8; font-size:0.78rem; line-height:1.4;">{desc}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Quick API health check
    with st.spinner("Checking API connection..."):
        try:
            r = requests.get("http://127.0.0.1:8000/health", timeout=5)
            if r.status_code == 200:
                st.success("✅ API Server is online and healthy.")
            else:
                st.warning("⚠️ API responded but may have issues.")
        except Exception:
            st.error("❌ Cannot connect to API server. Please start it with: `uvicorn api:app --reload`")


# ───────────── LISTENING ─────────────
elif "Listening" in page:
    st.markdown("""
    <div class="section-header">
        <div class="icon" style="background:rgba(108,99,255,0.15);">🎧</div>
        <div>
            <h2>Listening Practice</h2>
            <p>Generate realistic conversations and comprehension exercises</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🎙️ Conversation Generator", "📝 Exercises"])

    # ── Tab 1: Conversation Generator ──
    with tab1:
        col_left, col_right = st.columns([1, 1])

        with col_left:
            st.markdown("##### Conversation Settings")
            l_topic = st.text_input("Topic", "Ordering food at a restaurant", key="l_topic")
            l_difficulty = st.selectbox("CEFR Level", CEFR_LABELS, index=CEFR_DEFAULT_INDEX, key="l_diff")
            l_length = st.selectbox("Length", ["short", "medium", "long"], index=1, key="l_len")
            l_special = st.text_area("Special Details (optional)", "", key="l_special", height=80)
            l_target_vocab = st.text_input("🎯 Target Vocabulary (comma-separated)", "", key="l_tvocab", help="e.g. reservation, appetizer, vegetarian")
            l_target_grammar = st.text_input("🎯 Target Grammar (comma-separated)", "", key="l_tgrammar", help="e.g. Present Perfect, First Conditional")
            l_grade = st.selectbox("📚 Ders Kitabı Sınıfı", GRADE_LABELS, index=0, key="l_grade", help="Seçilen sınıfın ders kitabından bağlam çekilir")

        with col_right:
            st.markdown("##### Characters & Voices")
            c1, c2 = st.columns(2)
            with c1:
                l_char1 = st.text_input("Character 1", "Alex", key="l_c1")
                l_gender1 = st.selectbox("Gender 1", ["male", "female"], key="l_g1")
                l_voice1 = st.selectbox("Voice 1", ["auto", "male_1", "male_2", "male_3", "male_4", "female_1", "female_2", "female_3", "female_4"], key="l_v1")
            with c2:
                l_char2 = st.text_input("Character 2", "Sarah", key="l_c2")
                l_gender2 = st.selectbox("Gender 2", ["male", "female"], index=1, key="l_g2")
                l_voice2 = st.selectbox("Voice 2", ["auto", "male_1", "male_2", "male_3", "male_4", "female_1", "female_2", "female_3", "female_4"], key="l_v2")

            l_speed = st.slider("Speech Speed", 0.25, 3.0, 1.0, 0.25, key="l_speed", help="1.0 = normal, >1 = slower, <1 = faster")

        col_gen_text, col_gen_audio = st.columns(2)
        with col_gen_text:
            gen_text_only = st.button("📝 Generate Text Only", use_container_width=True, key="l_gen_text")
        with col_gen_audio:
            gen_with_audio = st.button("🎙️ Generate with Audio", use_container_width=True, key="l_gen_audio")

        if gen_text_only or gen_with_audio:
            payload = {
                "topic": l_topic,
                "difficulty": cefr_value(l_difficulty),
                "length": l_length,
                "character1": l_char1,
                "character2": l_char2,
                "gender1": l_gender1,
                "gender2": l_gender2,
            }
            if l_special.strip():
                payload["special_details"] = l_special.strip()
            if l_target_vocab.strip():
                payload["target_vocabulary"] = [v.strip() for v in l_target_vocab.split(",") if v.strip()]
            if l_target_grammar.strip():
                payload["target_grammar"] = [g.strip() for g in l_target_grammar.split(",") if g.strip()]
            l_grade_val = grade_value(l_grade)
            if l_grade_val:
                payload["textbook_grade"] = l_grade_val

            if gen_with_audio:
                if l_voice1 != "auto":
                    payload["voice_id1"] = l_voice1
                if l_voice2 != "auto":
                    payload["voice_id2"] = l_voice2
                payload["speech_speed"] = l_speed
                endpoint = "/listening/generate-conversation-with-audio"
            else:
                endpoint = "/listening/generate-conversation"

            with st.spinner("🔄 Generating conversation..."):
                result = api_post(endpoint, payload)

            if result and result.get("success"):
                st.session_state["listening_result"] = result
                st.session_state["listening_has_audio"] = gen_with_audio
                st.success("✅ Conversation generated!")

        # Display result
        if "listening_result" in st.session_state:
            result = st.session_state["listening_result"]
            dialogue = result.get("dialogue", [])
            char1 = result.get("character1", "")
            char2 = result.get("character2", "")

            st.markdown(f"""
            <div class="stat-row">
                <div class="stat-badge"><div class="value">{len(dialogue)}</div><div class="label">Lines</div></div>
                <div class="stat-badge"><div class="value">{result.get('difficulty','')}</div><div class="label">Level</div></div>
                <div class="stat-badge"><div class="value">{char1}</div><div class="label">Speaker 1</div></div>
                <div class="stat-badge"><div class="value">{char2}</div><div class="label">Speaker 2</div></div>
            </div>
            """, unsafe_allow_html=True)

            render_dialogue(dialogue, char1, char2)

            # Audio players
            if st.session_state.get("listening_has_audio"):
                audio_files = result.get("audio_files", [])
                if audio_files:
                    st.markdown("##### 🔊 Audio Playback")
                    for af in audio_files:
                        speaker = af.get("speaker", "")
                        text = af.get("text", "")
                        audio_data = af.get("audio_data", "")
                        with st.expander(f"🔈 {speaker}: {text[:60]}...", expanded=False):
                            play_audio_base64(audio_data, "wav")

            # Store dialogue for exercises
            dialogue_text = "\n".join([f"{d['speaker']}: {d['text']}" for d in dialogue])
            st.session_state["listening_dialogue_text"] = dialogue_text
            st.session_state["listening_speaker"] = char1

    # ── Tab 2: Exercises ──
    with tab2:
        if "listening_dialogue_text" not in st.session_state:
            st.info("👆 First generate a conversation in the **Conversation Generator** tab.")
        else:
            st.markdown(f"**Using dialogue from:** {st.session_state.get('listening_speaker', '')} & ...")

            ex_col1, ex_col2 = st.columns(2)
            with ex_col1:
                ex_difficulty = st.selectbox("Question CEFR Level", CEFR_LABELS, index=CEFR_DEFAULT_INDEX, key="lex_diff")
                ex_count = st.slider("Number of Questions", 1, 10, 5, key="lex_count")
            with ex_col2:
                ex_speaker = st.text_input("Speaker Focus", st.session_state.get("listening_speaker", ""), key="lex_speaker")
                ex_details = st.text_input("Additional Details (optional)", "", key="lex_details")

            exc1, exc2, exc3, exc4 = st.columns(4)

            base_payload = {
                "dialogue_excerpt": st.session_state["listening_dialogue_text"],
                "speaker": ex_speaker,
                "difficulty": cefr_value(ex_difficulty),
                "question_count": ex_count,
            }
            if ex_details.strip():
                base_payload["additional_details"] = ex_details.strip()

            with exc1:
                if st.button("❓ MC Questions", use_container_width=True, key="lex_mc"):
                    with st.spinner("Generating..."):
                        res = api_post("/listening/generate-mc-questions", base_payload)
                    if res and res.get("success"):
                        st.session_state["lex_mc_result"] = res

            with exc2:
                if st.button("📝 Fill Blank", use_container_width=True, key="lex_fb"):
                    with st.spinner("Generating..."):
                        res = api_post("/listening/generate-fill-blank", base_payload)
                    if res and res.get("success"):
                        st.session_state["lex_fb_result"] = res

            with exc3:
                if st.button("🔨 Sentence Builder", use_container_width=True, key="lex_sb"):
                    with st.spinner("Generating..."):
                        res = api_post("/listening/generate-sentence-builder", base_payload)
                    if res and res.get("success"):
                        st.session_state["lex_sb_result"] = res

            with exc4:
                vq_payload = {**base_payload, "generate_audio": True}
                if st.button("🔤 Vocab Quiz", use_container_width=True, key="lex_vq"):
                    with st.spinner("Generating..."):
                        res = api_post("/listening/generate-vocab-quiz", vq_payload)
                    if res and res.get("success"):
                        st.session_state["lex_vq_result"] = res

            # Render results
            if "lex_mc_result" in st.session_state:
                st.markdown("---")
                st.markdown("##### ❓ Multiple Choice Questions")
                render_mc_questions(st.session_state["lex_mc_result"].get("questions", []))

            if "lex_fb_result" in st.session_state:
                st.markdown("---")
                st.markdown("##### 📝 Fill in the Blank")
                render_fill_blank_questions(st.session_state["lex_fb_result"].get("questions", []), is_listening=True)

            if "lex_sb_result" in st.session_state:
                st.markdown("---")
                st.markdown("##### 🔨 Sentence Builder")
                render_sentence_builder(st.session_state["lex_sb_result"].get("questions", []))

            if "lex_vq_result" in st.session_state:
                st.markdown("---")
                st.markdown("##### 🔤 Vocabulary Quiz")
                render_vocab_quiz(st.session_state["lex_vq_result"].get("questions", []))


# ───────────── READING ─────────────
elif "Reading" in page:
    st.markdown("""
    <div class="section-header">
        <div class="icon" style="background:rgba(16,185,129,0.15);">📖</div>
        <div>
            <h2>Reading Practice</h2>
            <p>Generate reading texts with questions, fill-blanks, and vocabulary quizzes</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📄 Text Generator", "📝 Exercises", "🔤 Vocabulary Quiz"])

    # ── Tab 1: Text Generator ──
    with tab1:
        col_left, col_right = st.columns([1, 1])
        with col_left:
            r_concept = st.text_input("Topic / Concept", "Climate change and its effects", key="r_concept")
            r_content_type = st.selectbox("Content Type", ["article", "story", "email", "letter", "essay", "dialogue", "description", "instructions", "review", "report"], key="r_ctype")
            r_difficulty = st.selectbox("CEFR Level", CEFR_LABELS, index=CEFR_DEFAULT_INDEX, key="r_diff")
            r_length = st.selectbox("Text Length", ["short", "medium", "long", "very_long"], index=1, key="r_len")

        with col_right:
            r_words = st.text_input("Required Words (comma-separated)", "environment, pollution, sustainable", key="r_words")
            r_style = st.selectbox("Writing Style", ["(auto)", "formal", "informal", "neutral", "academic", "conversational", "professional"], key="r_style")
            r_tense = st.selectbox("Tense Preference", ["(auto)", "past", "present", "future", "mixed", "narrative"], key="r_tense")
            r_target_grammar = st.text_input("🎯 Target Grammar (comma-separated)", "", key="r_tgrammar", help="e.g. Passive Voice, Relative Clauses, Conditionals")
            r_grade = st.selectbox("📚 Ders Kitabı Sınıfı", GRADE_LABELS, index=0, key="r_grade", help="Seçilen sınıfın ders kitabından bağlam çekilir")
            r_details = st.text_area("Additional Details (optional)", "", key="r_details", height=80)

        if st.button("📄 Generate Reading Text", use_container_width=True, key="r_gen"):
            words_list = [w.strip() for w in r_words.split(",") if w.strip()]
            payload = {
                "concept": r_concept,
                "content_type": r_content_type,
                "difficulty": cefr_value(r_difficulty),
                "length": r_length,
                "required_words": words_list if words_list else ["example"],
            }
            if r_style != "(auto)":
                payload["writing_style"] = r_style
            if r_tense != "(auto)":
                payload["tense_preference"] = r_tense
            if r_target_grammar.strip():
                payload["target_grammar"] = [g.strip() for g in r_target_grammar.split(",") if g.strip()]
            r_grade_val = grade_value(r_grade)
            if r_grade_val:
                payload["textbook_grade"] = r_grade_val
            if r_details.strip():
                payload["additional_details"] = r_details.strip()

            with st.spinner("🔄 Generating reading text..."):
                result = api_post("/reading/generate-text", payload)

            if result and result.get("success"):
                st.session_state["reading_result"] = result
                st.success("✅ Text generated!")

        # Display result
        if "reading_result" in st.session_state:
            res = st.session_state["reading_result"]
            title = res.get("title", "")
            text = res.get("text", "")
            word_count = res.get("word_count", 0)
            words_used = res.get("required_words_used", [])
            words_missing = res.get("required_words_missing", [])

            st.markdown(f"""
            <div class="stat-row">
                <div class="stat-badge"><div class="value">{word_count}</div><div class="label">Words</div></div>
                <div class="stat-badge"><div class="value">{len(words_used)}</div><div class="label">Words Used</div></div>
                <div class="stat-badge"><div class="value">{res.get('content_type','')}</div><div class="label">Type</div></div>
                <div class="stat-badge"><div class="value">{res.get('difficulty','')}</div><div class="label">Level</div></div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="reading-text-box">
                <h3>📖 {title}</h3>
                <p>{text}</p>
            </div>
            """, unsafe_allow_html=True)

            if words_used:
                used_html = " ".join([f'<span class="tag">{w}</span>' for w in words_used])
                st.markdown(f"**✅ Words Used:** {used_html}", unsafe_allow_html=True)
            if words_missing:
                miss_html = " ".join([f'<span class="tag" style="background:rgba(239,68,68,0.15);color:#FCA5A5;">{w}</span>' for w in words_missing])
                st.markdown(f"**❌ Missing Words:** {miss_html}", unsafe_allow_html=True)

            st.session_state["reading_text_for_exercises"] = text

    # ── Tab 2: Exercises from Reading Text ──
    with tab2:
        if "reading_text_for_exercises" not in st.session_state:
            st.info("👆 First generate a reading text in the **Text Generator** tab.")
        else:
            st.markdown("**Using the generated reading text for exercises.**")

            ecol1, ecol2 = st.columns(2)
            with ecol1:
                re_diff = st.selectbox("Question CEFR Level", CEFR_LABELS, index=CEFR_DEFAULT_INDEX, key="re_diff")
                re_count = st.slider("Number of Questions", 1, 10, 5, key="re_count")
            with ecol2:
                re_kw = st.text_input("Focus Keywords (optional, comma-separated)", "", key="re_kw")
                re_inst = st.text_input("Additional Instructions (optional)", "", key="re_inst")

            rxc1, rxc2, rxc3 = st.columns(3)

            reading_text = st.session_state["reading_text_for_exercises"]
            base_payload_r = {
                "reading_text": reading_text,
                "difficulty": cefr_value(re_diff),
                "question_count": re_count,
            }
            if re_inst.strip():
                base_payload_r["additional_instructions"] = re_inst.strip()

            with rxc1:
                if st.button("❓ MC Questions", use_container_width=True, key="re_mc"):
                    payload = {**base_payload_r}
                    if re_kw.strip():
                        payload["keywords"] = [w.strip() for w in re_kw.split(",") if w.strip()]
                    with st.spinner("Generating..."):
                        res = api_post("/reading/generate-questions", payload)
                    if res and res.get("success"):
                        st.session_state["re_mc_result"] = res

            with rxc2:
                if st.button("📝 Fill Blank", use_container_width=True, key="re_fb"):
                    with st.spinner("Generating..."):
                        res = api_post("/reading/generate-fill-blank", base_payload_r)
                    if res and res.get("success"):
                        st.session_state["re_fb_result"] = res

            with rxc3:
                if st.button("🔨 Sentence Builder", use_container_width=True, key="re_sb"):
                    with st.spinner("Generating..."):
                        res = api_post("/reading/generate-sentence-builder", base_payload_r)
                    if res and res.get("success"):
                        st.session_state["re_sb_result"] = res

            if "re_mc_result" in st.session_state:
                st.markdown("---")
                st.markdown("##### ❓ Multiple Choice Questions")
                render_mc_questions(st.session_state["re_mc_result"].get("questions", []))

            if "re_fb_result" in st.session_state:
                st.markdown("---")
                st.markdown("##### 📝 Fill in the Blank")
                render_fill_blank_questions(st.session_state["re_fb_result"].get("questions", []), is_listening=False)

            if "re_sb_result" in st.session_state:
                st.markdown("---")
                st.markdown("##### 🔨 Sentence Builder")
                render_sentence_builder(st.session_state["re_sb_result"].get("questions", []))

    # ── Tab 3: Vocab Quiz (standalone) ──
    with tab3:
        st.markdown("##### Generate a Vocabulary Quiz")
        vc1, vc2 = st.columns(2)
        with vc1:
            vq_diff = st.selectbox("CEFR Level", CEFR_LABELS, index=CEFR_DEFAULT_INDEX, key="vq_diff")
            vq_count = st.slider("Number of Words", 1, 10, 5, key="vq_count")
            vq_audio = st.checkbox("Generate Audio", value=True, key="vq_audio")
        with vc2:
            vq_words = st.text_input("Specific Words (optional, comma-separated)", "", key="vq_words")
            vq_topic = st.text_input("Topic (optional)", "", key="vq_topic")
            vq_inst = st.text_input("Additional Instructions (optional)", "", key="vq_inst")

        if st.button("🔤 Generate Vocab Quiz", use_container_width=True, key="vq_gen"):
            payload = {
                "difficulty": cefr_value(vq_diff),
                "question_count": vq_count,
                "generate_audio": vq_audio,
            }
            if vq_words.strip():
                payload["word_list"] = [w.strip() for w in vq_words.split(",") if w.strip()]
            if vq_topic.strip():
                payload["topic"] = vq_topic.strip()
            if vq_inst.strip():
                payload["additional_instructions"] = vq_inst.strip()

            with st.spinner("🔄 Generating vocabulary quiz..."):
                res = api_post("/reading/generate-vocab-quiz", payload)
            if res and res.get("success"):
                st.session_state["rvq_result"] = res
                st.success("✅ Vocab quiz generated!")

        if "rvq_result" in st.session_state:
            render_vocab_quiz(st.session_state["rvq_result"].get("questions", []))

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        # Single word quiz
        st.markdown("##### 🔍 Quick Single-Word Quiz")
        sw_col1, sw_col2 = st.columns([3, 1])
        with sw_col1:
            sw_word = st.text_input("Enter a word", "", key="sw_word")
        with sw_col2:
            sw_audio = st.checkbox("Audio", value=True, key="sw_audio")

        if st.button("Look Up", key="sw_gen") and sw_word.strip():
            with st.spinner("Looking up..."):
                res = api_post("/reading/generate-single-word-quiz", {"word": sw_word.strip(), "generate_audio": sw_audio})
            if res and res.get("success"):
                q = res.get("question", res)
                # Render inline
                word = q.get("english_word", sw_word)
                phonetic = q.get("phonetic", "")
                audio_b64 = q.get("audio_base64", "")
                word_type = q.get("word_type", "")
                example = q.get("example_sentence", "")
                correct_meaning = q.get("correct_meaning", "")

                st.markdown(f'<span class="vocab-word">{word}</span> <span class="vocab-phonetic">{phonetic}</span>', unsafe_allow_html=True)
                if word_type:
                    st.markdown(f'<span class="vocab-type">{word_type}</span>', unsafe_allow_html=True)
                if audio_b64:
                    play_audio_base64(audio_b64, q.get("audio_format", "mp3"))

                options = q.get("options", [])
                for opt in options:
                    lbl = opt.get("label", "")
                    txt = opt.get("text", "")
                    ic = opt.get("is_correct", False)
                    st.markdown(f"**{lbl})** {txt} {'✅' if ic else ''}")

                st.markdown(f'<div class="correct-answer">✅ {correct_meaning}</div>', unsafe_allow_html=True)
                if example:
                    st.markdown(f'<div class="vocab-example">"{example}"</div>', unsafe_allow_html=True)


# ───────────── SPEAKING ─────────────
elif "Speaking" in page:
    st.markdown("""
    <div class="section-header">
        <div class="icon" style="background:rgba(245,158,11,0.15);">🗣️</div>
        <div>
            <h2>Speaking Practice</h2>
            <p>Practice word pronunciation with audio, IPA, and phonetics</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    sp_words = st.text_area("Enter words (one per line or comma-separated)", "hello\npronunciation\nbeautiful\nenvironment\nknowledge", height=150, key="sp_words")

    sc1, sc2, sc3 = st.columns(3)
    with sc1:
        sp_difficulty = st.selectbox("CEFR Level", CEFR_LABELS, index=CEFR_DEFAULT_INDEX, key="sp_diff")
    with sc2:
        sp_voice = st.selectbox("Voice", ["female_1", "female_2", "female_3", "female_4", "male_1", "male_2", "male_3", "male_4"], key="sp_voice")
    with sc3:
        sp_speed = st.slider("Speech Speed (0=auto)", 0.0, 2.0, 0.0, 0.1, key="sp_speed", help="Set to 0 for auto speed based on CEFR level")

    if st.button("🔊 Get Pronunciations", use_container_width=True, key="sp_gen"):
        # Parse words
        raw = sp_words.replace(",", "\n")
        words_list = [w.strip() for w in raw.split("\n") if w.strip()]
        if not words_list:
            st.warning("Please enter at least one word.")
        else:
            payload = {
                "words": words_list[:50],
                "difficulty": cefr_value(sp_difficulty),
                "voice_id": sp_voice,
            }
            if sp_speed > 0:
                payload["speech_speed"] = sp_speed
            with st.spinner("🔄 Generating pronunciations..."):
                res = api_post("/speaking/word-pronunciation", payload, timeout=60)
            if res and res.get("success"):
                st.session_state["speaking_result"] = res
                st.success(f"✅ Generated {res.get('total_words', 0)} pronunciations!")

    if "speaking_result" in st.session_state:
        res = st.session_state["speaking_result"]
        words_data = res.get("words", [])

        for wd in words_data:
            word = wd.get("word", "")
            ipa = wd.get("phonetic_ipa", "")
            simple = wd.get("phonetic_simple", "")
            syllables = wd.get("syllable_count", 0)
            stress = wd.get("stress_pattern", "")
            audio_b64 = wd.get("audio_base64", "")

            with st.expander(f"🔤 {word}  —  {ipa}", expanded=False):
                pc1, pc2 = st.columns([2, 1])
                with pc1:
                    example_sent = wd.get("example_sentence", "") or ""
                    usage = wd.get("usage_note", "") or ""
                    cefr = wd.get("cefr_level", "") or ""
                    extra_html = ""
                    if example_sent:
                        extra_html += f'<div class="example-sent" style="margin-top:6px;color:#4CAF50;font-style:italic;">📝 {example_sent}</div>'
                    if usage:
                        extra_html += f'<div class="usage-note" style="margin-top:4px;color:#888;font-size:0.9em;">💡 {usage}</div>'
                    st.markdown(f"""
                    <div class="word-pron-card" style="flex-direction:column; align-items:flex-start;">
                        <div class="word-main">{word} <span style="font-size:0.7em;color:#888;">({cefr})</span></div>
                        <div class="ipa">{ipa}</div>
                        <div class="simple-ph">Simple: {simple}</div>
                        <div class="syllables">Syllables: {syllables} | Stress: {stress}</div>
                        {extra_html}
                    </div>
                    """, unsafe_allow_html=True)
                with pc2:
                    if audio_b64:
                        play_audio_base64(audio_b64, "wav")


# ───────────── WRITING ─────────────
elif "Writing" in page:
    st.markdown("""
    <div class="section-header">
        <div class="icon" style="background:rgba(239,68,68,0.15);">✍️</div>
        <div>
            <h2>Writing Practice</h2>
            <p>Generate writing tasks and get AI-powered analysis with scores</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📋 Task Generator", "📊 Writing Analyzer"])

    # ── Tab 1: Task Generator ──
    with tab1:
        wc1, wc2 = st.columns(2)
        with wc1:
            w_topic = st.text_input("Writing Topic", "Write about your favorite hobby", key="w_topic")
            w_type = st.selectbox("Writing Type", ["(auto)", "email", "essay", "letter", "report", "story", "review", "article", "description"], key="w_type")
            w_difficulty = st.selectbox("CEFR Level", CEFR_LABELS, index=CEFR_DEFAULT_INDEX, key="w_diff")
        with wc2:
            w_tense = st.selectbox("Target Tense", ["(auto)", "past_simple", "past_continuous", "past_perfect", "present_simple", "present_continuous", "present_perfect", "future_simple", "future_continuous", "conditional", "mixed"], key="w_tense")
            w_vocab = st.text_input("Target Vocabulary (optional, comma-separated)", "", key="w_vocab")
            w_grammar = st.text_input("🎯 Target Grammar (optional, comma-separated)", "", key="w_grammar", help="e.g. Passive Voice, Reported Speech, Conditionals")
            w_grade = st.selectbox("📚 Ders Kitabı Sınıfı", GRADE_LABELS, index=0, key="w_grade", help="Seçilen sınıfın ders kitabından bağlam çekilir")
            w_details = st.text_area("Additional Details (optional)", "", key="w_details", height=80)

        if st.button("📋 Generate Task", use_container_width=True, key="w_gen"):
            payload = {
                "topic": w_topic,
                "difficulty": cefr_value(w_difficulty),
            }
            if w_type != "(auto)":
                payload["writing_type"] = w_type
            if w_tense != "(auto)":
                payload["target_tense"] = w_tense
            if w_vocab.strip():
                payload["target_vocabulary"] = [v.strip() for v in w_vocab.split(",") if v.strip()]
            if w_grammar.strip():
                payload["target_grammar"] = [g.strip() for g in w_grammar.split(",") if g.strip()]
            w_grade_val = grade_value(w_grade)
            if w_grade_val:
                payload["textbook_grade"] = w_grade_val
            if w_details.strip():
                payload["additional_details"] = w_details.strip()

            with st.spinner("🔄 Generating writing task..."):
                res = api_post("/writing/generate-task", payload)
            if res and res.get("success"):
                st.session_state["writing_task"] = res.get("task", {})
                st.success("✅ Task generated!")

        if "writing_task" in st.session_state:
            task = st.session_state["writing_task"]
            instruction = task.get("task_instruction", "")
            tips = task.get("tips", [])
            suggested_wc = task.get("suggested_word_count", "")

            st.markdown(f"""
            <div class="skill-card">
                <h4 style="color:var(--primary-light); margin:0 0 0.75rem;">📋 Your Writing Task</h4>
                <p style="color:var(--text-primary); font-size:0.95rem; line-height:1.6;">{instruction}</p>
                <div style="margin-top:0.75rem;">
                    <span class="tag">📝 ~{suggested_wc} words</span>
                    <span class="tag">{task.get('writing_type','')}</span>
                    <span class="tag">{task.get('target_tense','')}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if tips:
                st.markdown("**💡 Tips:**")
                for tip in tips:
                    st.markdown(f"- {tip}")

            # Store for analyzer
            st.session_state["w_task_instruction"] = instruction
            st.session_state["w_task_tense"] = task.get("target_tense", "")
            st.session_state["w_task_vocab"] = task.get("target_vocabulary", [])
            st.session_state["w_task_grammar"] = task.get("target_grammar", [])
            st.session_state["w_task_tips"] = tips

    # ── Tab 2: Writing Analyzer ──
    with tab2:
        st.markdown("##### Submit your writing for analysis")

        a_instruction = st.text_area(
            "Task Instruction",
            st.session_state.get("w_task_instruction", "Write a short essay about your daily routine."),
            key="a_inst",
            height=100,
        )
        a_response = st.text_area("Your Writing", "", key="a_resp", height=250, placeholder="Write your response here...")

        ac1, ac2 = st.columns(2)
        with ac1:
            a_difficulty = st.selectbox("CEFR Level", CEFR_LABELS, index=CEFR_DEFAULT_INDEX, key="a_diff")
            a_tense = st.selectbox("Target Tense", ["(none)", "past_simple", "past_continuous", "past_perfect", "present_simple", "present_continuous", "present_perfect", "future_simple", "future_continuous", "conditional", "mixed"],
                                   index=0, key="a_tense")
        with ac2:
            a_vocab = st.text_input("Target Vocabulary (optional)", "", key="a_vocab")
            a_grammar = st.text_input("🎯 Target Grammar (optional)", "", key="a_grammar", help="e.g. Passive Voice, Reported Speech")
            a_grade = st.selectbox("📚 Ders Kitabı Sınıfı", GRADE_LABELS, index=0, key="a_grade")

        if st.button("📊 Analyze Writing", use_container_width=True, key="a_gen") and a_response.strip():
            payload = {
                "task_instruction": a_instruction,
                "user_response": a_response,
                "difficulty": cefr_value(a_difficulty),
            }
            if a_tense != "(none)":
                payload["target_tense"] = a_tense
            if a_vocab.strip():
                payload["target_vocabulary"] = [v.strip() for v in a_vocab.split(",") if v.strip()]
            if a_grammar.strip():
                payload["target_grammar"] = [g.strip() for g in a_grammar.split(",") if g.strip()]
            a_grade_val = grade_value(a_grade)
            if a_grade_val:
                payload["textbook_grade"] = a_grade_val
            tips_list = st.session_state.get("w_task_tips", [])
            if tips_list:
                payload["tips"] = tips_list

            with st.spinner("🔄 Analyzing your writing..."):
                res = api_post("/writing/analyze", payload, timeout=120)
            if res and res.get("success"):
                st.session_state["writing_analysis"] = res
                st.success("✅ Analysis complete!")

        if "writing_analysis" in st.session_state:
            res = st.session_state["writing_analysis"]
            analysis = res.get("analysis", {})
            scores = analysis.get("scores", {})
            errors = analysis.get("errors", [])
            strengths = analysis.get("strengths", [])
            improvements = analysis.get("areas_for_improvement", [])
            tips_feedback = analysis.get("tips_feedback", [])

            st.markdown(f"""
            <div class="stat-row">
                <div class="stat-badge"><div class="value">{res.get('word_count', 0)}</div><div class="label">Word Count</div></div>
                <div class="stat-badge"><div class="value" style="color:{score_color(scores.get('overall',0))};">{scores.get('overall', 0)}</div><div class="label">Overall Score</div></div>
                <div class="stat-badge"><div class="value">{len(errors)}</div><div class="label">Errors Found</div></div>
            </div>
            """, unsafe_allow_html=True)

            # Score bars
            st.markdown("##### 📊 Detailed Scores")
            for key, label in [("grammar", "Grammar"), ("fluency", "Fluency"), ("vocabulary", "Vocabulary"), ("structure", "Structure"), ("task_completion", "Task Completion")]:
                render_score_bar(label, scores.get(key, 0))

            # Errors
            if errors:
                st.markdown("##### 🔴 Errors")
                for err in errors:
                    err_type = err.get("error_type", "")
                    original = err.get("original_sentence", "")
                    corrected = err.get("corrected_sentence", "")
                    note = err.get("note", "")
                    st.markdown(f"""
                    <div class="error-card">
                        <span class="error-type">{err_type}</span>
                        <div class="original">❌ {original}</div>
                        <div class="corrected">✅ {corrected}</div>
                        <div class="note">💡 {note}</div>
                    </div>
                    """, unsafe_allow_html=True)

            # Strengths & Improvements
            sc1, sc2 = st.columns(2)
            with sc1:
                if strengths:
                    st.markdown("##### 💪 Strengths")
                    for s in strengths:
                        st.markdown(f"✅ {s}")
            with sc2:
                if improvements:
                    st.markdown("##### 📈 Areas for Improvement")
                    for i in improvements:
                        st.markdown(f"🔹 {i}")

            if tips_feedback:
                st.markdown("##### 📌 Tips Feedback")
                for tf in tips_feedback:
                    st.info(tf)


# ───────────── PRACTICE ─────────────
elif "Practice" in page:
    st.markdown("""
    <div class="section-header">
        <div class="icon" style="background:rgba(59,130,246,0.15);">💬</div>
        <div>
            <h2>Conversation Practice</h2>
            <p>Chat with an AI partner to practice your English in real-time</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Initialize session state
    if "practice_session_id" not in st.session_state:
        st.session_state["practice_session_id"] = None
    if "practice_messages" not in st.session_state:
        st.session_state["practice_messages"] = []
    if "practice_done" not in st.session_state:
        st.session_state["practice_done"] = False
    if "practice_step" not in st.session_state:
        st.session_state["practice_step"] = 0
    if "practice_total" not in st.session_state:
        st.session_state["practice_total"] = 0

    # Not started yet — show setup
    if not st.session_state["practice_session_id"]:
        st.markdown("##### 🛠️ Setup Your Conversation")
        pc1, pc2 = st.columns(2)
        with pc1:
            p_name = st.text_input("AI Partner Name", "Sarah", key="p_name")
            p_role = st.text_input("AI Partner Role", "friendly coffee shop barista", key="p_role")
            p_topic = st.text_input("Conversation Topic (optional)", "ordering a cappuccino", key="p_topic")
            p_details = st.text_area("Additional Details (optional)", "", key="p_details", height=80)
        with pc2:
            p_steps = st.slider("Conversation Length (turns)", 3, 30, 10, key="p_steps")
            p_difficulty = st.selectbox("CEFR Level", CEFR_LABELS, index=CEFR_DEFAULT_INDEX, key="p_diff")
            p_gender = st.selectbox("Voice Gender", ["female", "male"], key="p_gender")
            p_voice = st.selectbox("Voice (optional)", ["auto", "male_1", "male_2", "male_3", "male_4", "female_1", "female_2", "female_3", "female_4"], key="p_voice_id")
            p_speed = st.slider("Speech Rate", 0.5, 1.5, 1.0, 0.05, key="p_speed")
            p_tts = st.checkbox("Enable Voice (TTS)", value=True, key="p_tts")

        p_vocab = st.text_input("Vocabulary to Practice (optional, comma-separated)", "", key="p_vocab")
        p_grammar = st.text_input("🎯 Grammar to Practice (optional, comma-separated)", "", key="p_grammar", help="e.g. Present Perfect, First Conditional, Comparatives")
        p_grade = st.selectbox("📚 Ders Kitabı Sınıfı", GRADE_LABELS, index=0, key="p_grade", help="Seçilen sınıfın ders kitabından bağlam çekilir")

        if st.button("🚀 Start Conversation", use_container_width=True, key="p_start"):
            payload = {
                "partner_name": p_name,
                "llm_role": p_role,
                "total_steps": p_steps,
                "difficulty": cefr_value(p_difficulty),
                "voice_gender": p_gender,
                "speech_rate": p_speed,
                "enable_tts": p_tts,
            }
            if p_topic.strip():
                payload["topic"] = p_topic.strip()
            if p_details.strip():
                payload["details"] = p_details.strip()
            if p_voice != "auto":
                payload["voice_id"] = p_voice
            if p_vocab.strip():
                payload["vocabulary"] = [v.strip() for v in p_vocab.split(",") if v.strip()]
            if p_grammar.strip():
                payload["target_grammar"] = [g.strip() for g in p_grammar.split(",") if g.strip()]
            p_grade_val = grade_value(p_grade)
            if p_grade_val:
                payload["textbook_grade"] = p_grade_val

            with st.spinner("🔄 Starting conversation..."):
                res = api_post("/practice/start", payload, timeout=60)

            if res and res.get("session_id"):
                st.session_state["practice_session_id"] = res["session_id"]
                st.session_state["practice_partner"] = res.get("partner_name", p_name)
                st.session_state["practice_total"] = p_steps
                st.session_state["practice_step"] = 0
                st.session_state["practice_done"] = False
                st.session_state["practice_messages"] = [
                    {"role": "ai", "text": res.get("opening_message", ""), "audio": res.get("audio_base64", "")}
                ]
                st.rerun()

    else:
        # Active conversation
        partner = st.session_state.get("practice_partner", "AI")
        total = st.session_state["practice_total"]
        step = st.session_state["practice_step"]
        is_done = st.session_state["practice_done"]

        # Progress bar
        progress = min(step / max(total, 1), 1.0)
        st.progress(progress, text=f"Turn {step}/{total} — {'✅ Completed' if is_done else '🔄 In Progress'}")

        # Display messages
        chat_html = '<div class="chat-container">'
        for msg in st.session_state["practice_messages"]:
            role = msg["role"]
            text = msg["text"]
            if role == "ai":
                chat_html += f"""
                <div class="chat-meta">{partner}</div>
                <div class="chat-bubble ai">{text}</div>"""
            else:
                chat_html += f"""
                <div class="chat-meta" style="text-align:right;">You</div>
                <div class="chat-bubble user">{text}</div>"""
        chat_html += '</div>'
        st.markdown(chat_html, unsafe_allow_html=True)

        # Audio for last AI message
        msgs = st.session_state["practice_messages"]
        if msgs and msgs[-1]["role"] == "ai" and msgs[-1].get("audio"):
            play_audio_base64(msgs[-1]["audio"], "wav")

        # Input
        if not is_done:
            user_input = st.chat_input("Type your message...")
            if user_input:
                # Add user message
                st.session_state["practice_messages"].append({"role": "user", "text": user_input, "audio": ""})

                payload = {
                    "session_id": st.session_state["practice_session_id"],
                    "user_message": user_input,
                }
                with st.spinner(f"💬 {partner} is typing..."):
                    res = api_post("/practice/chat", payload, timeout=60)

                if res:
                    ai_msg = res.get("ai_message", "")
                    audio = res.get("audio_base64", "")
                    st.session_state["practice_messages"].append({"role": "ai", "text": ai_msg, "audio": audio})
                    st.session_state["practice_step"] = res.get("current_step", step + 1)
                    st.session_state["practice_done"] = res.get("is_done", False)
                    st.rerun()
        else:
            st.markdown("""
            <div class="skill-card" style="text-align:center; border-top:3px solid #10B981;">
                <h3 style="color:#10B981; margin:0;">🎉 Conversation Complete!</h3>
                <p style="color:#94A3B8;">Great practice! Start a new session to continue learning.</p>
            </div>
            """, unsafe_allow_html=True)

        # New conversation button
        if st.button("🔄 Start New Conversation", key="p_new"):
            st.session_state["practice_session_id"] = None
            st.session_state["practice_messages"] = []
            st.session_state["practice_done"] = False
            st.session_state["practice_step"] = 0
            st.rerun()


# ───────────── TEXTBOOK ─────────────
elif "Textbook" in page:
    st.markdown("""
    <div class="section-header">
        <div class="icon" style="background:rgba(245,158,11,0.15);">📚</div>
        <div>
            <h2>Ders Kitabı Yönetimi</h2>
            <p>PDF ders kitaplarını yükleyin — AI tüm modüllerde kitap içeriğini kullanır</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab_upload, tab_manage, tab_search = st.tabs(["📤 Kitap Yükle", "📋 Yüklü Kitaplar", "🔍 İçerik Ara"])

    # ── Tab 1: Upload ──
    with tab_upload:
        st.markdown("##### PDF Ders Kitabı Yükle")
        st.markdown("""
        <div style="padding:0.75rem; background:rgba(108,99,255,0.08); border-radius:8px;
            border:1px solid rgba(108,99,255,0.2); margin-bottom:1rem;">
            <p style="color:#94A3B8; font-size:0.8rem; margin:0;">
                <strong style="color:#8B83FF;">ℹ️ Bilgi:</strong> PDF ders kitabını yükleyin.
                Kitap otomatik olarak ünitelere bölünüp vektör veritabanına eklenecek.
                Sonra her modülde sınıf seçerek bu kitabın içeriğinden yararlanabilirsiniz.
            </p>
        </div>
        """, unsafe_allow_html=True)

        tc1, tc2 = st.columns(2)
        with tc1:
            upload_grade_label = st.selectbox(
                "Sınıf Seçin",
                [g for g in GRADE_LABELS if g != "(Yok)"],
                index=3,  # default 5. Sınıf
                key="tb_grade"
            )
        with tc2:
            uploaded_file = st.file_uploader(
                "PDF Dosyası Seçin",
                type=["pdf"],
                key="tb_file",
                help="Sadece PDF formatı desteklenir"
            )

        if st.button("📤 Yükle ve İşle", use_container_width=True, key="tb_upload", disabled=uploaded_file is None):
            if uploaded_file is not None:
                upload_grade_val = grade_value(upload_grade_label)
                with st.spinner(f"📚 PDF işleniyor: {uploaded_file.name} ..."):
                    try:
                        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                        data = {"grade": upload_grade_val}
                        resp = requests.post(f"{API_BASE}/textbook/upload", files=files, data=data, timeout=300)
                        if resp.status_code == 200:
                            res = resp.json()
                            if res.get("success"):
                                st.success(f"✅ {res.get('message', 'Yüklendi!')}")
                                units = res.get("units_detected", [])
                                st.markdown(f"""
                                <div class="stat-row">
                                    <div class="stat-badge"><div class="value">{res.get('total_chunks', 0)}</div><div class="label">Chunk</div></div>
                                    <div class="stat-badge"><div class="value">{len(units)}</div><div class="label">Ünite</div></div>
                                    <div class="stat-badge"><div class="value">{res.get('grade', '')}</div><div class="label">Sınıf</div></div>
                                </div>
                                """, unsafe_allow_html=True)
                                if units:
                                    st.markdown("**Algılanan Üniteler:**")
                                    for u in units:
                                        st.markdown(f"- {u}")
                            else:
                                st.error(f"❌ {res.get('detail', 'Hata oluştu')}")
                        else:
                            detail = resp.json().get("detail", resp.text) if resp.headers.get("content-type", "").startswith("application/json") else resp.text
                            st.error(f"❌ Hata ({resp.status_code}): {detail}")
                    except requests.exceptions.ConnectionError:
                        st.error("❌ API sunucusuna bağlanılamıyor. Lütfen sunucuyu başlatın.")
                    except Exception as e:
                        st.error(f"❌ Hata: {e}")

    # ── Tab 2: Manage ──
    with tab_manage:
        st.markdown("##### Yüklü Ders Kitapları")
        if st.button("🔄 Yenile", key="tb_refresh"):
            pass  # will trigger reload below

        try:
            resp = requests.get(f"{API_BASE}/textbook/list", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                books = data.get("textbooks", [])
                if books:
                    for book in books:
                        with st.expander(f"📕 {book.get('filename', '')} — Sınıf {book.get('grade', '')}", expanded=False):
                            st.markdown(f"""
                            <div class="stat-row">
                                <div class="stat-badge"><div class="value">{book.get('total_chunks', 0)}</div><div class="label">Chunk</div></div>
                                <div class="stat-badge"><div class="value">{book.get('grade', '')}</div><div class="label">Sınıf</div></div>
                                <div class="stat-badge"><div class="value">{len(book.get('units', []))}</div><div class="label">Ünite</div></div>
                            </div>
                            """, unsafe_allow_html=True)
                            units = book.get("units", [])
                            if units:
                                st.markdown("**Üniteler:**")
                                for u in units:
                                    st.markdown(f"- {u}")
                            tid = book.get("textbook_id", "")
                            if st.button(f"🗑️ Sil", key=f"tb_del_{tid}"):
                                try:
                                    del_resp = requests.delete(f"{API_BASE}/textbook/delete/{tid}", timeout=10)
                                    if del_resp.status_code == 200:
                                        st.success("✅ Silindi!")
                                        st.rerun()
                                    else:
                                        st.error("❌ Silinemedi.")
                                except Exception:
                                    st.error("❌ API bağlantı hatası.")
                else:
                    st.info("📭 Henüz yüklenmiş ders kitabı yok. **Kitap Yükle** sekmesinden PDF yükleyin.")
            else:
                st.warning("⚠️ Kitap listesi alınamadı.")
        except requests.exceptions.ConnectionError:
            st.error("❌ API sunucusuna bağlanılamıyor.")
        except Exception as e:
            st.error(f"❌ Hata: {e}")

    # ── Tab 3: Search ──
    with tab_search:
        st.markdown("##### Kitap İçeriğinde Semantik Arama")
        sc1, sc2 = st.columns(2)
        with sc1:
            search_query = st.text_input("Arama Sorgusu", "", key="tb_search_q", placeholder="e.g. daily routines, animals, weather")
            search_grade_label = st.selectbox(
                "Sınıf",
                [g for g in GRADE_LABELS if g != "(Yok)"],
                index=3,
                key="tb_search_grade"
            )
        with sc2:
            search_top_k = st.slider("Sonuç Sayısı", 1, 20, 5, key="tb_search_k")
            search_unit = st.text_input("Ünite Filtresi (opsiyonel)", "", key="tb_search_unit")

        if st.button("🔍 Ara", use_container_width=True, key="tb_search_btn") and search_query.strip():
            search_grade_val = grade_value(search_grade_label)
            payload = {
                "query": search_query.strip(),
                "grade": search_grade_val,
                "top_k": search_top_k,
            }
            if search_unit.strip():
                payload["unit"] = search_unit.strip()

            with st.spinner("🔍 Aranıyor..."):
                res = api_post("/textbook/search", payload, timeout=30)

            if res and res.get("success"):
                results = res.get("results", [])
                st.session_state["tb_search_results"] = results
                if results:
                    st.success(f"✅ {len(results)} sonuç bulundu")
                else:
                    st.info("Sonuç bulunamadı. Farklı bir sorgu veya sınıf deneyin.")

        if "tb_search_results" in st.session_state:
            for i, r in enumerate(st.session_state["tb_search_results"], 1):
                score = r.get("score", 0)
                score_pct = int(score * 100)
                color = "#10B981" if score >= 0.6 else "#F59E0B" if score >= 0.4 else "#94A3B8"
                with st.expander(f"📄 Sonuç {i} — {r.get('unit', 'General')} (Skor: {score_pct}%)", expanded=i<=2):
                    st.markdown(f"""
                    <div class="stat-row">
                        <div class="stat-badge"><div class="value" style="color:{color};">{score_pct}%</div><div class="label">Benzerlik</div></div>
                        <div class="stat-badge"><div class="value">{r.get('grade','')}</div><div class="label">Sınıf</div></div>
                        <div class="stat-badge"><div class="value">{r.get('page', 0)}</div><div class="label">Sayfa</div></div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown(f"**Kaynak:** {r.get('textbook_filename', '')}")
                    st.text_area("İçerik", r.get("text", ""), height=200, key=f"tb_sr_{i}", disabled=True)
