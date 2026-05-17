import streamlit as st
import hashlib

_USERNAME = "tester"
_PASSWORD_HASH = hashlib.sha256("Test123.".encode()).hexdigest()


def require_login():
    """Show a login gate if the user is not authenticated in this session.
    
    - Persists across page refreshes (same browser session).
    - Resets when the browser tab is closed or a new session starts.
    """
    if st.session_state.get("authenticated", False):
        return

    # Inject Inter font + centered card styling
    st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        *, html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        }
        /* Hide all Streamlit chrome */
        [data-testid="stSidebar"],
        [data-testid="stSidebarCollapsedControl"],
        header[data-testid="stHeader"],
        footer { display: none !important; }

        /* Dark full-page background */
        .stApp {
            background: #0a0a0a !important;
        }

        .login-wrapper {
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 80vh;
        }
        .login-card {
            background: #111;
            border: 1px solid #222;
            border-radius: 16px;
            padding: 3rem 2.5rem 2.5rem 2.5rem;
            width: 100%;
            max-width: 420px;
            box-shadow: 0 8px 40px rgba(0,0,0,0.6);
        }
        .login-logo {
            text-align: center;
            margin-bottom: 0.5rem;
        }
        .login-logo span {
            font-size: 2.2rem;
        }
        .login-title {
            text-align: center;
            font-size: 1.5rem;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 0.25rem;
        }
        .login-subtitle {
            text-align: center;
            font-size: 0.9rem;
            color: #888;
            margin-bottom: 2rem;
        }
        /* Style the Streamlit form inputs to match dark theme */
        [data-testid="stTextInput"] input {
            background: #1a1a1a !important;
            border: 1px solid #333 !important;
            border-radius: 8px !important;
            color: #fff !important;
            padding: 0.6rem 0.75rem !important;
        }
        [data-testid="stTextInput"] input:focus {
            border-color: #667eea !important;
            box-shadow: 0 0 0 3px rgba(102,126,234,0.15) !important;
        }
        [data-testid="stTextInput"] label {
            color: #aaa !important;
            font-size: 0.85rem !important;
            font-weight: 500 !important;
        }
        /* Login button */
        button[kind="primaryFormSubmit"],
        [data-testid="stFormSubmitButton"] > button {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            font-size: 1rem !important;
            padding: 0.65rem 1rem !important;
            width: 100% !important;
            cursor: pointer !important;
            transition: opacity 0.2s !important;
        }
        button[kind="primaryFormSubmit"]:hover,
        [data-testid="stFormSubmitButton"] > button:hover {
            opacity: 0.88 !important;
        }
        .error-box {
            background: rgba(239,68,68,0.1);
            border: 1px solid rgba(239,68,68,0.3);
            border-radius: 8px;
            padding: 0.65rem 1rem;
            color: #f87171;
            font-size: 0.875rem;
            text-align: center;
            margin-top: 0.75rem;
        }
    </style>
    """, unsafe_allow_html=True)

    # Centered card via columns
    _, center, _ = st.columns([1, 1.4, 1])
    with center:
        st.markdown("""
        <div class="login-logo"><span>🖨️</span></div>
        <div class="login-title">Welcome Back</div>
        <div class="login-subtitle">Sign in to access the platform</div>
        """, unsafe_allow_html=True)

        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submitted = st.form_submit_button("Sign In", use_container_width=True)

        if submitted:
            pw_hash = hashlib.sha256(password.encode()).hexdigest()
            if username == _USERNAME and pw_hash == _PASSWORD_HASH:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.markdown(
                    '<div class="error-box">Incorrect username or password.</div>',
                    unsafe_allow_html=True,
                )

    st.stop()
