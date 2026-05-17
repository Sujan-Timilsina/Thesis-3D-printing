# Homepage for 3D Printing Services
import streamlit as st
from pathlib import Path
import base64


@st.cache_data
def _load_video_base64(path_str: str) -> str:
    """Load a video file and return a base64-encoded string suitable for a data URI."""
    with open(path_str, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

from auth import require_login
from styles import inject_global_styles

# Page config
st.set_page_config(
    page_title="3D Printing Services",
    layout="wide"
)

require_login()
inject_global_styles()

# Custom CSS
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
    /*
     * Color system — slate family + two adjacent accents
     * --slate-900: #0F172A   page accents / hero
     * --slate-800: #1E293B   card backgrounds
     * --slate-400: #94A3B8   muted text
     * --slate-50:  #F8FAFC   primary text on dark
     * --blue-500:  #3B82F6   primary accent (card 1, feature icons)
     * --indigo-500:#6366F1   secondary accent (card 2)
     */

    *, html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    /* --- Service cards --- */
    .service-card {
        padding: 2.5rem 2rem;
        border-radius: 12px;
        background: #1E293B;
        color: #F8FAFC;
        text-align: left;
        min-height: 280px;
        border: 1px solid rgba(255,255,255,0.06);
        border-top: 3px solid #3B82F6;
        box-shadow: 0 4px 24px rgba(0,0,0,0.18);
        line-height: 1.7;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .service-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 32px rgba(59,130,246,0.18);
    }
    .service-card .service-title {
        font-size: 1.3rem;
        font-weight: 600;
        margin-bottom: 1rem;
        color: #F8FAFC;
    }
    .service-card .service-description {
        font-size: 0.95rem;
        color: #94A3B8;
        line-height: 1.7;
    }
    /* Alt card: same dark surface, indigo accent (adjacent hue to blue — feels related, not random) */
    .service-card-alt {
        background: #1E293B;
        border-top-color: #6366F1;
    }
    .service-card-alt:hover {
        box-shadow: 0 8px 32px rgba(99,102,241,0.18);
    }

    /* --- Feature cards --- */
    .feature-card {
        background: #1E293B;
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 12px;
        padding: 2rem;
        height: 220px;
        box-sizing: border-box;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .feature-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(0,0,0,0.2);
    }
    .feature-icon {
        font-size: 1.6rem;
        margin-bottom: 0.85rem;
        display: block;
        line-height: 1;
    }
    .feature-card h3 {
        font-size: 1.05rem;
        font-weight: 600;
        color: #F8FAFC;
        margin-bottom: 0.6rem;
    }
    .feature-card p {
        font-size: 0.9rem;
        color: #94A3B8;
        line-height: 1.65;
    }

    /* --- Hero fallback (no video) --- */
    .hero-fallback {
        background: #0F172A;
        color: #F8FAFC;
        text-align: center;
        padding: 6rem 2rem;
        border-radius: 0;
        margin: 0 -2.5rem 2rem -2.5rem;
    }
    .hero-fallback h1 {
        font-size: clamp(2rem, 5vw, 3.5rem);
        font-weight: 700;
        letter-spacing: -0.02em;
        margin-bottom: 0.5rem;
    }
    .hero-fallback p {
        font-size: 1.1rem;
        color: #94A3B8;
        max-width: 500px;
        margin: 0 auto;
    }

    .block-container {
        padding-top: 1rem !important;
        padding-left: 2.5rem !important;
        padding-right: 2.5rem !important;
    }

    .section-heading {
        font-size: 1.5rem;
        font-weight: 600;
        color: #F8FAFC;
        text-align: center;
        margin: 2rem 0 1.5rem 0;
        letter-spacing: -0.01em;
    }

    .footer {
        text-align: center;
        color: #64748B;
        padding: 3rem 0 2rem 0;
        font-size: 0.85rem;
        border-top: 1px solid rgba(0,0,0,0.06);
        margin-top: 1rem;
    }
    .footer p { margin: 0.25rem 0; }
</style>
""", unsafe_allow_html=True)

# Sidebar toggle and navigation
if "sidebar_open" not in st.session_state:
    st.session_state.sidebar_open = True

top_cols = st.columns([0.88, 0.12])
with top_cols[1]:
    if st.button("Menu", key="toggle_sidebar"):
        st.session_state.sidebar_open = not st.session_state.sidebar_open

if not st.session_state.sidebar_open:
    st.markdown('<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded" rel="stylesheet"><style>[data-testid="stSidebar"],[data-testid="stSidebarCollapsedControl"],[data-testid="collapsedControl"],[data-testid="stSidebarNav"],header[data-testid="stHeader"],button[kind="headerNoPadding"],.stSidebar,.stSidebarCollapsedControl,#stSidebarCollapsedControl,[class*="SidebarCollapsed"],[class*="collapsedControl"]{display:none!important;visibility:hidden!important;width:0!important;height:0!important;overflow:hidden!important;position:absolute!important;z-index:-1!important;}</style>', unsafe_allow_html=True)
else:
    with st.sidebar:
        if st.button("Home", use_container_width=True, key="nav_home"):
            st.switch_page("Home.py")
        if st.button("AI 3D Generation", use_container_width=True, key="nav_gen"):
            st.switch_page("pages/1_AI_3D_Generation.py")
        if st.button("Print With Us", use_container_width=True, key="nav_print"):
            st.switch_page("pages/2_Print_With_Us.py")

# Featured video section
video_root = Path(r"C:\\Users\\mtigr\\Downloads\\Website video 3D printing.mp4")
if video_root.exists():
    try:
        b64 = _load_video_base64(str(video_root))
        video_html = '''
<div style="position:relative; width:100vw; height:100vh; overflow:hidden; margin:0; padding:0;">
    <video autoplay loop muted playsinline style="position:absolute; top:0; left:0; width:100%; height:100%; object-fit:cover; z-index: 1;">
    <source src="data:video/mp4;base64,{B64}" type="video/mp4">
    Your browser does not support the video tag.
  </video>
    <div class="hero-overlay">
        <div class="hero-overlay-content">
            <p>The Future Of</p>
            <p>3D Printing</p>
            <p>Is Here</p>
        </div>
    </div>
</div>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
<style>
body { margin: 0; padding: 0; }
.hero-overlay *, .hero-overlay {
    font-family: 'Inter', sans-serif !important;
}
.hero-overlay {
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: flex-end;
    text-align: center;
    color: #FFFFFF;
    font-weight: 700;
    letter-spacing: 0.02em;
    z-index: 2;
    background: rgba(0, 0, 0, 0.45);
    padding: 2rem 3rem 2rem 1.5rem;
    backdrop-filter: blur(4px);
}
.hero-overlay-content {
    width: min(40vw, 30rem);
    text-align: left;
}
.hero-overlay p {
    margin: 0;
    font-size: clamp(2.5rem, 6vw, 4.5rem);
    line-height: 1.05;
    letter-spacing: -0.02em;
}
</style>
'''
        st.markdown(video_html.replace('{B64}', b64), unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Unable to load video: {e}")
else:
    # Fallback hero when video is missing
    st.markdown("""
    <div class='hero-fallback'>
        <h1>The Future of 3D Printing</h1>
        <p>AI-powered design and professional printing, all in one place.</p>
    </div>
    """, unsafe_allow_html=True)


# Service cards
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class='service-card'>
        <div class='service-title'>AI 3D Model Generation</div>
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
    st.markdown("""
    <div class='service-card service-card-alt'>
        <div class='service-title'>Professional 3D Printing</div>
        <div class='service-description'>
            Upload your STL file and let our AI recommend optimal materials and print settings
            based on your use case. We handle everything from material selection to final production.
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Get a Quote", type="primary", use_container_width=True, key="print"):
        st.switch_page("pages/2_Print_With_Us.py")

st.markdown("<br>", unsafe_allow_html=True)

# Features section
st.markdown("<div class='section-heading'>Why Choose Us</div>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class='feature-card'>
        <span class='feature-icon'>🧠</span>
        <h3>AI-Powered Design</h3>
        <p>Advanced AI analyzes your requirements and generates optimal designs and print settings automatically.</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class='feature-card'>
        <span class='feature-icon'>⚡</span>
        <h3>Fast Turnaround</h3>
        <p>Automated slicing and print queue management ensures quick processing and delivery of your parts.</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class='feature-card'>
        <span class='feature-icon'>🎯</span>
        <h3>Precision Quality</h3>
        <p>Professional-grade printers and AI-optimized settings guarantee consistent, high-quality results.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# How it works
st.markdown("<div class='section-heading'>How It Works</div>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["3D Model Generation", "Print Service"])

with tab1:
    st.markdown("""
    ### AI 3D Model Generation Process

    1. **Describe Your Idea** \u2014 Provide a text description or upload reference images
    2. **AI Generation** \u2014 Our AI creates custom Python code to generate your 3D model
    3. **Interactive Preview** \u2014 View and interact with your model in 3D
    4. **Refine & Export** \u2014 Make adjustments and download as STL for printing

    Perfect for: Custom parts, prototypes, replacement components, artistic designs
    """)

with tab2:
    st.markdown("""
    ### Professional Print Service Process

    1. **Upload STL** \u2014 Submit your 3D model file
    2. **Describe Use Case** \u2014 Tell us how the part will be used (environment, forces, etc.)
    3. **AI Analysis** \u2014 Our AI recommends optimal material and print parameters
    4. **Automatic Slicing** \u2014 Files are prepared using Bambu Studio CLI
    5. **Production** \u2014 Your part is queued and printed with professional equipment

    Perfect for: Functional parts, mechanical components, end-use products
    """)

# Footer
st.markdown("""
<div class='footer'>
    <p>AI-Powered Design &middot; Professional 3D Printing &middot; Fast & Reliable</p>
    <p>Questions? Contact our support team for assistance.</p>
</div>
""", unsafe_allow_html=True)
