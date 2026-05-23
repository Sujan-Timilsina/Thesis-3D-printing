# Homepage for 3D Printing Services
import streamlit as st

# Self-healing: force PagesManager to rescan pages/ on every rerun.
# Without this, adding a new page while Streamlit is already running stays
# invisible until the process is fully killed (in-memory page cache is stale).
try:
    from streamlit.source_util import invalidate_pages_cache as _invalidate_pages_cache
    _invalidate_pages_cache()
except Exception:
    pass

from auth import require_login
from styles import inject_global_styles

# Page config
st.set_page_config(
    page_title="3D Printing Services",
    layout="wide",
    initial_sidebar_state="collapsed"
)

require_login()
inject_global_styles()

# Inline SVG icons (single-color, currentColor stroke) — used for service & feature cards
ICON_CUBE = """
<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor"
     stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
  <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
  <polyline points="3.27 6.96 12 12.01 20.73 6.96"/>
  <line x1="12" y1="22.08" x2="12" y2="12"/>
</svg>
"""
ICON_PRINTER = """
<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor"
     stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
  <polyline points="6 9 6 2 18 2 18 9"/>
  <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/>
  <rect x="6" y="14" width="12" height="8" rx="1"/>
</svg>
"""
ICON_CPU = """
<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor"
     stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
  <rect x="4" y="4" width="16" height="16" rx="2"/>
  <rect x="9" y="9" width="6" height="6"/>
  <path d="M9 1v3M15 1v3M9 20v3M15 20v3M20 9h3M20 14h3M1 9h3M1 14h3"/>
</svg>
"""
ICON_BOLT = """
<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor"
     stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
  <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
</svg>
"""
ICON_TARGET = """
<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor"
     stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="12" cy="12" r="10"/>
  <circle cx="12" cy="12" r="6"/>
  <circle cx="12" cy="12" r="2"/>
</svg>
"""

# Custom CSS — layout inspired by push-beyond.site
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
    /* ===== Push-Beyond inspired dark theme ===== */
    html, body, [class*="stApp"], .main, .stApp {
        background-color: #0a0a0a !important;
        color: #ffffff !important;
    }
    *, html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    /* Center the block container in the viewport */
    .block-container {
        padding-top: 0 !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        max-width: 1280px !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }
    div[data-testid="stMarkdown"] { width: 100%; }

    /* Hide the sidebar and its toggle entirely on the home page */
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
    .stMarkdown h3 > a[href^="#"],
    .stMarkdown h4 > a[href^="#"],
    .stMarkdown h5 > a[href^="#"],
    .stMarkdown h6 > a[href^="#"] {
        display: none !important;
    }

    /* ===== Header / nav bar ===== */
    .nav-bar {
        padding: 1.5rem 0 0.5rem 0;
        border-bottom: 1px solid #1f1f1f;
        margin-bottom: 0.5rem;
    }
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
    /* Compact nav buttons */
    .nav-bar .stButton > button {
        padding: 0.55rem 1rem !important;
        font-size: 0.88rem !important;
        font-weight: 600 !important;
    }

    /* ===== Hero ===== */
    .hero-spacer { height: 2.5rem; }
    .hero-title {
        font-size: clamp(2.5rem, 6vw, 4.5rem);
        font-weight: 800;
        letter-spacing: -0.025em;
        line-height: 1.05;
        color: #ffffff;
        margin: 0 0 1.25rem 0;
    }
    .hero-title .accent {
        background: linear-gradient(135deg, #47a3f3, #1e88e4);
        -webkit-background-clip: text;
        background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .hero-subtitle {
        font-size: 1.15rem;
        color: #a3a3a3;
        line-height: 1.65;
        max-width: 36rem;
        margin: 0 0 0.5rem 0;
    }

    /* ===== Floating laptop (replaces right-side visual) ===== */
    .laptop-stage {
        display: flex;
        justify-content: center;
        align-items: flex-start;
        padding: 0.5rem 0;
    }
    .laptop {
        position: relative;
        width: 100%;
        max-width: 540px;
        animation: floatSubtle 4s ease-in-out infinite;
        filter: drop-shadow(0 30px 40px rgba(0,0,0,0.55));
    }
    .laptop-bezel {
        background: linear-gradient(145deg, #2a2a2a, #161616);
        border-radius: 14px 14px 4px 4px;
        padding: 14px;
        box-shadow:
            inset 0 0 0 1px rgba(255,255,255,0.05),
            0 1px 0 rgba(255,255,255,0.03);
    }
    .laptop-screen {
        background: #000;
        border-radius: 4px;
        aspect-ratio: 16 / 10;
        width: 100%;
        position: relative;
        box-shadow:
            inset 0 0 0 1px #1a1a1a,
            inset 0 0 60px rgba(71,163,243,0.04);
        overflow: hidden;
    }
    .laptop-bezel::before {
        content: "";
        position: absolute;
        top: 6px;
        left: 50%;
        transform: translateX(-50%);
        width: 6px; height: 6px;
        border-radius: 50%;
        background: #3a3a3a;
        box-shadow: inset 0 0 2px #000;
    }
    .laptop-hinge {
        height: 6px;
        background: linear-gradient(180deg, #1a1a1a, #0a0a0a);
        margin: 0 -1.5%;
        border-radius: 2px;
    }
    .laptop-base {
        height: 16px;
        background: linear-gradient(180deg, #2a2a2a, #161616);
        margin: 0 -6%;
        border-radius: 0 0 16px 16px;
        position: relative;
        box-shadow: 0 8px 14px rgba(0,0,0,0.55);
    }
    .laptop-base::after {
        content: "";
        position: absolute;
        top: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 14%;
        height: 5px;
        background: #0a0a0a;
        border-radius: 0 0 8px 8px;
    }
    @keyframes floatSubtle {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-8px); }
    }

    /* ===== Section scaffolding (force centered headings) ===== */
    .section {
        padding: 4.5rem 0 1rem 0;
        width: 100%;
        text-align: center;
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    @media (min-width: 768px) {
        .section { padding: 6rem 0 1.25rem 0; }
    }
    .section-eyebrow {
        text-transform: uppercase;
        letter-spacing: 0.12em;
        font-size: 0.78rem;
        font-weight: 600;
        color: #47a3f3;
        margin: 0 auto 0.6rem auto;
        text-align: center;
    }
    .section-title {
        font-size: clamp(2rem, 4vw, 3rem);
        font-weight: 800;
        letter-spacing: -0.02em;
        line-height: 1.1;
        color: #ffffff;
        margin: 0 auto 0.6rem auto;
        max-width: 48rem;
        text-align: center;
    }
    .section-title .accent {
        background: linear-gradient(135deg, #47a3f3, #1e88e4);
        -webkit-background-clip: text;
        background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .section-lede {
        color: #a3a3a3;
        font-size: 1.05rem;
        max-width: 42rem;
        margin: 0 auto;
        line-height: 1.65;
        text-align: center;
    }

    /* ===== Service cards ===== */
    .service-card {
        background: #171717;
        border: 1px solid #262626;
        border-radius: 24px;
        padding: 2rem;
        min-height: 240px;
        display: flex;
        flex-direction: column;
        gap: 0.85rem;
        transition: transform 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.3);
        text-align: left;
    }
    .service-card:hover {
        transform: translateY(-4px);
        border-color: #1e88e4;
        box-shadow: 0 20px 40px -15px rgba(30,136,228,0.3);
    }
    .service-card .service-icon {
        width: 52px; height: 52px;
        border-radius: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: rgba(30,136,228,0.10);
        border: 1px solid rgba(30,136,228,0.28);
        color: #47a3f3;
        margin-bottom: 0.5rem;
    }
    .service-card .service-icon svg { display: block; }
    .service-card .service-title {
        font-size: 1.35rem;
        font-weight: 700;
        color: #ffffff;
        letter-spacing: -0.01em;
    }
    .service-card .service-description {
        font-size: 0.97rem;
        color: #a3a3a3;
        line-height: 1.65;
    }
    .service-card-alt .service-icon {
        background: rgba(99,102,241,0.10);
        border-color: rgba(99,102,241,0.32);
        color: #8b8df0;
    }
    .service-card-alt:hover {
        border-color: #6366f1;
        box-shadow: 0 20px 40px -15px rgba(99,102,241,0.3);
    }

    /* ===== Feature cards (3-up grid) ===== */
    .feature-card {
        background: #171717;
        border: 1px solid #262626;
        border-radius: 20px;
        padding: 1.75rem;
        height: 100%;
        transition: transform 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease;
        text-align: left;
    }
    .feature-card:hover {
        transform: translateY(-3px);
        border-color: #1e88e4;
        box-shadow: 0 14px 30px -12px rgba(30,136,228,0.25);
    }
    .feature-icon {
        width: 44px; height: 44px;
        border-radius: 12px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        background: rgba(30,136,228,0.10);
        border: 1px solid rgba(30,136,228,0.25);
        color: #47a3f3;
        margin-bottom: 1rem;
    }
    .feature-card h3 {
        font-size: 1.1rem;
        font-weight: 700;
        color: #ffffff !important;
        margin: 0 0 0.5rem 0;
        letter-spacing: -0.01em;
    }
    .feature-card p {
        font-size: 0.92rem;
        color: #a3a3a3;
        line-height: 1.65;
        margin: 0;
    }

    /* ===== CTA band ===== */
    .cta-band {
        width: 100%;
        margin: 4rem 0 2rem 0;
        padding: 3.5rem 2rem;
        border-radius: 28px;
        background: linear-gradient(135deg, #1976d2, #0d47a1);
        text-align: center;
        position: relative;
        overflow: hidden;
        border: 1px solid rgba(255,255,255,0.08);
    }
    .cta-band::before {
        content: "";
        position: absolute;
        inset: -40% -10% auto auto;
        width: 360px; height: 360px;
        background: radial-gradient(closest-side, rgba(71,163,243,0.35), transparent 70%);
        filter: blur(40px);
        pointer-events: none;
    }
    .cta-band h2 {
        font-size: clamp(1.8rem, 4vw, 2.6rem);
        font-weight: 800;
        color: #ffffff;
        letter-spacing: -0.02em;
        margin: 0 0 0.6rem 0;
    }
    .cta-band p {
        color: rgba(255,255,255,0.85);
        font-size: 1.05rem;
        max-width: 38rem;
        margin: 0 auto 1.75rem auto;
        line-height: 1.6;
    }

    /* ===== Phase framework + tips (How It Works) ===== */
    .phase-eyebrow {
        color: #47a3f3;
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        margin: 1.5rem 0 0.15rem 0;
    }
    .phase-heading {
        color: #ffffff !important;
        font-size: 1.05rem;
        font-weight: 700;
        letter-spacing: -0.01em;
        margin: 0 0 0.85rem 0;
    }
    .phase-grid {
        display: grid;
        grid-template-columns: 1fr;
        gap: 0.6rem;
        margin: 0 0 1rem 0;
    }
    @media (min-width: 768px) {
        .phase-grid { grid-template-columns: 1fr 1fr; gap: 0.7rem; }
    }
    .phase-card {
        background: #171717;
        border: 1px solid #262626;
        border-radius: 12px;
        padding: 0.75rem 0.95rem;
        display: flex;
        align-items: flex-start;
        gap: 0.75rem;
        transition: border-color 0.2s ease;
    }
    .phase-card:hover { border-color: #1e88e4; }
    .phase-card .phase-num {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 24px;
        height: 24px;
        border-radius: 7px;
        background: linear-gradient(135deg, #1e88e4, #0d47a1);
        color: #ffffff;
        font-weight: 800;
        font-size: 0.78rem;
        flex-shrink: 0;
        margin-top: 1px;
    }
    .phase-card .phase-body { flex: 1; min-width: 0; }
    .phase-card h4 {
        color: #ffffff !important;
        font-size: 0.93rem;
        font-weight: 700;
        letter-spacing: -0.01em;
        margin: 0 0 0.15rem 0;
    }
    .phase-card p {
        color: #a3a3a3;
        font-size: 0.83rem;
        line-height: 1.5;
        margin: 0;
    }

    .tips-card {
        background: linear-gradient(135deg, rgba(30,136,228,0.06), rgba(13,71,161,0.06));
        border: 1px solid rgba(30,136,228,0.25);
        border-radius: 18px;
        padding: 1.4rem 1.5rem;
        margin: 1.25rem 0 0.75rem 0;
    }
    .tips-card .tips-title {
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        font-weight: 700;
        color: #47a3f3;
        margin: 0 0 0.85rem 0;
    }
    .tips-card ul {
        list-style: none;
        padding: 0;
        margin: 0;
    }
    .tips-card li {
        display: flex;
        align-items: flex-start;
        gap: 0.65rem;
        padding: 0.35rem 0;
        color: #d4d4d4;
        font-size: 0.95rem;
        line-height: 1.55;
    }
    .tips-card li::before {
        content: "→";
        color: #47a3f3;
        font-weight: 700;
        flex-shrink: 0;
        margin-top: 1px;
    }
    .tips-card li strong {
        color: #ffffff;
        font-weight: 600;
    }

    .disclaimer {
        display: block;
        width: 100%;
        max-width: 60rem;
        margin: 1.25rem auto 0 auto;
        padding: 0 1rem;
        box-sizing: border-box;
        color: #737373 !important;
        font-size: 0.82rem;
        font-style: italic;
        line-height: 1.6;
        text-align: center;
    }

    /* ===== Tabs (How It Works) — dark themed ===== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem !important;
        border-bottom: 1px solid #262626 !important;
        justify-content: center;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        color: #a3a3a3 !important;
        border-radius: 10px 10px 0 0 !important;
        padding: 0.7rem 1.2rem !important;
        font-weight: 600 !important;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(30,136,228,0.08) !important;
        color: #ffffff !important;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(30,136,228,0.15) !important;
        color: #47a3f3 !important;
    }
    .stTabs [data-baseweb="tab-panel"] {
        color: #d4d4d4 !important;
        padding-top: 1.5rem !important;
    }
    .stTabs [data-baseweb="tab-panel"] h3 {
        color: #ffffff !important;
        font-weight: 700;
        letter-spacing: -0.01em;
    }

    /* Streamlit buttons */
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

    /* ===== Footer ===== */
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

# ===== Header / nav bar =====
st.markdown('<div class="nav-bar-anchor"></div>', unsafe_allow_html=True)
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
    if st.button("Pricing", use_container_width=True, key="header_pricing"):
        st.switch_page("pages/3_Pricing.py")
st.markdown('<div style="border-bottom:1px solid #1f1f1f; margin: 0.25rem 0 0.5rem 0;"></div>', unsafe_allow_html=True)

# ===== Hero section — title (left) and floating laptop (right) =====
st.markdown('<div class="hero-spacer"></div>', unsafe_allow_html=True)
hero_text_col, hero_visual_col = st.columns([1.05, 0.95], gap="large", vertical_alignment="top")

with hero_text_col:
    st.markdown("""
    <h1 class="hero-title">From Idea to <span class="accent">3D Model</span>, in Seconds</h1>
    <p class="hero-subtitle">
        Describe what you need in plain language and our AI builds a print-ready
        3D model &mdash; no CAD experience required. Refine it, export the STL,
        or send it straight to our printers.
    </p>
    """, unsafe_allow_html=True)

    cta_l, cta_r, _spacer = st.columns([1, 1, 0.6])
    with cta_l:
        if st.button("Start Generating", type="primary", use_container_width=True, key="hero_gen"):
            st.switch_page("pages/1_AI_3D_Generation.py")
    with cta_r:
        if st.button("Get a Quote", use_container_width=True, key="hero_print"):
            st.switch_page("pages/2_Print_With_Us.py")

with hero_visual_col:
    st.markdown("""
    <div class="laptop-stage">
        <div class="laptop">
            <div class="laptop-bezel">
                <div class="laptop-screen"></div>
            </div>
            <div class="laptop-hinge"></div>
            <div class="laptop-base"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ===== Services section =====
st.markdown("""
<div class="section">
    <div class="section-eyebrow">Our Services</div>
    <h2 class="section-title">Two ways to bring your <span class="accent">ideas to life</span></h2>
    <p class="section-lede">
        Generate custom 3D models from a prompt, or upload your own STL and let us print it
        with AI-recommended materials and settings.
    </p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown(f"""
    <div class='service-card'>
        <div class='service-icon'>{ICON_CUBE}</div>
        <div class='service-title'>3D Model Generation</div>
        <div class='service-description'>
            Transform your ideas into 3D models using our AI-powered generation tool.
            Describe what you need or upload reference images, and our AI will create
            custom code for your model.
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Start Generating", type="primary", use_container_width=True, key="gen"):
        st.switch_page("pages/1_AI_3D_Generation.py")

with col2:
    st.markdown(f"""
    <div class='service-card service-card-alt'>
        <div class='service-icon'>{ICON_PRINTER}</div>
        <div class='service-title'>3D Printing</div>
        <div class='service-description'>
            Upload your STL file and let our AI recommend optimal materials and print settings
            based on your use case. We handle everything from material selection to final production.
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Get a Quote", type="primary", use_container_width=True, key="print"):
        st.switch_page("pages/2_Print_With_Us.py")

# ===== Features section =====
st.markdown("""
<div class="section">
    <div class="section-eyebrow">Why Choose Us</div>
    <h2 class="section-title">Everything you need to <span class="accent">crush your prints</span></h2>
    <p class="section-lede">
        Smart design, fast production, and reliable quality — built into every step of the workflow.
    </p>
</div>
""", unsafe_allow_html=True)

fcol1, fcol2, fcol3 = st.columns(3, gap="large")

with fcol1:
    st.markdown(f"""
    <div class='feature-card'>
        <span class='feature-icon'>{ICON_CPU}</span>
        <h3>AI-Powered Design</h3>
        <p>Advanced AI analyzes your requirements and generates optimal designs and print settings automatically.</p>
    </div>
    """, unsafe_allow_html=True)

with fcol2:
    st.markdown(f"""
    <div class='feature-card'>
        <span class='feature-icon'>{ICON_BOLT}</span>
        <h3>Fast Turnaround</h3>
        <p>Automated slicing and print queue management ensures quick processing and delivery of your parts.</p>
    </div>
    """, unsafe_allow_html=True)

with fcol3:
    st.markdown(f"""
    <div class='feature-card'>
        <span class='feature-icon'>{ICON_TARGET}</span>
        <h3>Precision Quality</h3>
        <p>Professional-grade printers and AI-optimized settings guarantee consistent, high-quality results.</p>
    </div>
    """, unsafe_allow_html=True)

# ===== How it works =====
st.markdown("""
<div class="section">
    <div class="section-eyebrow">How It Works</div>
    <h2 class="section-title">From idea to <span class="accent">finished part</span></h2>
</div>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["3D Model Generation", "Print Service"])

with tab1:
    st.markdown("""
    ### AI 3D Model Generation Process

    1. **Describe Your Idea** &mdash; Provide a text description or upload reference images
    2. **AI Generation** &mdash; Our AI creates custom Python code to generate your 3D model
    3. **Interactive Preview** &mdash; View and interact with your model in 3D
    4. **Refine & Export** &mdash; Make adjustments and download as STL for printing

    Perfect for: Custom parts, prototypes, replacement components, artistic designs

    <div class="phase-eyebrow">Behind the scenes</div>
    <div class="phase-heading">The AI's 4-phase framework</div>
    <div class="phase-grid">
        <div class="phase-card">
            <div class="phase-num">1</div>
            <div class="phase-body">
                <h4>Analyse</h4>
                <p>Reads your description and images, identifies the geometry, and asks clarifying questions.</p>
            </div>
        </div>
        <div class="phase-card">
            <div class="phase-num">2</div>
            <div class="phase-body">
                <h4>Confirm</h4>
                <p>Restates its understanding back to you and waits for approval before generating anything.</p>
            </div>
        </div>
        <div class="phase-card">
            <div class="phase-num">3</div>
            <div class="phase-body">
                <h4>Plan</h4>
                <p>Drafts a step-by-step build strategy &mdash; primitives, operations, and order &mdash; with consistency checks.</p>
            </div>
        </div>
        <div class="phase-card">
            <div class="phase-num">4</div>
            <div class="phase-body">
                <h4>Code</h4>
                <p>Writes parametric CadQuery code, executes it live, and renders the result in the 3D preview.</p>
            </div>
        </div>
    </div>

    <div class="tips-card">
        <div class="tips-title">Tips for best results</div>
        <ul>
            <li><strong>Be as detailed as possible</strong> &mdash; describe the part's shape, purpose, and how it'll be used.</li>
            <li><strong>Give all the dimensions</strong> &mdash; width, height, depth, hole diameters, wall thickness, and tolerances.</li>
            <li><strong>Attach images or sketches</strong> &mdash; a quick hand-drawn sketch or reference photo dramatically improves accuracy.</li>
            <li><strong>Always double-check the AI's interpretation</strong> &mdash; read the Confirm phase carefully before approving the plan.</li>
        </ul>
    </div>

    <div class="disclaimer">
        Disclaimer: we don't guarantee geometric accuracy or fitness for any specific purpose.
        AI-generated models should be verified by the user before printing or production &mdash;
        final responsibility for correctness rests with you.
    </div>
    """, unsafe_allow_html=True)

with tab2:
    st.markdown("""
    ### Professional Print Service Process

    1. **Upload STL** — Submit your 3D model file
    2. **Describe Use Case** — Tell us how the part will be used (environment, forces, etc.)
    3. **AI Analysis** — Our AI recommends optimal material and print parameters
    4. **Automatic Slicing** — Files are prepared using Bambu Studio CLI
    5. **Production** — Your part is queued and printed with professional equipment

    Perfect for: Functional parts, mechanical components, end-use products
    """)

# ===== CTA band =====
st.markdown("""
<div class="cta-band">
    <h2>Ready to bring your designs to life?</h2>
    <p>Get started in minutes — generate a model with AI or send us your STL for professional printing.</p>
</div>
""", unsafe_allow_html=True)

# Centered bottom CTA buttons
_lpad, cbtn1, cbtn2, _rpad = st.columns([1, 1, 1, 1])
with cbtn1:
    if st.button("Start Generating", type="primary", use_container_width=True, key="cta_gen"):
        st.switch_page("pages/1_AI_3D_Generation.py")
with cbtn2:
    if st.button("Get a Quote", use_container_width=True, key="cta_print"):
        st.switch_page("pages/2_Print_With_Us.py")

# ===== Footer =====
st.markdown("""
<div class='footer'>
    <p class='footer-brand'>3D Printing Services</p>
    <p>AI-Powered Design &middot; Professional 3D Printing &middot; Fast & Reliable</p>
    <p>Questions? Contact our support team for assistance.</p>
</div>
""", unsafe_allow_html=True)
