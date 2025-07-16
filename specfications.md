# Language Learner - AI-Powered Language Learning App

Learn a new language with the help of Google's Gemini AI! This Streamlit application provides an interactive, accessible way to learn languages through structured lessons and real-time translations.

**Story behind our app**
  * Many people want to learn a new language but lack interactive tools that are easy to use, especially for elderly users or those with disabilities. Existing apps often focus on reading/writing without sufficient support for speaking practice. Our app aims to provide an interactive audio-based chatbot to help users learn and practice spoken language in real time.
  * Maybe you can also learn some local phrases before your next personal or work trip, so that you can speak confidently!


* **Flowchart**
```
User Input (Text or Audio)
     ↓
[Model: Language Processing & Translation (Gemini Live API)]
     ↓
Audio Output + Visual Feedback (Streamlit UI)
     ↓
User Practices Response
     ↓
Repeat the Cycle / Move on to the Next Lesson
```


## Features
- **13 Supported Languages**: Hebrew, Finnish, French, German, Spanish, Italian, Portuguese, Japanese, Korean, Hindi, Arabic, Bahasa Melayu, Chinese (Mandarin)
- **Structured Curriculum**: Progressive lessons from basic greetings to intermediate conversations
- **Real-time Translation**: Powered by Google Gemini AI
- **Pronunciation Guides**: Phonetic pronunciation for every phrase
- **Interactive Practice**: Test your knowledge with instant feedback
- **Progress Tracking**: Monitor your learning journey
- **Accessibility First**: 
  - Large, easy-to-click buttons
  - Adjustable font sizes
  - Dark mode support
  - Keyboard navigation
  - Screen reader friendly


## Screenshots
<to be added>

### Main Lesson Selection
- Choose from beginner and intermediate lessons
- Track completion status
- See phrase counts for each lesson

### Practice Interface
- Real-time translations
- Pronunciation guides
- Interactive practice with feedback
- Example sentences for context



## Quick Start

### Option 1: Run the Simplified Version (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/KaiquanMah/language-learner.git
   cd language-learner
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements_simple.txt
   ```

3. **Set up your Gemini API key**
   - Get a free API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a `.env` file in the project root:
     ```
     GEMINI_API_KEY=your_api_key_here
     ```

4. **Run the app**
   ```bash
   streamlit run app_simple.py
   ```

### Option 2: Run the Full Version (with Audio Features)

1. **Install all dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Additional setup for audio features**
   - Ensure you have system audio libraries installed
   - On Ubuntu/Debian: `sudo apt-get install python3-pyaudio`
   - On macOS: `brew install portaudio`

3. **Run the full app**
   ```bash
   streamlit run app.py
   ```




## Deployment on Streamlit Community Cloud

1. **Fork this repository** to your GitHub account

2. **Create a Streamlit account** at [streamlit.io](https://streamlit.io)

3. **Deploy the app**:
   - Click "New app" on your Streamlit dashboard
   - Connect your GitHub repository
   - Set the main file path to `app_simple.py`
   - Add your Gemini API key in the Secrets section:
     ```toml
     GEMINI_API_KEY = "your_api_key_here"
     ```

4. **Deploy and share** your app URL!




## ��️ Project Structure

```
language-learner/
├── archive                # folder containing archived builds
├── artifacts              # folder containing terminal workings and screenshots for the assignment report
├── .env                   # API key configuration (create this yourself)
├── .gitignore             # Git ignore file
├── specifications.md      # This file
├── requirements.txt       # Dependencies
├── streamlit_app.py       # Full version with audio features
```



## Curriculum Overview

### Beginner Lessons
1. **Basic Greetings** - Hello, goodbye, introductions
2. **Numbers 1-20** - Learn to count
3. **Daily Phrases** - Common everyday expressions

### Intermediate Lessons
1. **Food & Drink** - Restaurant and cafe vocabulary
2. **Directions** - Asking for and giving directions



## ♿ Accessibility Features

- **Visual**:
  - Adjustable font sizes (small to extra-large)
  - High contrast mode
  - Dark/light theme toggle
  - Clear visual feedback

- **Navigation**:
  - Keyboard-only navigation
  - Tab order optimization
  - Focus indicators
  - Skip links

- **Screen Readers**:
  - Semantic HTML
  - ARIA labels
  - Meaningful button text
  - Progress announcements



## �� Configuration

### Environment Variables
- `GEMINI_API_KEY`: Your Google Gemini API key (required)

### Customization
You can customize the app by modifying:
- `CURRICULUM`: Add or modify lessons
- `LANGUAGES`: Add more language options

**Happy Language Learning! ✨**






# Requirements
**Instructions**
- Please create my web application from the tech stack specified, with the features and satisfy the user stories
- DO NOT create any HTML, TSX files!
- From the specifications in this specfications.md readme file, plan out the steps to create the web app first


**Technology Stack**
- Frontend : Streamlit
- Backend : Python
- Gemini API: [models/gemini-live-2.5-flash-preview](https://ai.google.dev/gemini-api/docs/models#live-api)
- Hosting: Streamlit Community Cloud


**Streamlit User Interface**
- Easy to use
- Engaging visuals, while prioritising accessibility for elderly and people with disabilities who may use the application
  - Accessible for the visually impaired who need to use screen readers and navigate only using a keyboard, or high-contrast mode
  - Large buttons and clear fonts for the elderly
  - Light/dark mode toggle to reduce eye fatigue
- Automatically load the app when the webpage loads
- No login required
- UI Element Suggestions
  1. Header
    - App Title, Target Language Selector, Theme Toggle
  2. Main Area
    - Audio Player
    - Microphone Button
    - Transcript Display
  3. Lesson Panel
    - Progress Tracker
    - Topic Navigator
  4. Footer
    - Accessibility Controls
    - Help & Instructions


**Python Backend and Gemini API**
- Handles any combination of "text or audio" as inputs and outputs
- Manage and track the state of a conversation
- Orchestrate Gemini API calls - [models/gemini-live-2.5-flash-preview](https://ai.google.dev/gemini-api/docs/models#live-api)
- All code and markdown files will be stored in the [GitHub repo](https://github.com/KaiquanMah/language-learner)



**User Stories**
- As a beginner learner, I want to start practicing immediately after opening the app so that I can begin learning without any setup  
- As an elderly user, I want large buttons and readable fonts so that I can easily navigate the interface  
- As a visually impaired user, I want to interact with voice commands and screen reader support so that I can access the app independently  
- As a language learner, I want to **hear native pronunciation of phrases** so that I can improve my accent and comprehension  
- As a user, I want to **receive feedback so that I can know how to improve my speaking skills**
- As a student, I want to follow a s**tructured curriculum** so that I can progress from basic to advanced topics  
- As a non-native speaker, I want to **translate and practice common phrases** so that I can become fluent in daily conversations



Approach 1
- Use [Google AI Studio](https://aistudio.google.com/apps) to build the app

Approach 2
- Use [Gemini CLI](https://github.com/google-gemini/gemini-cli) to build the app


# Gemini CLI Plan
- **Phase 1: Basic UI Setup (in `streamlit_app.py`)**
  - Set up the basic Streamlit page configuration (title, icon).
  - Create the main title and a brief introduction for the app.
  - Implement the layout with placeholders for Header, Main Area, Lesson Panel, and Footer.

- **Phase 2: Implement UI Components (in `streamlit_app.py`)**
  - **Header:**
    - Add a title: "Language Learner".
    - Create a dropdown for language selection (e.g. Hebrew, Finnish, French, Korean, Bahasa Melayu, Bahasa Indonesia, Simplified Chinese, Traditional Chinese).
    - Add a toggle for light/dark mode.
  - **Main Area:**
    - Add an audio player to listen to the chatbot.
    - Implement a microphone button for user input.
    - Create a display area for the conversation transcript.
  - **Lesson Panel:**
    - Add a progress bar for lesson tracking.
    - Create a navigator with a list of topics (eg., Greetings, Numbers).
  - **Footer:**
    - Add a section for accessibility controls.
    - Include a help section with instructions.

- **Phase 3: Backend and Gemini API Integration (in `streamlit_app.py`)**
  - Initialize the Gemini API client to interact with models/gemini-live-2.5-flash-preview
  - Implement the function for real-time conversation, handling audio and text.
  - Implement the translation practice feature.
  - Develop the logic for the progressive curriculum, managing lessons and user progress.
  - Manage conversation state using Streamlit's session state.

- **Phase 4: Refinement and Styling (in `streamlit_app.py`)**
  - Apply styling to improve visual appeal and accessibility (e.g., larger fonts, high-contrast colors).
  - Ensure all interactive elements are keyboard-navigable.
  - Test the application to ensure all features work as expected.