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
# from google import genai
from dotenv import load_dotenv

# import asyncio
import websockets
import queue
import base64
import threading
import asyncio, taskgroup, exceptiongroup
import contextlib
from IPython import display
from fuzzywuzzy import fuzz




# Optional audio imports - comment out if causing issues
try:
    import speech_recognition as sr
    from gtts import gTTS
    import pygame
    from streamlit_webrtc import webrtc_streamer, WebRtcMode
    import av

    AUDIO_ENABLED = True
except ImportError:
    AUDIO_ENABLED = False

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
        # for Gemini live API
        st.session_state.audio_queue = queue.Queue()
        st.session_state.audio_processing = False
        st.session_state.audio_messages = []
        st.session_state.websocket_connected = False


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

# Language options
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
        # self.model = genai.GenerativeModel('gemini-1.5-flash') # 50 requests per day
        self.model = genai.GenerativeModel('gemma-3-27b-it') # 14.4k requests per day


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
                import re
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
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                else:
                    json_str = response_text

            result = json.loads(json_str)
            return result
        except Exception as e:
            return {
                "accuracy_score": 70,
                "feedback": "Keep practicing!",
                "tips": ["Try speaking more slowly", "Focus on pronunciation"],
                "encouragement": "You're doing great!"
            }

    def generate_conversation(self, topic: str, language: str, level: str) -> Dict[str, any]:
        """Generate a conversation scenario"""
        prompt = f"""
        Create a simple {level} level conversation in {language} about {topic}.
        Include English translations.

        Format as JSON:
        {{
            "scenario": "description of the situation",
            "dialogue": [
                {{"speaker": "A", "text": "...", "translation": "..."}},
                {{"speaker": "B", "text": "...", "translation": "..."}}
            ],
            "vocabulary": {{"word": "translation", ...}},
            "grammar_point": "brief explanation"
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
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                else:
                    json_str = response_text

            result = json.loads(json_str)
            return result
        except Exception as e:
            return {
                "scenario": f"Practice {topic} conversation",
                "dialogue": [
                    {"speaker": "A", "text": "Hello", "translation": "Hello"},
                    {"speaker": "B", "text": "Hi", "translation": "Hi"}
                ],
                "vocabulary": {},
                "grammar_point": "Practice basic conversation"
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

    /* Audio player styling */
    .audio-controls {{
        display: flex;
        gap: 15px;
        align-items: center;
        margin: 20px 0;
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

    /* Accessibility announcements */
    .sr-only {{
        position: absolute;
        width: 1px;
        height: 1px;
        padding: 0;
        margin: -1px;
        overflow: hidden;
        clip: rect(0,0,0,0);
        white-space: nowrap;
        border: 0;
    }}
    
    /* Live conversation styling */
    .conversation-bubble {{
        padding: 15px;
        border-radius: 18px;
        margin: 10px 0;
        max-width: 80%;
    }}
    
    .user-bubble {{
        background-color: #d1e7ff;
        margin-left: auto;
    }}
    
    .bot-bubble {{
        background-color: #f0f0f0;
        margin-right: auto;
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


def display_progress_bar():
    """Display overall progress"""
    total_lessons = len(CURRICULUM)
    completed_lessons = len(st.session_state.lesson_completed)
    progress = (completed_lessons / total_lessons) * 100

    st.markdown(f"""
    <div class="progress-bar" role="progressbar" aria-valuenow="{progress}" 
         aria-valuemin="0" aria-valuemax="100">
        <div class="progress-fill" style="width: {progress}%">
            {int(progress)}% Complete
        </div>
    </div>
    """, unsafe_allow_html=True)



##########################
# from tab1 - after selecting a PRACTICE
# the "supposed tab2"
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
            st.markdown("### 🇬🇧 English")
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
            st.info(
                "🔇 Audio features are not available. To enable audio, install the optional audio libraries listed in requirements.txt")


        col1, col2, col3 = st.columns(3)

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
                    st.info("🔇 Audio features are not available. Install audio libraries to enable.")


        # currently not working
        with col2:
            if st.button("🎤 Record Your Voice", key="record_voice",
                         help="Record yourself saying the phrase"):
                st.info("🎤 Recording feature coming soon!")
                # Note: Actual recording would require WebRTC implementation


        # currently not updating the 'selected_phrase' st.selectbox
        # maybe comment out this line?
        with col3:
            if st.button("📝 Next Phrase", key="next_phrase",
                         help="Move to the next phrase"):
                # Find next phrase
                current_idx = current_lesson['phrases'].index(selected_phrase)
                if current_idx < len(current_lesson['phrases']) - 1:
                    next_phrase = current_lesson['phrases'][current_idx + 1]
                    st.success(f"Moving to: {next_phrase}")
                else:
                    st.session_state.lesson_completed.add(st.session_state.current_topic)
                    st.balloons()
                    st.success("🎉 Lesson completed!")
        ###############################



        # Interactive practice
        st.markdown("### 💬 Practice Typing Translated Text")

        user_input = st.text_input(
            "Try translating this phrase yourself:",
            placeholder=f"Type the {target_lang} translation here...",
            help="Type your translation and press Enter"
        )

        if user_input:
            # Approach 1 - Exact string matching
            # # Simple feedback (in real app, would use Gemini for evaluation)
            # if user_input.lower() == translation_data['translation'].lower():
            #     st.success("🎯 Perfect! Great job!")
            # else:
            #     st.warning(f"Not quite. The correct translation is: {translation_data['translation']}")
            #     st.info("Keep practicing! You're doing great!")
            # Calculate similarity score (0-100)
            
            # Approach 2 - flexible/fuzzy match
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






################################
# tab3 live conversation
################################
def start_live_conversation():
    """Initialize live conversation session"""
    st.session_state.audio_processing = True
    st.session_state.audio_messages = []
    st.session_state.websocket_connected = False

def stop_live_conversation():
    """Stop live conversation session"""
    st.session_state.audio_processing = False
    st.session_state.websocket_connected = False

def display_conversation_bubbles():
    """Display conversation messages in chat bubbles"""
    for msg in st.session_state.audio_messages:
        if msg['role'] == 'user':
            st.markdown(f"""
                <div class="conversation-bubble user-bubble">
                    <strong>You:</strong> {msg['text']}
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class="conversation-bubble bot-bubble">
                    <strong>Bot:</strong> {msg['text']}
                </div>
            """, unsafe_allow_html=True)
            
            # Play audio if available
            if 'audio' in msg and msg['audio'] is not None:
                st.audio(msg['audio'], format='audio/mp3')




def manage_websocket_connection(target_language, api_key):
    """Manage WebSocket connection to Gemini Live with passed parameters"""
    HOST = 'generativelanguage.googleapis.com'
    MODEL = 'models/gemini-live-2.5-flash-preview'
    INITIAL_REQUEST_TEXT = f"You are a helpful language tutor for {target_language}. Help beginners practice conversation."
    
    # Create a new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def run_websocket():
        uri = f'wss://{HOST}/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent?key={api_key}'
        
        try:
            async with websockets.connect(uri, ping_interval=10, ping_timeout=10) as websocket:
                # Update connection status using thread-safe state
                st.session_state._ws_connected = True
                st.session_state._ws_should_rerun = True
                
                # Send initial setup
                initial_request = json.dumps({
                    'setup': {
                        'model': MODEL,
                    },
                })
                await websocket.send(initial_request)
                
                # Send initial text prompt
                if INITIAL_REQUEST_TEXT:
                    text_request = json.dumps({
                        'clientContent': {
                            'turns': [{
                                'role': 'USER',
                                'parts': [{'text': INITIAL_REQUEST_TEXT}],
                            }],
                            'turnComplete': True,
                        },
                    })
                    await websocket.send(text_request)
                
                # Process messages
                while 'audio_processing' in st.session_state and st.session_state.audio_processing:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=5)
                        data = json.loads(message)
                        
                        # Handle responses
                        if 'serverContent' in data:
                            server_content = data['serverContent']
                            
                            # Handle model turn
                            if 'modelTurn' in server_content:
                                model_turn = server_content['modelTurn']
                                
                                # Initialize messages list if not exists
                                if 'audio_messages' not in st.session_state:
                                    st.session_state.audio_messages = []
                                
                                # Process audio parts
                                for part in model_turn.get('parts', []):
                                    if 'inlineData' in part and 'data' in part['inlineData']:
                                        audio_data = base64.b64decode(part['inlineData']['data'])
                                        if audio_data:
                                            # Add to conversation
                                            st.session_state.audio_messages.append({
                                                'role': 'bot',
                                                'text': "[Audio response]",
                                                'audio': audio_data
                                            })
                                            st.session_state._ws_should_rerun = True
                                
                                # Process text parts
                                for part in model_turn.get('parts', []):
                                    if 'text' in part:
                                        # Add to conversation
                                        st.session_state.audio_messages.append({
                                            'role': 'bot',
                                            'text': part['text'],
                                            'audio': None
                                        })
                                        st.session_state._ws_should_rerun = True
                        
                    except asyncio.TimeoutError:
                        # Timeout is normal, just check if we should continue
                        continue
                    except Exception as e:
                        st.session_state._ws_error = f"Error processing message: {str(e)}"
                        st.session_state._ws_should_rerun = True
                        break
        
        except websockets.exceptions.ConnectionClosedError as e:
            st.session_state._ws_error = f"Connection closed unexpectedly: {str(e)}"
            st.session_state._ws_should_rerun = True
        except Exception as e:
            st.session_state._ws_error = f"WebSocket error: {str(e)}"
            st.session_state._ws_should_rerun = True
        finally:
            st.session_state._ws_connected = False
            st.session_state._ws_should_rerun = True
    
    # Run the async function in the event loop
    loop.run_until_complete(run_websocket())






def live_conversation_interface():
    """Real-time conversation with Gemini Live"""
    st.header("🎤 Real-time Conversation")
    st.markdown("Practice speaking with an AI tutor in real-time using your microphone")
    
    # Connection management
    if (st.session_state.audio_processing and 
        not st.session_state.websocket_connected and
        not hasattr(st.session_state, '_ws_thread_running')):
        
        # Get values before starting thread
        target_language = st.session_state.target_language
        api_key = os.getenv('GEMINI_API_KEY', '')
        
        if not api_key:
            st.error("Gemini API key not found")
            st.session_state.audio_processing = False
            return
        
        # Initialize thread state
        st.session_state._ws_thread_running = True
        st.session_state._ws_connected = False
        st.session_state._ws_should_rerun = False
        st.session_state._ws_error = None
        
        # Start WebSocket connection in a separate thread
        threading.Thread(
            target=manage_websocket_connection,
            args=(target_language, api_key),
            daemon=True
        ).start()
    
    # Handle WebSocket status updates from the thread
    if hasattr(st.session_state, '_ws_should_rerun') and st.session_state._ws_should_rerun:
        st.session_state.websocket_connected = getattr(st.session_state, '_ws_connected', False)
        st.session_state._ws_should_rerun = False
        
        if hasattr(st.session_state, '_ws_error') and st.session_state._ws_error:
            st.error(st.session_state._ws_error)
            del st.session_state._ws_error
        
        st.rerun()
    
    # Clean up thread state when stopping
    if not st.session_state.audio_processing and hasattr(st.session_state, '_ws_thread_running'):
        # Clean up thread state
        for attr in ['_ws_thread_running', '_ws_connected', '_ws_should_rerun', '_ws_error']:
            if hasattr(st.session_state, attr):
                delattr(st.session_state, attr)
        st.rerun()

################################





def main():
    """Main application"""
    init_session_state()
    apply_custom_css()

    # Skip to main content link for screen readers
    st.markdown('<a href="#main-content" class="skip-link">Skip to main content</a>',
                unsafe_allow_html=True)

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
    # Progress overview
    display_progress_bar()


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
        # AFTER WE SELECT A PRACTICE IN 'tab1 📚 Lessons'
        if st.session_state.current_topic and st.session_state.current_topic in CURRICULUM:
            # Show practice interface
            practice_interface(teacher)
        else:
            # Show MAIN NAVIGATION TABS
            # WHEN THE PAGE LOADS INITIALLY
            tab1, tab2, tab3, tab4 = st.tabs(["📚 Lessons", "🗣️ Practice", "🎤 Live Conversation", "📊 Progress"])

            with tab1:
                st.header("Choose Your Lesson")

                # Display LESSON CARDS in a grid
                cols = st.columns(2)
                for idx, (lesson_key, lesson_data) in enumerate(CURRICULUM.items()):
                    # in col0 OR col1
                    with cols[idx % 2]:
                        display_lesson_card(lesson_key, lesson_data)


            # the loop does not enter tab2
            # maybe comment out tab2?
            # even though original intention might be to go from the 'practice' selected in tab1
            # to the practice in tab2
            # the 'if block' above might be running 1st
            with tab2:
                st.header("🗣️ Practice Mode")
                if st.session_state.current_topic:
                    practice_interface(teacher)
                else:
                    st.info("👈 Please select a lesson from the Lessons tab first!")

            with tab3:
                live_conversation_interface()

            with tab4:
                st.header("📊 Your Progress")

                # Statistics
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Lessons Completed",
                              len(st.session_state.lesson_completed),
                              f"/{len(CURRICULUM)}")

                with col2:
                    total_phrases = sum(len(lesson['phrases']) for lesson in CURRICULUM.values())
                    st.metric("Total Phrases Available", total_phrases)

                with col3:
                    st.metric("Current Language", st.session_state.target_language)

                # Completed lessons
                st.subheader("✅ Completed Lessons")
                if st.session_state.lesson_completed:
                    for lesson in st.session_state.lesson_completed:
                        if lesson in CURRICULUM:
                            st.success(f"✓ {CURRICULUM[lesson]['title']}")
                else:
                    st.info("No lessons completed yet. Start learning!")

                # Reset progress
                if st.button("🔄 Reset Progress",
                             help="Clear all progress and start fresh"):
                    if st.checkbox("Are you sure? This will clear all your progress."):
                        st.session_state.lesson_completed = set()
                        st.session_state.lesson_progress = {}
                        st.session_state.conversation_history = []
                        st.session_state.current_topic = None
                        st.rerun()

    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center'>
            <p>Made with ❤️ for language learners everywhere</p>
            <p>Press Tab to navigate • Press Space to select • Press Escape to close menus</p>
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
