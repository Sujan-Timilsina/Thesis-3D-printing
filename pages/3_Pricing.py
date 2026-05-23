# Pricing page — placeholder
import streamlit as st

# Self-healing: force PagesManager to rescan pages/ on every rerun.
# Without this, adding a new page while Streamlit is running stays invisible
# until the process is fully killed (in-memory page cache is stale).
try:
    from streamlit.source_util import invalidate_pages_cache as _invalidate_pages_cache
    _invalidate_pages_cache()
except Exception:
    pass

from auth import require_login
from styles import inject_global_styles

st.set_page_config(
    page_title="Pricing — 3D Printing Services",
    layout="wide",
    initial_sidebar_state="collapsed"
)

require_login()
inject_global_styles()

# Shared dark-theme layout (mirrors Home.py)
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
    html, body, [class*="stApp"], .main, .stApp {
        background-color: #0a0a0a !important;
        color: #ffffff !important;
    }
    *, html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    .block-container {
        padding-top: 0 !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        max-width: 1280px !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }
    div[data-testid="stMarkdown"] { width: 100%; }

    /* Hide sidebar + collapse control */
    [data-testid="stSidebar"],
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="collapsedControl"],
    [data-testid="stSidebarNav"],
    button[kind="headerNoPadding"] {
        display: none !important;
        visibility: hidden !important;
        width: 0 !important;
    }

    /* Hide Streamlit's auto-generated heading anchor link icons */
    [data-testid="stHeaderActionElements"],
    .stMarkdown a.anchor-link,
    .streamlit-anchor-link,
    .stMarkdown h1 > a[href^="#"],
    .stMarkdown h2 > a[href^="#"],
    .stMarkdown h3 > a[href^="#"] {
        display: none !important;
    }

    /* Header / nav */
    .nav-brand {
        font-size: 1.1rem;
        font-weight: 800;
        letter-spacing: -0.015em;
        color: #ffffff;
        text-decoration: none;
        display: inline-flex;
        align-items: center;
        height: 42px;
        line-height: 1;
    }
    .nav-brand:hover { opacity: 0.85; }
    .nav-brand .accent {
        background: linear-gradient(135deg, #47a3f3, #1e88e4);
        -webkit-background-clip: text;
        background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* Coming-soon hero */
    .coming-soon-wrap {
        min-height: 60vh;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 4rem 1rem 6rem 1rem;
    }
    .coming-soon-eyebrow {
        text-transform: uppercase;
        letter-spacing: 0.14em;
        font-size: 0.8rem;
        font-weight: 700;
        color: #47a3f3;
        margin-bottom: 1rem;
    }
    .coming-soon-title {
        font-size: clamp(2.6rem, 6vw, 4.5rem);
        font-weight: 800;
        letter-spacing: -0.025em;
        line-height: 1.05;
        color: #ffffff;
        margin: 0 0 1rem 0;
    }
    .coming-soon-title .accent {
        background: linear-gradient(135deg, #47a3f3, #1e88e4);
        -webkit-background-clip: text;
        background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .coming-soon-sub {
        font-size: 1.15rem;
        color: #a3a3a3;
        max-width: 38rem;
        line-height: 1.65;
        margin: 0 auto;
    }

    /* Buttons — same look as Home */
    .stButton > button {
        border-radius: 14px !important;
        padding: 0.85rem 1.6rem !important;
        font-weight: 600 !important;
        font-size: 0.98rem !important;
        background: #171717 !important;
        color: #ffffff !important;
        border: 1px solid #262626 !important;
        transition: transform 0.2s, background 0.2s, border-color 0.2s, box-shadow 0.2s !important;
    }
    .stButton > button:hover {
        background: #262626 !important;
        border-color: #404040 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 20px -10px rgba(0,0,0,0.6) !important;
        color: #ffffff !important;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #1e88e4, #0d47a1) !important;
        border: 1px solid #1976d2 !important;
        color: #ffffff !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #47a3f3, #1565c0) !important;
        box-shadow: 0 14px 28px -10px rgba(30,136,228,0.5) !important;
    }

    /* Footer */
    .footer {
        text-align: center;
        color: #737373;
        padding: 3rem 0 2rem 0;
        font-size: 0.88rem;
        border-top: 1px solid #262626;
        margin-top: 2rem;
    }
    .footer p { margin: 0.3rem 0; }
    .footer .footer-brand {
        color: #ffffff;
        font-weight: 700;
        letter-spacing: -0.01em;
        margin-bottom: 0.4rem;
    }
</style>
""", unsafe_allow_html=True)

# ===== Header (matches Home) =====
nav_brand, _nav_gap, nav_a, nav_b, nav_c = st.columns([0.40, 0.04, 0.18, 0.18, 0.20])
with nav_brand:
    st.markdown(
        '<a href="/" target="_self" class="nav-brand">3D Print<span class="accent">.AI</span></a>',
        unsafe_allow_html=True,
    )
with nav_a:
    if st.button("Start Generating", use_container_width=True, key="header_gen"):
        st.switch_page("pages/1_AI_3D_Generation.py")
with nav_b:
    if st.button("Get a Quote", use_container_width=True, key="header_quote"):
        st.switch_page("pages/2_Print_With_Us.py")
with nav_c:
    if st.button("Pricing", type="primary", use_container_width=True, key="header_pricing"):
        st.switch_page("pages/3_Pricing.py")
st.markdown('<div style="border-bottom:1px solid #1f1f1f; margin: 0.25rem 0 0.5rem 0;"></div>', unsafe_allow_html=True)

# ===== Coming Soon hero =====
st.markdown("""
<div class="coming-soon-wrap">
    <div class="coming-soon-eyebrow">Pricing</div>
    <h1 class="coming-soon-title">Coming <span class="accent">Soon</span></h1>
    <p class="coming-soon-sub">
        We're putting the finishing touches on transparent, pay-as-you-print pricing.
        Check back shortly &mdash; in the meantime, generate a model or request a custom quote.
    </p>
</div>
""", unsafe_allow_html=True)

# ===== Footer =====
st.markdown("""
<div class='footer'>
    <p class='footer-brand'>3D Printing Services</p>
    <p>AI-Powered Design &middot; Professional 3D Printing &middot; Fast & Reliable</p>
    <p>Questions? Contact our support team for assistance.</p>
</div>
""", unsafe_allow_html=True)
