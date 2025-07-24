# Language Learner App - Technical Plan 

## Overview
The Language Learner is an AI-powered web application built with Streamlit that provides interactive language learning through structured lessons, real-time translation, and pronunciation feedback using Google's Gemini AI.

## Architecture & Components

### 1. Core Technology Stack
- **Frontend**: Streamlit 
- **Backend**: Python with Google Generative AI (Gemini)
- **Audio Processing**: gTTS (Text-to-Speech), SpeechRecognition, audio-recorder-streamlit
- **API Integration**: Google Gemini AI (gemma-3-27b-it model)
- **Additional Libraries**: fuzzywuzzy, pyaudio, dotenv

### 2. Application Structure

#### Session State Management
```python
# Core state variables initialized in init_session_state()
- target_language: Selected learning language
- current_lesson: Active lesson index
- accessibility settings: dark_mode, font_size, high_contrast
- current_topic: Active lesson topic
```

#### Curriculum Architecture
```python
CURRICULUM = {
    'lesson_key': {
        'title': 'Display name',
        'description': 'Lesson overview',
        'phrases': ['list', 'of', 'practice', 'phrases'],
    }
}
```

#### Language Support
11 supported languages with proper language codes for TTS/STT:
Hebrew, Spanish, French, German, Italian, Portuguese, Japanese, Korean, Chinese, Hindi, Arabic

## 3. Core Application Logic Flow

### Application Initialization
```
1. Load environment variables (.env file for API keys)
2. Configure Streamlit page (title, icon, layout)
3. Initialize session state variables
```

### Main Application Workflow

#### Phase 1: User Interface Setup
```
Header Section:
├── App Title & Description
├── Language Selector (target language)
└── Accessibility Controls
    ├── Dark/Light Mode Toggle
    ├── Font Size Slider (small → extra-large)
    └── High Contrast Mode
```

#### Phase 2: Lesson Selection Interface
```
Main Content Area:
├── Lesson Cards Grid (2-column layout)
│   ├── Lesson Title & Emoji
│   ├── Description
│   └──Phrase Count
```

#### Phase 3: Practice Interface (when lesson selected)
```
Practice Mode Layout:
├── Back Button (← Back to Lessons)
├── Lesson Header (title + description)
├── Phrase Selector (dropdown menu)
├── Translation Display (2-column)
│   ├── English Original
│   └── Target Language Translation
├── Pronunciation Guide
├── Usage Notes/Cultural Context
├── Audio Controls Section
│   ├── Play Translation Button (🔊)
│   ├── Voice Recording Interface (🎤)
│   └── Audio Analysis Results
└── Interactive Practice (typing exercise)
```

## 4. AI Integration Pipeline

### GeminiLanguageTeacher Class
```python
class GeminiLanguageTeacher:
    def __init__(self, api_key):
        # Initialize Gemini AI model
    
    def get_translation(self, text, target_language):
        # Request translation with context
        # Return: translation, pronunciation, literal, usage_notes
    
    def evaluate_pronunciation(self, user_text, target_text, language):
        # Analyze pronunciation accuracy
        # Return: accuracy_score, feedback, tips, encouragement
```

### Translation Workflow
```
Input: English phrase + target language
    ↓
Gemini AI Prompt Engineering:
    - Request JSON-formatted response
    - Include pronunciation guide
    - Add cultural context/usage notes
    ↓
Response Processing:
    - Parse JSON from AI response
    - Extract key components
    - Handle error fallbacks
    ↓
Output: Structured translation data
```

### Pronunciation Evaluation Pipeline
```
User Audio Input (via audio_recorder_streamlit)
    ↓
Speech-to-Text Conversion:
    - Use SpeechRecognition library
    - Convert to text with target language
    ↓
AI-Powered Analysis:
    - Send user text + target text to Gemini
    - Request structured feedback
    ↓
Fuzzy Matching Fallback:
    - Use fuzzywuzzy for similarity scoring
    - Provide basic accuracy percentage
    ↓
Feedback Display:
    - Score visualization (0-100)
    - Constructive feedback messages
    - Improvement tips
    - Encouragement
```

## 5. Audio Processing Pipeline

### Text-to-Speech (TTS)
```python
def text_to_speech(text, language_code):
    # Use gTTS (Google Text-to-Speech)
    # Generate audio from translated text
    # Return audio bytes for playback
```

### Speech-to-Text (STT)
```python
def speech_to_text(audio_bytes, language_code):
    # Use SpeechRecognition library
    # Convert user audio to text
    # Handle recognition errors gracefully
```

### Audio Recording Workflow
```
User clicks "Record" button
    ↓
audio_recorder_streamlit captures audio
    ↓
Audio bytes stored in session
    ↓
Display audio player for playback
    ↓
Process through STT pipeline
    ↓
Send to AI for pronunciation evaluation
    ↓
Display results and feedback
```

## 6. Accessibility & UI Features

### CSS Theming System
```python
def apply_custom_css():
    # Dynamic CSS generation based on user preferences
    # Support for multiple themes and font sizes
    # Focus indicators for keyboard navigation
    # High contrast mode implementation
```

## 7. Data Flow Summary

```
User Session Start
    ↓
Initialize State & Load Preferences
    ↓
Display Language Selection & Lesson Grid
    ↓
User Selects Lesson → Switch to Practice Mode
    ↓
User Selects Phrase → AI Translation Request
    ↓
Display Translation + Audio Options
    ↓
User Interaction (Audio/Text Practice)
    ↓
AI Evaluation & Feedback
    ↓
Return to Lesson Grid or Continue Practice
```

## 9. Performance Considerations

### Optimization Strategies
- **Session State**: Minimal state storage for performance
- **API Rate Limits**: Graceful handling of Gemini API limitations

### Scalability Factors
- **Curriculum Expansion**: Easy addition of new lessons via CURRICULUM dict
- **Language Addition**: Simple language code mapping in LANGUAGES dict
- **Feature Extension**: Modular component design allows easy feature additions

## 10. Deployment Considerations

### Environment Setup
```bash
# Required environment variables
GEMINI_API_KEY=your_api_key_here

# Dependencies
pip install -r requirements.txt
```
### Streamlit Community Cloud Deployment
- Repository structure optimized for Streamlit deployment
- Secrets management for API keys
