"""Shared visual design system for the 3D-printing service pages.

Call ``inject_global_styles()`` once near the top of each page,
right after ``st.set_page_config(...)``. Page-specific CSS can still be
loaded afterwards and will override these defaults where needed.
"""

import streamlit as st


# IMPORTANT: the string MUST start with `<style>` as its very first character.
# If there is a leading newline (or a preceding `<link>` tag), CommonMark
# parses the payload as block-level HTML that terminates at the first blank
# line — everything after the blank line then renders as a plain paragraph,
# which dumps the raw CSS onto the page.
_DESIGN_TOKENS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/*
 * Palette (matches Home.py and the rest of the app)
 *   --slate-900: #0F172A   page accents / hero
 *   --slate-800: #1E293B   dark surface (cards)
 *   --slate-700: #334155   muted dark
 *   --slate-400: #94A3B8   muted text
 *   --slate-100: #F1F5F9   light surface
 *   --slate-50:  #F8FAFC   light primary text on dark
 *   --blue-500:  #3B82F6   primary accent
 *   --indigo-500:#6366F1   secondary accent
 */

*, html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* === Layout === */
.block-container {
    padding-top: 1rem !important;
    padding-left: 2.5rem !important;
    padding-right: 2.5rem !important;
    max-width: 1400px !important;
}

/* === Buttons (default + primary) === */
.stButton > button, .stDownloadButton > button {
    border-radius: 10px !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
    padding: 0.5rem 1.1rem !important;
    transition: transform 0.15s, box-shadow 0.15s, background 0.15s, border-color 0.15s !important;
    border: 1px solid rgba(15,23,42,0.1) !important;
    background: #FFFFFF !important;
    color: #0F172A !important;
    box-shadow: 0 1px 2px rgba(15,23,42,0.04) !important;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(59,130,246,0.12) !important;
    border-color: rgba(59,130,246,0.35) !important;
    color: #0F172A !important;
}
.stButton > button:active, .stDownloadButton > button:active {
    transform: translateY(0) !important;
}
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {
    background: linear-gradient(180deg, #3B82F6 0%, #2563EB 100%) !important;
    color: #FFFFFF !important;
    border: 1px solid #2563EB !important;
    box-shadow: 0 1px 2px rgba(37,99,235,0.2) !important;
}
.stButton > button[kind="primary"]:hover, .stDownloadButton > button[kind="primary"]:hover {
    background: linear-gradient(180deg, #2563EB 0%, #1D4ED8 100%) !important;
    box-shadow: 0 4px 14px rgba(37,99,235,0.3) !important;
    color: #FFFFFF !important;
}
.stButton > button:disabled, .stDownloadButton > button:disabled {
    opacity: 0.5 !important;
    transform: none !important;
}

/* === Selectbox & multiselect === */
div[data-baseweb="select"] > div {
    border-radius: 10px !important;
    border-color: rgba(15,23,42,0.12) !important;
    transition: border-color 0.15s, box-shadow 0.15s !important;
    min-height: 40px !important;
}
div[data-baseweb="select"] > div:hover {
    border-color: rgba(59,130,246,0.4) !important;
}
div[data-baseweb="select"]:focus-within > div {
    border-color: rgba(59,130,246,0.5) !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.08) !important;
}

/* === Text input & number input === */
.stTextInput input, .stNumberInput input {
    border-radius: 10px !important;
    border: 1px solid rgba(15,23,42,0.12) !important;
    padding: 0.55rem 0.9rem !important;
    transition: border-color 0.15s, box-shadow 0.15s !important;
}
.stTextInput input:focus, .stNumberInput input:focus {
    border-color: rgba(59,130,246,0.5) !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.08) !important;
    outline: none !important;
}

/* === Generic text area (chat input has its own dark styling override) === */
div[data-testid="stTextArea"] textarea:not([aria-label="Message"]) {
    border-radius: 10px !important;
    border: 1px solid rgba(15,23,42,0.12) !important;
    padding: 0.7rem 0.9rem !important;
    transition: border-color 0.15s, box-shadow 0.15s !important;
}
div[data-testid="stTextArea"] textarea:not([aria-label="Message"]):focus {
    border-color: rgba(59,130,246,0.5) !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.08) !important;
    outline: none !important;
}

/* === Slider === */
.stSlider [data-baseweb="slider"] > div > div > div {
    background: #3B82F6 !important;
}
.stSlider [role="slider"] {
    background: #3B82F6 !important;
    border: 2px solid #FFFFFF !important;
    box-shadow: 0 1px 4px rgba(15,23,42,0.15) !important;
}

/* === Metric cards === */
[data-testid="stMetric"] {
    background: #1E293B !important;
    padding: 1rem 1.2rem !important;
    border-radius: 12px !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.2) !important;
}
[data-testid="stMetricLabel"] {
    color: #94A3B8 !important;
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
}
[data-testid="stMetricValue"] {
    font-size: 1.45rem !important;
    font-weight: 600 !important;
    color: #F8FAFC !important;
}
[data-testid="stMetricDelta"] {
    font-size: 0.8rem !important;
}

/* === Expander === */
[data-testid="stExpander"] {
    border-radius: 12px !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    background: #1E293B !important;
    overflow: hidden !important;
    margin-bottom: 0.6rem !important;
}
[data-testid="stExpander"] details summary {
    padding: 0.85rem 1rem !important;
    font-weight: 500 !important;
    color: #F8FAFC !important;
    transition: background 0.12s !important;
}
[data-testid="stExpander"] details summary:hover {
    background: rgba(59,130,246,0.08) !important;
}

/* === Alerts (info / success / warning / error) === */
[data-testid="stAlert"], .stAlert {
    border-radius: 12px !important;
    border: 1px solid transparent !important;
    padding: 0.85rem 1rem !important;
}

/* === Dividers === */
hr {
    border: none !important;
    border-top: 1px solid rgba(15,23,42,0.08) !important;
    margin: 1.5rem 0 !important;
}

/* === Tabs === */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.25rem !important;
    border-bottom: 1px solid rgba(15,23,42,0.08) !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px 8px 0 0 !important;
    padding: 0.55rem 1rem !important;
    font-weight: 500 !important;
    color: #64748B !important;
    transition: color 0.15s, background 0.15s !important;
}
.stTabs [data-baseweb="tab"]:hover {
    color: #0F172A !important;
    background: rgba(59,130,246,0.04) !important;
}
.stTabs [aria-selected="true"] {
    background: rgba(59,130,246,0.08) !important;
    color: #2563EB !important;
}

/* === Radio (horizontal) === */
div[data-baseweb="radio"] label {
    font-weight: 500 !important;
}

/* === File uploader (default — chat-page override sits in its own CSS) === */
[data-testid="stFileUploader"]:not(.chat-attach) > section {
    border-radius: 12px !important;
    border: 1px dashed rgba(15,23,42,0.18) !important;
    background: rgba(15,23,42,0.02) !important;
    transition: border-color 0.15s, background 0.15s !important;
}
[data-testid="stFileUploader"]:not(.chat-attach) > section:hover {
    border-color: rgba(59,130,246,0.4) !important;
    background: rgba(59,130,246,0.03) !important;
}

/* === Captions === */
[data-testid="stCaptionContainer"], .stCaption {
    color: #64748B !important;
    font-size: 0.85rem !important;
}

/* === Typography helpers === */
h1, h2, h3, h4 {
    letter-spacing: -0.015em !important;
    color: #F8FAFC !important;
}

/* === Spinner === */
.stSpinner > div {
    border-color: #3B82F6 transparent transparent transparent !important;
}
</style>"""


def inject_global_styles() -> None:
    """Inject the shared design system CSS into the current page."""
    st.markdown(_DESIGN_TOKENS, unsafe_allow_html=True)
