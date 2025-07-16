import streamlit as st
import os
import google.genai as genai
from dotenv import load_dotenv


from audio_recorder_streamlit import audio_recorder
import tempfile
from gtts import gTTS
import base64

# Load environment variables from .env file
load_dotenv()

# --- Page Configuration ---
st.set_page_config(
    page_title="Language Learner",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom CSS for Styling ---
st.markdown("""
<style>
    /* Base styles for light mode */
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background-color: #FFFFFF;
        color: #000000;
    }
    .stButton>button {
        border-radius: 12px;
        padding: 12px 24px;
        font-size: 18px;
        background-color: #F0F2F6;
        color: #31333F;
    }
    .stSelectbox div[data-baseweb="select"] > div {
        background-color: #F0F2F6;
        color: #31333F;
    }
    h1, h2, h3, h4, h5, h6 {
        font-weight: 600;
    }

    /* Dark Mode Theme */
    body.dark-mode {
        background-color: #1E1E1E;
        color: #FFFFFF;
    }
    .dark-mode .stButton>button {
        background-color: #007ACC;
        color: #FFFFFF;
    }
    .dark-mode .stSelectbox div[data-baseweb="select"] > div {
        background-color: #333333;
        color: #FFFFFF;
    }

    /* High Contrast Mode */
    body.high-contrast {
        background-color: #000000;
        color: #FFFF00;
    }
    .high-contrast .stButton>button {
        background-color: #FFFF00;
        color: #000000;
        border: 2px solid #000000;
    }
    .high-contrast .stSelectbox div[data-baseweb="select"] > div {
        background-color: #555555;
        color: #FFFF00;
    }
    .high-contrast h1, .high-contrast h2, .high-contrast h3, .high-contrast h4, .high-contrast h5, .high-contrast h6 {
        color: #FFFF00;
    }
</style>
""", unsafe_allow_html=True)


# --- Gemini API Configuration ---
try:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.error("GEMINI_API_KEY not found. Please set it in your .env file.")
    else:
        genai.configure(api_key=api_key)
except Exception as e:
    st.error(f"Error configuring Gemini API: {e}")

# --- Text-to-Speech Function ---
def text_to_speech(text, lang='en'):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        tts = gTTS(text=text, lang=lang)
        tts.save(fp.name)
        return fp.name

def autoplay_audio(file_path: str):
    with open(file_path, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f"""
            <audio controls autoplay="true">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
        st.markdown(
            md,
            unsafe_allow_html=True,
        )

def inject_theme():
    theme_class = ''
    if 'theme' in st.session_state:
        if st.session_state.theme == 'dark':
            theme_class = 'dark-mode'
        elif st.session_state.theme == 'contrast':
            theme_class = 'high-contrast'

    st.markdown(
        f"""
        <script>
            const body = window.parent.document.querySelector('body');
            body.className = '{theme_class}';
        </script>
        """,
        unsafe_allow_html=True
    )

# --- Main App ---
def main():
    inject_theme()


    st.title("Language Learner 🎙️")
    st.markdown("Learn a new language with our chatbot!")

    language = st.selectbox("Select Target Language", ["Hebrew", "Finnish", "French", "Korean", "Bahasa Melayu", "Bahasa Indonesia", "Simplified Chinese", "Traditional Chinese"])
    
    st.header("Conversation")

    # --- Audio Recorder ---
    audio_bytes = audio_recorder(
        text="Click to record",
        recording_color="#e8b623",
        neutral_color="#6a6a6a",
        icon_name="microphone",
        pause_threshold=2.0,
    )

    if audio_bytes:
        st.audio(audio_bytes, format="audio/wav")

        try:
            model = genai.GenerativeModel('models/gemini-live-2.5-flash-preview')
            response = model.generate_content([
                "Please transcribe this audio file.",
                {"mime_type": "audio/wav", "data": audio_bytes}
            ])
            response_text = response.text
            
            with st.chat_message("assistant"):
                st.markdown(response_text)
            
            if response_text:
                lang_code = 'en'
                if language == "Hebrew": lang_code = 'iw'
                elif language == "Finnish": lang_code = 'fi'
                elif language == "French": lang_code = 'fr'
                elif language == "Korean": lang_code = 'ko'
                elif language == "Bahasa Melayu" or language == "Bahasa Indonesia": lang_code = 'id'
                elif language == "Simplified Chinese" or language == "Traditional Chinese": lang_code = 'zh-CN'

                audio_file = text_to_speech(response_text, lang=lang_code)
                autoplay_audio(audio_file)

        except Exception as e:
            st.error(f"Error during conversation: {e}")

    # --- Lesson Panel (Sidebar) ---
    with st.sidebar:
        st.header("Lessons")
        st.progress(25, "Lesson 1: Greetings")
        
        with st.expander("Topics"):
            st.write("1. Greetings")
            st.write("2. Numbers")
            st.write("3. Daily Phrases")

    # --- Footer ---
    st.markdown("---")
    st.markdown("Help & Instructions: Click the microphone to record your message.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Toggle Dark Mode"):
            st.session_state.theme = 'dark' if st.session_state.theme != 'dark' else 'light'
            st.rerun()
            
    with col2:
        if st.button("High Contrast Mode"):
            st.session_state.theme = 'contrast' if st.session_state.theme != 'contrast' else 'light'
            st.rerun()

if __name__ == "__main__":
    main()
