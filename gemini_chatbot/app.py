import streamlit as st
import config
# The ONLY line that changed: swap the backend service provider import
from services.gemini_service import get_ai_response_stream, parse_stream_chunks

st.set_page_config(page_title="Gemini Chatbot", page_icon="🤖", layout="centered")

st.title("🤖 Cloud Gemini Chatbot")
st.caption(f"Connected to Google Cloud | Model: **{config.GEMINI_MODEL}**")
st.markdown("---")

# 1. Initialize UI Session State
if "messages" not in st.session_state:
    st.session_state.messages = [
        {'role': 'system', 'content': config.SYSTEM_PROMPT}
    ]

# 2. Render Existing Chat History
for msg in st.session_state.messages:
    if msg['role'] != 'system':
        with st.chat_message(msg['role']):
            st.write(msg['content'])

# 3. Accept User Interaction
if user_input := st.chat_input("Ask Gemini anything..."):
    with st.chat_message("user"):
        st.write(user_input)

    st.session_state.messages.append({'role': 'user', 'content': user_input})

    # 4. Generate AI Response using Service Layer Functions
    with st.chat_message("assistant"):
        try:
            # The service functions are called identically, abstracting the API switch
            raw_stream = get_ai_response_stream(st.session_state.messages)
            clean_text_stream = parse_stream_chunks(raw_stream)

            full_response = st.write_stream(clean_text_stream)
            st.session_state.messages.append({'role': 'assistant', 'content': full_response})

        except Exception as e:
            st.error(f"Cloud API Error: {e}")
