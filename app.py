import streamlit as st
import requests
import io
import json
import os
import time

if "splash_shown" not in st.session_state:
    st.session_state.splash_shown = False

if not st.session_state.splash_shown:
    splash = st.empty()
    with splash.container():
        st.markdown("""
        <div style="display:flex; flex-direction:column; align-items:center;
        justify-content:center; height:80vh; text-align:center;">
            <div style="font-size:5rem;">👗</div>
            <h1 style="font-size:3rem; background:linear-gradient(90deg,#1d4ed8,#7c3aed);
            -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
            Fashion AI</h1>
            <p style="color:#64748b; font-size:1.2rem;">Your Personal AI Stylist</p>
            <p style="color:#94a3b8; font-style:italic;">"Style is a way to say who you are without speaking..."</p>
        </div>
        """, unsafe_allow_html=True)
        time.sleep(3)
    splash.empty()
    st.session_state.splash_shown = True
    st.rerun()
from datetime import datetime
from PIL import Image
from analyzer import analyze_outfit

# ── Page config ────────────────────────────────────────────────
st.set_page_config(
    page_title="Fashion AI",
    page_icon="👗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ─────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');

* { font-family: 'Poppins', sans-serif; }

/* Main background */
.stApp { background: linear-gradient(135deg, #f0f4ff 0%, #ffffff 100%); }

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1d4ed8 0%, #1e40af 100%);
    color: white;
}
[data-testid="stSidebar"] * { color: white !important; }
[data-testid="stSidebar"] .stSelectbox label { color: white !important; }

/* Title */
.main-title {
    font-size: 3rem;
    font-weight: 700;
    background: linear-gradient(90deg, #1d4ed8, #7c3aed);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
    margin-bottom: 0;
}
.subtitle {
    text-align: center;
    color: #64748b;
    font-size: 1.1rem;
    margin-bottom: 2rem;
}

/* Suggestion box */
.suggestion-box {
    background: white;
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 4px 24px rgba(29,78,216,0.08);
    border-left: 5px solid #1d4ed8;
    font-size: 1.05rem;
    line-height: 1.8;
    color: #1e293b;
}

/* Outfit card */
.outfit-card {
    background: white;
    border-radius: 16px;
    padding: 20px;
    box-shadow: 0 4px 24px rgba(29,78,216,0.08);
    text-align: center;
}

/* UIverse style animated button */
.uiverse-btn {
    display: inline-block;
    padding: 12px 32px;
    background: linear-gradient(90deg, #1d4ed8, #7c3aed);
    color: white !important;
    border-radius: 50px;
    font-weight: 600;
    font-size: 1rem;
    border: none;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(29,78,216,0.3);
    text-decoration: none;
}
.uiverse-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(29,78,216,0.4);
}

/* Like/Feedback button */
.like-btn {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 24px;
    background: white;
    border: 2px solid #e2e8f0;
    border-radius: 50px;
    cursor: pointer;
    font-weight: 600;
    color: #64748b;
    transition: all 0.3s ease;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.like-btn:hover {
    border-color: #f43f5e;
    color: #f43f5e;
    transform: scale(1.05);
}

/* History card */
.history-card {
    background: white;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 12px;
    box-shadow: 0 2px 12px rgba(29,78,216,0.06);
    border-left: 4px solid #1d4ed8;
}

/* Feedback form */
.feedback-box {
    background: linear-gradient(135deg, #eff6ff, #f5f3ff);
    border-radius: 16px;
    padding: 24px;
    border: 1px solid #bfdbfe;
    margin-top: 20px;
}

/* Divider */
.divider {
    height: 2px;
    background: linear-gradient(90deg, #1d4ed8, #7c3aed);
    border-radius: 2px;
    margin: 20px 0;
}
</style>
""", unsafe_allow_html=True)

# ── History helpers ─────────────────────────────────────────────
HISTORY_FILE = "history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []

def save_to_history(style, suggestion):
    history = load_history()
    entry = {
        "date": datetime.now().strftime("%d %b %Y, %I:%M %p"),
        "style": style,
        "suggestion": suggestion[:300] + "..."
    }
    history.insert(0, entry)
    history = history[:20]
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)

# ── Session state ───────────────────────────────────────────────
if "try_count" not in st.session_state:
    st.session_state.try_count = 0
if "show_feedback" not in st.session_state:
    st.session_state.show_feedback = False
if "suggestion_text" not in st.session_state:
    st.session_state.suggestion_text = None
if "outfit_image" not in st.session_state:
    st.session_state.outfit_image = None
if "image_prompt" not in st.session_state:
    st.session_state.image_prompt = None

# ── Header ──────────────────────────────────────────────────────
st.markdown('<div class="main-title">👗 Fashion AI</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Your Personal AI Stylist — Upload a photo, get outfit suggestions instantly</div>', unsafe_allow_html=True)
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ── Sidebar ─────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    st.markdown("---")

    uploaded_file = st.file_uploader(
        "📷 Upload Your Photo",
        type=["jpg", "jpeg", "png", "webp"],
        help="Upload a clear front-facing photo"
    )

    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, caption="Your Photo", use_container_width=True)

    st.markdown("---")
    style = st.selectbox(
        "👗 Style Preference",
        ["Casual", "Formal", "College Wear", "Party Wear", "Traditional"]
    )

    st.markdown("---")
    st.markdown("### 📊 Stats")
    st.metric("Analyses Done", st.session_state.try_count)

    st.markdown("---")
    st.markdown("**Made with ❤️ using**")
    st.markdown("Python • Streamlit • Gemini AI")

# ── Main tabs ───────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["✨ Get Suggestions", "🕓 History", "ℹ️ About"])

# ════════════════════════════════════════════════════════════════
# TAB 1 — Main
# ════════════════════════════════════════════════════════════════
with tab1:
    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown("### 📸 Your Photo")
        if uploaded_file:
            st.image(img, use_container_width=True)
        else:
            st.info("👈 Upload your photo from the sidebar to get started!")

        # Animated get suggestions button
        st.markdown("""
        <style>
        div.stButton > button {
            width: 100%;
            padding: 14px;
            background: linear-gradient(90deg, #1d4ed8, #7c3aed);
            color: white;
            border: none;
            border-radius: 50px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(29,78,216,0.3);
        }
        div.stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(29,78,216,0.5);
        }
        </style>
        """, unsafe_allow_html=True)

        analyze = st.button("✨ Get Outfit Suggestions", use_container_width=True)

    with col2:
        st.markdown("### 👗 Outfit Suggestions")

        if analyze:
            if not uploaded_file:
                st.error("⚠️ Please upload a photo first!")
            else:
                with st.spinner("🔍 Analyzing your style..."):
                    try:
                        # Save uploaded file temporarily
                        temp_path = f"temp_{uploaded_file.name}"
                        with open(temp_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())

                        result = analyze_outfit(temp_path, style)
                        if result is None:
                            st.error("❌ AI returned empty response. Please try again!")
                            st.stop()
                        suggestion_text, image_prompt = result
                        st.session_state.suggestion_text = suggestion_text
                        st.session_state.image_prompt = image_prompt
                        st.session_state.try_count += 1

                        save_to_history(style, suggestion_text)

                        # Show feedback every 3 tries
                        if st.session_state.try_count % 3 == 0:
                            st.session_state.show_feedback = True

                        os.remove(temp_path)
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

        if st.session_state.suggestion_text:
            st.markdown(f"""
            <div class="suggestion-box">
            {st.session_state.suggestion_text.replace(chr(10), '<br>')}
            </div>
            """, unsafe_allow_html=True)

            # Copy & PDF buttons
            bcol1, bcol2 = st.columns(2)
            with bcol1:
                st.download_button(
                    "📋 Download Suggestions",
                    data=st.session_state.suggestion_text,
                    file_name="fashion_suggestions.txt",
                    mime="text/plain",
                    use_container_width=True
                )

    # ── Outfit Image ───────────────────────────────────────────
    if st.session_state.image_prompt:
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown("### 👗 Generated Outfit Preview")

        with st.spinner("🎨 Generating outfit image..."):
            try:
                encoded = st.session_state.image_prompt.replace(" ", "%20")
                url = f"https://image.pollinations.ai/prompt/{encoded}?width=500&height=500&nologo=true"
                response = requests.get(url, timeout=60)
                outfit_img = Image.open(io.BytesIO(response.content))
                st.session_state.outfit_image = outfit_img
            except:
                outfit_img = None

        if st.session_state.outfit_image:
            imgcol1, imgcol2, imgcol3 = st.columns([1, 2, 1])
            with imgcol2:
                st.markdown('<div class="outfit-card">', unsafe_allow_html=True)
                st.image(st.session_state.outfit_image,
                    caption="AI Generated Outfit", use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

                # Save image button
                buf = io.BytesIO()
                st.session_state.outfit_image.save(buf, format="PNG")
                st.download_button(
                    "💾 Save Outfit Image",
                    data=buf.getvalue(),
                    file_name="outfit.png",
                    mime="image/png",
                    use_container_width=True
                )

    # ── Feedback (every 3 tries) ───────────────────────────────
    if st.session_state.show_feedback:
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown('<div class="feedback-box">', unsafe_allow_html=True)
        st.markdown("### 💬 You've used Fashion AI 3 times! How's it going?")

        fcol1, fcol2, fcol3 = st.columns(3)
        with fcol1:
            if st.button("❤️ Loving it!", use_container_width=True):
                st.success("Thank you! That means a lot 🙏")
                st.session_state.show_feedback = False
        with fcol2:
            if st.button("😐 It's okay", use_container_width=True):
                st.info("Thanks for the feedback! We'll improve 💪")
                st.session_state.show_feedback = False
        with fcol3:
            if st.button("😞 Needs work", use_container_width=True):
                st.warning("Sorry to hear that! Tell us more below 👇")

        feedback_text = st.text_area("Any specific feedback? (optional)")
        if st.button("Submit Feedback"):
            st.success("Feedback submitted! Thank you 🙏")
            st.session_state.show_feedback = False
        st.markdown('</div>', unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
# TAB 2 — History
# ════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("### 🕓 Past Analyses")
    history = load_history()

    if not history:
        st.info("No history yet! Start by getting outfit suggestions.")
    else:
        for entry in history:
            st.markdown(f"""
            <div class="history-card">
                <strong>🕓 {entry['date']}</strong> &nbsp;|&nbsp; 👗 <strong>{entry['style']}</strong><br>
                <span style="color:#64748b; font-size:0.95rem">{entry['suggestion']}</span>
            </div>
            """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
# TAB 3 — About
# ════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("### ℹ️ About Fashion AI")
    st.markdown("""
    <div class="suggestion-box">
    <strong>Fashion AI</strong> is a smart outfit suggestion system built as part of an Interdisciplinary Project.<br><br>
    🤖 <strong>AI Engine:</strong> OpenRouter (Llama Vision Model)<br>
    🎨 <strong>Image Generation:</strong> Pollinations AI<br>
    🐍 <strong>Built with:</strong> Python, Streamlit<br>
    👨‍💻 <strong>Developer:</strong> Mohammed Umar<br><br>
    Upload your photo, choose a style, and let AI suggest the perfect outfit for you!
    </div>
    """, unsafe_allow_html=True)