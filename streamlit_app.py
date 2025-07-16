import streamlit as st

# --- Page Configuration ---
st.set_page_config(
    page_title="Language Learner",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Header ---
st.title("Language Learner 🎙️")
st.markdown("Learn a new language with our chatbot!")

col1, col2 = st.columns(2)
with col1:
    st.selectbox("Select Target Language", ["Spanish", "French", "German", "Japanese"])
with col2:
    st.toggle("Toggle Dark Mode")


# --- Main Area ---
st.header("Conversation")

# Placeholder for audio player
st.audio("https://www.w3schools.com/html/horse.mp3", format="audio/mpeg")

# Placeholder for microphone button
if st.button("Start Recording"):
    st.write("Recording...")

# Placeholder for transcript display
st.text_area("Transcript", "Bot: Hello! How are you?\nYou: I am fine, thank you.", height=200)


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
col1, col2 = st.columns(2)
with col1:
    st.markdown("Accessibility Controls")
    st.button("High Contrast Mode")
with col2:
    st.markdown("Help & Instructions")
    st.write("Click the microphone to speak. The conversation will appear in the transcript.")