import streamlit as st
import os
import google.generativeai as genai
from dotenv import load_dotenv
import asyncio
from google.generativeai.types import content_types

# Load environment variables from .env file
load_dotenv()

# --- Page Configuration ---
st.set_page_config(
    page_title="Language Learner",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Gemini API Configuration ---
try:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.error("GEMINI_API_KEY not found. Please set it in your .env file.")
    else:
        genai.configure(api_key=api_key)
except Exception as e:
    st.error(f"Error configuring Gemini API: {e}")

# --- Main App ---
async def main():
    st.title("Language Learner 🎙️")
    st.markdown("Learn a new language with our chatbot!")

    col1, col2 = st.columns(2)
    with col1:
        language = st.selectbox("Select Target Language", ["Hebrew", "Finnish", "French", "Korean", "Bahasa Melayu", "Bahasa Indonesia", "Simplified Chinese", "Traditional Chinese"])
    with col2:
        st.toggle("Toggle Dark Mode")

    st.header("Conversation")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # React to user input
    if prompt := st.chat_input("What would you like to practice?"):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        try:
            async with genai.live.AsyncLiveClient(model_name='gemini-live-2.5-flash-preview') as client:
                await client.send(content_types.to_content(f"You are a language tutor. The user wants to learn {language}. Respond to the user's message: {prompt}"))
                
                response_text = ""
                with st.chat_message("assistant"):
                    message_placeholder = st.empty()
                    async for chunk in client:
                        if chunk.text:
                            response_text += chunk.text
                            message_placeholder.markdown(response_text + "▌")
                    message_placeholder.markdown(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text})

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
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("Accessibility Controls")
        st.button("High Contrast Mode")
    with col2:
        st.markdown("Help & Instructions")
        st.write("Type your message in the box below and press Enter to chat with the language tutor.")

if __name__ == "__main__":
    asyncio.run(main())