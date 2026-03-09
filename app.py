"""
app.py — Verité Research Chatbot UI
Professional dark-accented design with branded header, hero section,
source citation cards, and meaningful session names in sidebar.
"""

import streamlit as st
import base64
from pathlib import Path
from agent import VeriteAgent
from config import GROQ_API_KEY


def _load_logo_b64() -> str:
    """Load logo.jpg as base64 string for embedding in HTML."""
    logo_path = Path("logo.jpg")
    if logo_path.exists():
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title  = "Veri — Verité Research Assistant",
    page_icon   = "📚",
    layout      = "wide",
    initial_sidebar_state = "expanded",
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* ── Global ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* hide only streamlit footer and main menu, NOT header (needed for sidebar toggle) */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    /* make sidebar toggle button more visible */
    [data-testid="collapsedControl"] {
        display: block !important;
        visibility: visible !important;
        background: #1a5276 !important;
        border-radius: 0 8px 8px 0 !important;
    }

    /* ── Branded top banner ── */
    .top-banner {
        background: linear-gradient(135deg, #1a3a5c 0%, #1a5276 60%, #2471a3 100%);
        border-radius: 16px;
        padding: 32px 40px;
        margin-bottom: 24px;
        display: flex;
        align-items: center;
        gap: 24px;
        box-shadow: 0 4px 20px rgba(26,82,118,0.25);
    }
    .banner-text h1 {
        color: white;
        font-size: 2rem;
        font-weight: 700;
        margin: 0 0 6px 0;
    }
    .banner-text p {
        color: rgba(255,255,255,0.80);
        font-size: 0.95rem;
        margin: 0;
    }
    .banner-logo {
        background: white;
        border-radius: 12px;
        padding: 10px 16px;
        display: flex;
        align-items: center;
    }

    /* ── Topic pills ── */
    .pills-row {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin-bottom: 24px;
    }
    .pill {
        background: #eaf2fb;
        color: #1a5276;
        border: 1px solid #aed6f1;
        border-radius: 20px;
        padding: 4px 14px;
        font-size: 0.8rem;
        font-weight: 500;
    }

    /* ── Chat messages ── */
    .stChatMessage {
        border-radius: 12px !important;
        margin-bottom: 8px !important;
    }

    /* ── Search badge ── */
    .badge-search {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        background: #eaf2fb;
        color: #1a5276;
        border: 1px solid #aed6f1;
        padding: 3px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 500;
        margin-bottom: 8px;
    }

    /* ── Source card ── */
    .source-card {
        background: #f4f8fd;
        border-left: 4px solid #2471a3;
        border-radius: 0 10px 10px 0;
        padding: 12px 16px;
        margin: 6px 0;
        font-size: 0.83rem;
        line-height: 1.6;
        color: #2c3e50;
    }
    .source-card .src-title {
        font-weight: 600;
        color: #1a5276;
        font-size: 0.85rem;
        margin-bottom: 4px;
    }
    .source-card .src-page {
        display: inline-block;
        background: #1a5276;
        color: white;
        border-radius: 4px;
        padding: 1px 7px;
        font-size: 0.72rem;
        margin-bottom: 8px;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: #f0f4f8 !important;
        border-right: 1px solid #d5e8f3;
    }
    .sidebar-title {
        font-size: 0.7rem;
        font-weight: 700;
        color: #7f8c9a;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin: 16px 0 8px 0;
    }
    .session-label-current {
        background: #1a5276;
        color: white;
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 0.82rem;
        font-weight: 500;
        margin: 3px 0;
    }
    .session-label {
        background: white;
        color: #2c3e50;
        border: 1px solid #d5e8f3;
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 0.82rem;
        margin: 3px 0;
    }
    .status-dot-green { color: #27ae60; font-size: 0.78rem; }
    .status-dot-red   { color: #e74c3c; font-size: 0.78rem; }

    /* ── Welcome card (empty state) ── */
    .welcome-card {
        background: white;
        border: 1px solid #d5e8f3;
        border-radius: 16px;
        padding: 32px;
        text-align: center;
        max-width: 640px;
        margin: 40px auto;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    }
    .welcome-card h3 { color: #1a5276; margin-bottom: 12px; }
    .welcome-card p  { color: #5d6d7e; font-size: 0.9rem; }
    .sample-q {
        background: #eaf2fb;
        border-radius: 8px;
        padding: 8px 14px;
        margin: 6px 0;
        font-size: 0.85rem;
        color: #1a5276;
        cursor: pointer;
        text-align: left;
    }
</style>
""", unsafe_allow_html=True)


# ── Agent singleton ────────────────────────────────────────────────────────────

@st.cache_resource(show_spinner="Loading Verité knowledge base...")
def get_agent() -> VeriteAgent:
    return VeriteAgent()


# ── Session state ──────────────────────────────────────────────────────────────

def init_session() -> None:
    agent = get_agent()
    if "session_id" not in st.session_state:
        session_id, history = agent.start_session()
        st.session_state.session_id           = session_id
        st.session_state.conversation_history = history
        st.session_state.display_messages     = []
    if "input_key" not in st.session_state:
        st.session_state.input_key = 0


# ── Sidebar ────────────────────────────────────────────────────────────────────

def render_sidebar() -> None:
    agent = get_agent()

    with st.sidebar:
        # Logo
        st.markdown("<div style='padding:12px 0 4px 0'>", unsafe_allow_html=True)
        try:
            st.image("logo.jpg", use_container_width=True)
        except Exception:
            st.markdown("### 📚 Veri")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("---")

        # New session button
        if st.button("＋  New Conversation", use_container_width=True, type="primary"):
            session_id, history = agent.start_session()
            st.session_state.session_id           = session_id
            st.session_state.conversation_history = history
            st.session_state.display_messages     = []
            st.rerun()

        # Past sessions
        st.markdown('<div class="sidebar-title">Conversation History</div>', unsafe_allow_html=True)
        past = [s for s in agent.memory.list_sessions(limit=15) if s["message_count"] > 0]

        for s in past:
            sid   = s["session_id"]
            label = s.get("user_label") or "New conversation"
            count = s["message_count"]
            # Format date nicely
            try:
                from datetime import datetime
                dt   = datetime.fromisoformat(s["created_at"])
                date = dt.strftime("%b %d, %H:%M")
            except Exception:
                date = ""

            display = f"{label}"
            subtitle = f"{count} messages  •  {date}"

            if sid == st.session_state.session_id:
                st.markdown(
                    f'<div class="session-label-current">'
                    f'<div style="font-weight:600">▶ {display}</div>'
                    f'<div style="opacity:0.75;font-size:0.72rem;margin-top:2px">{subtitle}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            else:
                if st.button(
                    display,
                    key        = f"load_{sid}",
                    help       = subtitle,
                    use_container_width = True,
                ):
                    msgs = agent.memory.load_session_messages(sid)
                    st.session_state.conversation_history = msgs
                    st.session_state.session_id           = sid
                    st.session_state.display_messages     = [
                        (m["role"], m["content"], [], None) for m in msgs
                    ]
                    st.rerun()

        st.markdown("---")

        # KB status
        if agent.is_ready():
            st.markdown('<span class="status-dot-green">● Knowledge base ready</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-dot-red">● Knowledge base empty</span>', unsafe_allow_html=True)

        st.markdown(
            "<div style='font-size:0.72rem;color:#7f8c9a;margin-top:12px;line-height:1.5'>"
            "Veri is an AI assistant for Verité Research. "
            "Answers are based on Verité's publications only."
            "</div>",
            unsafe_allow_html=True,
        )


# ── Header banner ──────────────────────────────────────────────────────────────

def render_header() -> None:
    logo_b64 = _load_logo_b64()
    logo_html = (
        f'<img src="data:image/jpeg;base64,{logo_b64}" '
        f'style="height:48px;object-fit:contain;"/>'
        if logo_b64
        else '<span style="font-size:2rem">📚</span>'
    )

    st.markdown(f"""
    <div class="top-banner">
        <div class="banner-logo">
            {logo_html}
        </div>
        <div class="banner-text">
            <h1>Veri — Research Assistant</h1>
            <p>Your AI guide to Verité Research's publications on Sri Lanka's economy,
               governance, capital markets, and labour rights.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Topic pills
    st.markdown("""
    <div class="pills-row">
        <span class="pill">🏛 Governance</span>
        <span class="pill">📈 Capital Markets</span>
        <span class="pill">⚖️ Labour Rights</span>
        <span class="pill">💰 Fiscal Policy</span>
        <span class="pill">🌿 Trade & Investment</span>
        <span class="pill">🏦 Financial Markets</span>
    </div>
    """, unsafe_allow_html=True)


# ── Welcome (empty state) ──────────────────────────────────────────────────────

def render_welcome() -> None:
    st.markdown("""
    <div class="welcome-card">
        <h3>👋 Welcome! I'm Veri</h3>
        <p>I can answer questions about Verité Research's publications.
           Try one of these to get started:</p>
        <div class="sample-q">💬 What does Verité say about property taxes in Sri Lanka?</div>
        <div class="sample-q">💬 What are governance-linked bonds?</div>
        <div class="sample-q">💬 Explain the findings on trade facilitation and forest permits.</div>
        <div class="sample-q">💬 What is forced labour?</div>
    </div>
    """, unsafe_allow_html=True)


# ── Chat rendering ─────────────────────────────────────────────────────────────

def render_chat() -> None:
    for role, text, sources, search_query in st.session_state.display_messages:
        avatar = "🧑" if role == "user" else "📚"
        with st.chat_message(role, avatar=avatar):
            if role == "assistant" and search_query:
                st.markdown(
                    f'<div class="badge-search">🔍 Searched knowledge base: '
                    f'<em>{search_query}</em></div>',
                    unsafe_allow_html=True,
                )
            st.markdown(text)

            if sources:
                st.markdown(
                    "<div style='font-size:0.8rem;font-weight:600;"
                    "color:#1a5276;margin:10px 0 4px 0'>📎 Sources</div>",
                    unsafe_allow_html=True,
                )
                for src in sources:
                    with st.expander(f"📄 {src.source}  •  Page {src.page}"):
                        st.markdown(
                            f'<div class="source-card">'
                            f'<div class="src-title">{src.source}</div>'
                            f'<span class="src-page">Page {src.page}</span>'
                            f'<div>{src.text[:600]}{"…" if len(src.text) > 600 else ""}</div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )


# ── Input handler ──────────────────────────────────────────────────────────────

def handle_input() -> None:
    agent = get_agent()

    user_input = st.chat_input(
        "Ask about Verité's research..." if agent.is_ready() else "Knowledge base empty — run ingest.py",
        disabled = not agent.is_ready(),
        key      = f"chat_input_{st.session_state.input_key}",
    )

    if not user_input:
        return

    with st.chat_message("user", avatar="🧑"):
        st.markdown(user_input)

    with st.chat_message("assistant", avatar="📚"):
        with st.spinner("Searching and thinking..."):
            agent_response, updated_history = agent.chat(
                user_message         = user_input,
                session_id           = st.session_state.session_id,
                conversation_history = st.session_state.conversation_history,
            )

        if agent_response.tool_was_used and agent_response.search_query:
            st.markdown(
                f'<div class="badge-search">🔍 Searched knowledge base: '
                f'<em>{agent_response.search_query}</em></div>',
                unsafe_allow_html=True,
            )

        st.markdown(agent_response.text)

        if agent_response.sources:
            st.markdown(
                "<div style='font-size:0.8rem;font-weight:600;"
                "color:#1a5276;margin:10px 0 4px 0'>📎 Sources</div>",
                unsafe_allow_html=True,
            )
            for src in agent_response.sources:
                with st.expander(f"📄 {src.source}  •  Page {src.page}"):
                    st.markdown(
                        f'<div class="source-card">'
                        f'<div class="src-title">{src.source}</div>'
                        f'<span class="src-page">Page {src.page}</span>'
                        f'<div>{src.text[:600]}{"…" if len(src.text) > 600 else ""}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

    st.session_state.conversation_history = updated_history
    st.session_state.display_messages.append(("user", user_input, [], None))
    st.session_state.display_messages.append((
        "assistant", agent_response.text,
        agent_response.sources, agent_response.search_query,
    ))
    st.session_state.input_key += 1


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    if not GROQ_API_KEY:
        st.error(
            "### ⚠️ GROQ_API_KEY is not set\n\n"
            "**Local:** Add it to your `.env` file.\n\n"
            "**Hugging Face Spaces:** Settings → Repository Secrets → add `GROQ_API_KEY`."
        )
        st.stop()

    init_session()
    render_sidebar()
    render_header()

    if not get_agent().is_ready():
        st.warning("Knowledge base is empty — place PDFs in `data/` and run `python ingest.py`")
        return

    if not st.session_state.display_messages:
        render_welcome()

    render_chat()
    handle_input()


if __name__ == "__main__":
    main()
