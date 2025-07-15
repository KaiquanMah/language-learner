# Introduction
* **Project Title**: Language Learner - Learn a new language with our chatbot!
* **Problem we want to solve**: Build a simple web application to help people learn a new language.
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




# Requirements
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
- Streamlit app will be hosted on Streamlit Community Cloud


**Features**
1. Real-time conversation
```
User speaks in target language → Gemini processes conversation → Responds in target language via audio and text → App shows text on the user interface
```

2. Translation Practice
```
User reads a passage in English → Gemini translates and speaks in target language → User practices pronunciation
```

3. Progressive Curriculum
```
Users can follow structured lessons (e.g. Greetings → Numbers → Daily Phrases)
Each lesson includes listening, repeating, and responding exercises
Allow user to share where they left off and continue from that topic, else start with some basic lessons again to help user refresh their memory and conversation skills
```


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


