import streamlit as st
import os
from datetime import datetime
import json
import base64
import io
import time
import re
from typing import Dict, List, Optional, Tuple
import google.generativeai as genai
from dotenv import load_dotenv
import tempfile
import numpy as np
from fuzzywuzzy import fuzz
import pyaudio

# Optional audio imports
try:
    import speech_recognition as sr
    from gtts import gTTS
    from audio_recorder_streamlit import audio_recorder

    AUDIO_ENABLED = True
    RECORDER_AVAILABLE = True
except ImportError:
    AUDIO_ENABLED = False
    RECORDER_AVAILABLE = False
    try:
        import speech_recognition as sr
        from gtts import gTTS

        AUDIO_ENABLED = True
    except ImportError:
        pass

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Language Learner - Learn with AI",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Initialize session state
def init_session_state():
    """Initialize all session state variables"""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.target_language = 'Hebrew'
        st.session_state.current_lesson = 0
        st.session_state.lesson_progress = {}
        st.session_state.conversation_history = []
        st.session_state.dark_mode = False
        st.session_state.font_size = 'medium'
        st.session_state.high_contrast = False
        st.session_state.current_topic = None
        st.session_state.lesson_completed = set()
        st.session_state.last_recording = None



# Curriculum structure
CURRICULUM = {
    'greetings': {
        'title': 'Basic Greetings',
        'description': 'Learn how to say hello, goodbye, and introduce yourself',
        'phrases': [
            'Hello', 
            'Good morning', 
            'Good afternoon', 
            'Good evening',
            'How are you?', 
            'I am fine, thank you', 
            'What is your name?',
            'My name is...', 
            'Nice to meet you', 
            'Goodbye'
        ],
        'difficulty': 'beginner'
    },
    'numbers': {
        'title': 'Numbers 1-20',
        'description': 'Learn to count from 1 to 20',
        'phrases': ['One', 
                    'Two', 
                    'Three', 
                    'Four', 
                    'Five', 
                    'Six', 
                    'Seven',
                    'Eight', 
                    'Nine', 
                    'Ten', 
                    'Eleven', 
                    'Twelve', 
                    'Thirteen',
                    'Fourteen', 
                    'Fifteen', 
                    'Sixteen', 
                    'Seventeen', 
                    'Eighteen',
                    'Nineteen', 
                    'Twenty'],
        'difficulty': 'beginner'
    },
    'daily_phrases': {
        'title': 'Daily Phrases',
        'description': 'Common phrases for everyday situations',
        'phrases': [
            'Please', 
            'Thank you', 
            'You are welcome', 
            'Excuse me',
            'I am sorry', 
            'Can you help me?', 
            'Where is the bathroom?',
            'How much does this cost?', 
            'I do not understand',
            'Can you speak slower?'
        ],
        'difficulty': 'beginner'
    },
    'food_drink': {
        'title': 'Food & Drink',
        'description': 'Essential vocabulary for restaurants and cafes',
        'phrases': [
            'I would like...', 
            'Water, please', 
            'Coffee', 
            'Tea',
            'The menu, please', 
            'The bill, please', 
            'Is this vegetarian?',
            'I am allergic to...', 
            'Delicious!', 
            'More, please'
        ],
        'difficulty': 'intermediate'
    },
    'directions': {
        'title': 'Directions',
        'description': 'Ask for and understand directions',
        'phrases': [
            'Where is...?', 
            'Turn left', 
            'Turn right', 
            'Go straight',
            'Near', 
            'Far', 
            'Next to', 
            'Behind', 
            'In front of',
            'How do I get to...?'
        ],
        'difficulty': 'intermediate'
    }
}

# Language options with full names and codes
LANGUAGES = {
    'Hebrew': 'iw', # 2025.07.17 fix language code
    'Finnish': 'fi',
    'French': 'fr',
    'German': 'de',
    'Spanish': 'es',
    'Italian': 'it',
    'Portuguese': 'pt',
    'Japanese': 'ja',
    'Korean': 'ko',
    'Hindi': 'hi',
    'Arabic': 'ar',
    'Bahasa Melayu': 'ms',
    'Chinese (Mandarin)': 'zh'
}


class GeminiLanguageTeacher:
    """Handle Gemini API interactions for language learning"""

    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        # Use gemini-1.5-flash which is the current model
        # self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.model = genai.GenerativeModel('gemma-3-27b-it')  # 14.4k requests per day

    def get_translation(self, text: str, target_language: str) -> Dict[str, str]:
        """Get translation and pronunciation guide"""
        prompt = f"""
        Translate the following text to {target_language}:
        "{text}"

        Provide the response in JSON format with:
        1. "translation": the translated text
        2. "pronunciation": phonetic pronunciation guide
        3. "literal": literal word-by-word translation
        4. "usage_notes": brief usage notes or cultural context

        Example format:
        {{
            "translation": "Hola",
            "pronunciation": "OH-lah",
            "literal": "Hello",
            "usage_notes": "Informal greeting used throughout the day"
        }}
        """

        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()

            # Try to extract JSON from the response
            if '```json' in response_text:
                json_str = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                json_str = response_text.split('```')[1].split('```')[0].strip()
            else:
                # Try to find JSON pattern
                json_match = re.search(r'\{[^{}]*\}', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                else:
                    json_str = response_text

            result = json.loads(json_str)
            return result
        except Exception as e:
            st.error(f"Translation error: {e}")
            # Provide a fallback response
            return {
                "translation": f"[Translation of '{text}' to {target_language}]",
                "pronunciation": "[pronunciation guide]",
                "literal": text,
                "usage_notes": "Translation service temporarily unavailable. Please try again."
            }

    def evaluate_pronunciation(self, user_text: str, target_text: str, language: str) -> Dict[str, any]:
        """Evaluate user's pronunciation attempt"""
        prompt = f"""
        The user is learning {language} and tried to say: "{target_text}"
        They said: "{user_text}"

        Provide feedback in JSON format:
        {{
            "accuracy_score": 0-100,
            "feedback": "constructive feedback",
            "tips": ["tip1", "tip2"],
            "encouragement": "positive message"
        }}
        """

        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()

            # Extract JSON
            if '```json' in response_text:
                json_str = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                json_str = response_text.split('```')[1].split('```')[0].strip()
            else:
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                else:
                    json_str = response_text

            result = json.loads(json_str)
            return result
        except Exception as e:
            # Simple comparison fallback
            similarity_ex = fuzz.ratio(user_text.lower(), target_text)
            # similarity = len(set(user_text.lower().split()) & set(target_text.lower().split())) / max(
            #     len(target_text.split()), 1) * 100
            return {
                "accuracy_score": int(similarity_ex),
                "feedback": "Keep practicing!" if similarity_ex < 70 else "Good job!",
                "tips": ["Try speaking more slowly", "Focus on each syllable"],
                "encouragement": "You're making progress!"
            }


def apply_custom_css():
    """Apply custom CSS for accessibility and theming"""
    font_sizes = {
        'small': '14px',
        'medium': '18px',
        'large': '24px',
        'extra-large': '30px'
    }

    current_font = font_sizes.get(st.session_state.font_size, '18px')

    if st.session_state.dark_mode:
        bg_color = '#1a1a1a'
        text_color = '#ffffff'
        card_bg = '#2d2d2d'
        border_color = '#4a4a4a'
        button_bg = '#4a4a4a'
        button_hover = '#5a5a5a'
    else:
        bg_color = '#ffffff'
        text_color = '#000000'
        card_bg = '#f8f9fa'
        border_color = '#dee2e6'
        button_bg = '#007bff'
        button_hover = '#0056b3'

    if st.session_state.high_contrast:
        text_color = '#ffffff' if st.session_state.dark_mode else '#000000'
        bg_color = '#000000' if st.session_state.dark_mode else '#ffffff'
        border_color = '#ffffff' if st.session_state.dark_mode else '#000000'

    st.markdown(f"""
    <style>
    /* Global styles */
    .stApp {{
        background-color: {bg_color};
        color: {text_color};
    }}

    /* Font size */
    .stApp, .stMarkdown, p, span, div {{
        font-size: {current_font} !important;
    }}

    /* Large buttons for accessibility */
    .stButton > button {{
        font-size: {current_font} !important;
        padding: 15px 30px !important;
        background-color: {button_bg} !important;
        color: white !important;
        border: 2px solid {border_color} !important;
        border-radius: 10px !important;
        min-height: 60px !important;
        transition: all 0.3s ease !important;
    }}

    .stButton > button:hover {{
        background-color: {button_hover} !important;
        transform: scale(1.05);
    }}

    .stButton > button:focus {{
        outline: 3px solid #ff6b6b !important;
        outline-offset: 2px !important;
    }}

    /* Card styling */
    .lesson-card {{
        background-color: {card_bg};
        border: 2px solid {border_color};
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        transition: all 0.3s ease;
    }}

    .lesson-card:hover {{
        transform: translateY(-5px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }}

    /* Progress bar */
    .progress-bar {{
        background-color: {border_color};
        height: 30px;
        border-radius: 15px;
        overflow: hidden;
        margin: 20px 0;
    }}

    .progress-fill {{
        background: linear-gradient(90deg, #4CAF50 0%, #8BC34A 100%);
        height: 100%;
        transition: width 0.5s ease;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
    }}

    /* Audio recorder styling */
    .audio-recorder {{
        background-color: {card_bg};
        border: 2px solid {border_color};
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }}

    /* Focus indicators for keyboard navigation */
    *:focus {{
        outline: 3px solid #ff6b6b !important;
        outline-offset: 2px !important;
    }}

    /* Skip to main content link */
    .skip-link {{
        position: absolute;
        top: -40px;
        left: 0;
        background: #333333;
        color: #FFFFFF !important;
        padding: 10px 15px;
        z-index: 100;
        text-decoration: none;
        border-radius: 0 0 8px 0;
        font-weight: bold;
    }}

    .skip-link:focus {{
        top: 0;
    }}

    /* Large text inputs */
    .stTextInput > div > div > input {{
        font-size: {current_font} !important;
        padding: 15px !important;
        min-height: 50px !important;
    }}

    /* Audio visualization */
    .recording-indicator {{
        display: inline-block;
        width: 20px;
        height: 20px;
        background-color: #ff4444;
        border-radius: 50%;
        animation: pulse 1.5s infinite;
        margin-left: 10px;
    }}

    @keyframes pulse {{
        0% {{
            box-shadow: 0 0 0 0 rgba(255, 68, 68, 0.7);
        }}
        70% {{
            box-shadow: 0 0 0 10px rgba(255, 68, 68, 0);
        }}
        100% {{
            box-shadow: 0 0 0 0 rgba(255, 68, 68, 0);
        }}
    }}
    </style>
    """, unsafe_allow_html=True)


def text_to_speech(text: str, language_code: str) -> Optional[bytes]:
    """Convert text to speech using gTTS"""
    if not AUDIO_ENABLED:
        return None

    try:
        tts = gTTS(text=text, lang=language_code, slow=True)
        audio_fp = io.BytesIO()
        tts.write_to_fp(audio_fp)
        audio_fp.seek(0)
        return audio_fp.read()
    except Exception as e:
        st.error(f"Text-to-speech error: {e}")
        return None


def speech_to_text(audio_bytes: bytes, language_code: str) -> Optional[str]:
    """Convert speech to text using speech recognition"""
    if not AUDIO_ENABLED:
        return None

    try:
        recognizer = sr.Recognizer()

        # Create AudioData from bytes
        audio_data = sr.AudioData(audio_bytes, 44100, 2)

        with sr.Microphone() as src:
            recognizer.adjust_for_ambient_noise(src, duration=2)  # autocalibrate
            audio = recognizer.listen(src, timeout=5, phrase_time_limit=10)

            # Recognize speech
            try:
                print(audio)
                text = recognizer.recognize_google(audio, language=language_code)
                return text
            except sr.UnknownValueError:
                return "Could not understand the audio"
            except sr.RequestError as e:
                return f"Speech recognition error: {str(e)}"
    except Exception as e:
        st.error(f"Speech-to-text error: {e}")
        return None






##########################
# tab1 LESSON CARDS
##########################
def display_lesson_card(lesson_key: str, lesson_data: Dict):
    """Display a lesson card with accessibility features"""
    completed = lesson_key in st.session_state.lesson_completed

    # Create a unique container for each lesson
    container = st.container()
    with container:

        # Use columns for better layout
        # col1_width : col2_width is 3:1
        col1, col2 = st.columns([3, 1])

        with col1:
            # SHOW THE LESSON FROM THE CURRICULUM
            st.markdown(f"""
            <div class="lesson-card" role="article" aria-label="{lesson_data['title']} lesson">
                <h3>{lesson_data['title']} {"✅" if completed else ""}</h3>
                <p>{lesson_data['description']}</p>
                <p><strong>Difficulty:</strong> {lesson_data['difficulty'].capitalize()}</p>
                <p><strong>Phrases:</strong> {len(lesson_data['phrases'])}</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            # INITIALLY - Show "Start <lesson title>" buttons
            # Button outside of markdown for proper functionality
            if st.button(
                    f"Start {lesson_data['title']}" if not completed else f"Review {lesson_data['title']}",
                    key=f"start_{lesson_key}",
                    # tooltip when you hover over the button
                    help=f"Begin the {lesson_data['title']} lesson",
                    use_container_width=True
            ):
                st.session_state.current_topic = lesson_key
                st.rerun()

            if completed:
                st.success("✅ Completed", icon="✅")

##########################


##########################
# from tab1 - after selecting a PRACTICE
##########################
def practice_interface(teacher: GeminiLanguageTeacher):
    """Main practice interface"""
    current_lesson = CURRICULUM.get(st.session_state.current_topic, CURRICULUM['greetings'])

    # Back button
    if st.button("← Back to Lessons", key="back_to_lessons"):
        st.session_state.current_topic = None
        st.rerun()

    st.header(f"📚 {current_lesson['title']}")
    st.markdown(f"*{current_lesson['description']}*")


    ###############################
    # Phrase selector
    ###############################
    selected_phrase = st.selectbox(
        "Choose a phrase to practice:",
        current_lesson['phrases'],
        help="Select a phrase to learn its translation and practice pronunciation"
    )
    ###############################


    if selected_phrase:
        # Get translation
        target_lang = st.session_state.target_language
        translation_data = teacher.get_translation(selected_phrase, target_lang)


        ###############################
        # Display translation card
        ###############################
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### English")
            st.markdown(f"**{selected_phrase}**")

        with col2:
            st.markdown(f"### 🌍 {target_lang}")
            st.markdown(f"**{translation_data['translation']}**")
            if translation_data['pronunciation']:
                st.markdown(f"*Pronunciation: {translation_data['pronunciation']}*")
        ###############################




        ###############################
        # Usage notes
        ###############################        
        if translation_data.get('usage_notes'):
            st.info(f"💡 {translation_data['usage_notes']}")
        ###############################




        ###############################
        # play translation or record audio
        ###############################
        st.markdown("### 🔊 Listen and Practice")
        
        # check if TTS and audio imports worked
        if not AUDIO_ENABLED:
            st.info("🔇 Audio features are not available. To enable audio, install the optional audio libraries.")

        # Three main audio actions
        # col1, col2, col3 = st.columns(3)
        # 2 main audio actions
        col1, col2 = st.columns(2)

        # Audio controls
        with col1:
            if st.button("🔊 Play Translation", key="play_translation",
                         help="Listen to the pronunciation"):
                if AUDIO_ENABLED:
                    audio_data = text_to_speech(
                        translation_data['translation'],
                        LANGUAGES[target_lang]
                    )
                    if audio_data:
                        st.audio(audio_data, format='audio/mp3')
                else:
                    st.info("🔇 Audio features are not available.")



        # currently still debugging
        # audio recording works
        # audio file playback appears
        # BUT error appears later
        #     "Speech-to-text error: No Default Input Device Available"
        with col2:
            if AUDIO_ENABLED and RECORDER_AVAILABLE:
                st.markdown("🎤 **Record Your Voice**")

                # Use audio_recorder for simple recording
                audio_bytes = audio_recorder(
                    text="Click to record",
                    recording_color="#e8b62c",
                    neutral_color="#6aa36f",
                    icon_name="microphone",
                    icon_size="2x",
                    key=f"recorder_{selected_phrase}"
                )

                if audio_bytes:
                    st.audio(audio_bytes, format="audio/wav")

                    # Analyze the recording
                    with st.spinner("Analyzing your pronunciation..."):
                        # Transcribe
                        transcribed = speech_to_text(audio_bytes, LANGUAGES[target_lang])

                        if transcribed:
                            st.markdown(f"**You said:** {transcribed}")

                            # Get evaluation
                            evaluation = teacher.evaluate_pronunciation(
                                transcribed,
                                translation_data['translation'],
                                target_lang
                            )

                            # Display score
                            score = evaluation.get('accuracy_score', 0)
                            if score >= 80:
                                st.success(f"🎯 Excellent! Score: {score}/100")
                            elif score >= 60:
                                st.warning(f"👍 Good effort! Score: {score}/100")
                            else:
                                st.info(f"💪 Keep practicing! Score: {score}/100")

                            # Feedback
                            st.markdown(f"**Feedback:** {evaluation.get('feedback', '')}")

                            # Tips
                            if evaluation.get('tips'):
                                with st.expander("💡 Tips for improvement"):
                                    for tip in evaluation['tips']:
                                        st.markdown(f"• {tip}")

                            # Encouragement
                            st.info(f"💬 {evaluation.get('encouragement', 'Keep practicing!')}")
            else:
                # Fallback for when recorder is not available
                st.markdown("🎤 **Recording**")

                # Alternative: File upload for audio
                uploaded_audio = st.file_uploader(
                    "Upload an audio recording",
                    type=['wav', 'mp3', 'm4a'],
                    key=f"upload_{selected_phrase}",
                    help="Record yourself saying the phrase and upload the audio file"
                )

                if uploaded_audio:
                    audio_bytes = uploaded_audio.read()
                    st.audio(audio_bytes)

                    if AUDIO_ENABLED:
                        with st.spinner("Analyzing..."):
                            transcribed = speech_to_text(audio_bytes, LANGUAGES[target_lang])
                            if transcribed:
                                st.markdown(f"**You said:** {transcribed}")
                    else:
                        st.info("Install audio libraries for speech recognition")

        # with col3:
        #     if st.button("📝 Next Phrase", key="next_phrase",
        #                  help="Move to the next phrase"):
        #         # Find next phrase
        #         current_idx = current_lesson['phrases'].index(selected_phrase)
        #         if current_idx < len(current_lesson['phrases']) - 1:
        #             next_phrase = current_lesson['phrases'][current_idx + 1]
        #             st.success(f"Moving to: {next_phrase}")
        #             st.rerun()
        #         else:
        #             st.session_state.lesson_completed.add(st.session_state.current_topic)
        #             st.balloons()
        #             st.success("🎉 Lesson completed!")

        # Interactive practice
        st.markdown("### 💬 Practice Conversation")

        user_input = st.text_input(
            "Try translating this phrase yourself:",
            placeholder=f"Type the {target_lang} translation here...",
            help="Type your translation and press Enter"
        )

        if user_input:
            similarity = fuzz.ratio(user_input.lower(), translation_data['translation'].lower())

            if similarity > 90:  # Adjust threshold as needed
                st.success("🎯 Perfect! Great job!")
            elif similarity > 70:
                st.info(f"Close! The correct translation is: {translation_data['translation']}")
                st.info("You were very close! Just a small typo.")
            else:
                st.warning(f"Not quite. The correct translation is: {translation_data['translation']}")
                st.info("Keep practicing! You'll get it next time!")

##########################






def main():
    """Main application"""
    init_session_state()
    apply_custom_css()

    # # Skip to main content link for screen readers
    # st.markdown('<a href="#main-content" class="skip-link">Skip to main content</a>',
    #             unsafe_allow_html=True)

    # Header
    col1, col2, col3 = st.columns([2, 1, 1])

    # TOP-LEFT
    with col1:
        st.title("🌍 Language Learner")
        st.markdown("Learn a new language with AI-powered assistance!")

    # TOP-MIDDLE
    with col2:
        # Language selector
        st.session_state.target_language = st.selectbox(
            "Target Language:",
            list(LANGUAGES.keys()),
            index=list(LANGUAGES.keys()).index(st.session_state.target_language),
            help="Choose the language you want to learn"
        )

    # TOP-RIGHT
    with col3:
        # Accessibility controls
        with st.expander("♿ Accessibility"):
            st.checkbox("🌙 Dark Mode",
                        value=st.session_state.dark_mode,
                        key="dark_mode_toggle",
                        on_change=lambda: setattr(st.session_state, 'dark_mode',
                                                  not st.session_state.dark_mode))

            st.session_state.font_size = st.select_slider(
                "Font Size:",
                options=['small', 'medium', 'large', 'extra-large'],
                value=st.session_state.font_size
            )

            st.checkbox("🔲 High Contrast",
                        value=st.session_state.high_contrast,
                        key="high_contrast_toggle",
                        on_change=lambda: setattr(st.session_state, 'high_contrast',
                                                  not st.session_state.high_contrast))

    # TOP-MIDDLE OF THE PAGE
    # # Progress overview
    # display_progress_bar()

    # PLACEHOLDER CONTAINER FOR SCREEN READER TO JUMP HERE
    # Main content area
    st.markdown('<div id="main-content"></div>', unsafe_allow_html=True)

    # Initialize teacher
    api_key = os.getenv('GEMINI_API_KEY', '')
    if not api_key:
        st.warning("⚠️ Please set your GEMINI_API_KEY in the .env file")
        api_key = st.text_input("Enter your Gemini API Key:", type="password")

    if api_key:
        teacher = GeminiLanguageTeacher(api_key)

        # Check if we're in PRACTICE MODE
        # AFTER SELECTING A TAB
        if st.session_state.current_topic and st.session_state.current_topic in CURRICULUM:
            # Show practice interface
            practice_interface(teacher)
        else:
            # Display lesson cards in a grid
            cols = st.columns(2)
            for idx, (lesson_key, lesson_data) in enumerate(CURRICULUM.items()):
                with cols[idx % 2]:
                    display_lesson_card(lesson_key, lesson_data)

    # Footer
    st.markdown("---")



if __name__ == "__main__":
    main()
