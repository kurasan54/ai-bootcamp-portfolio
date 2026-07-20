from google import genai
from google.genai import types
import config

# Initialize the official Gemini Client using the key from config
client = genai.Client(api_key=config.GEMINI_API_KEY)

def _convert_to_gemini_contents(messages):
    """
    Helper Function (Internal):
    Translates standard chat history dictionaries into the specific
    Content types required by the google-genai SDK.
    """
    formatted_contents = []

    for msg in messages:
        # Skip system messages since system instructions are passed separately in config
        if msg['role'] == 'system':
            continue

        # Map roles: Streamlit uses 'assistant', Gemini uses 'model'
        gemini_role = "model" if msg['role'] == "assistant" else "user"

        # Build the structured content object required by the SDK
        content_obj = types.Content(
            role=gemini_role,
            parts=[types.Part.from_text(text=msg['content'])]
        )
        formatted_contents.append(content_obj)

    return formatted_contents

def get_ai_response_stream(messages):
    """
    Sends the message history to the Gemini cloud API.
    Returns a live text stream chunking back from Google servers.
    """
    # 1. Transform the message history format
    gemini_payload = _convert_to_gemini_contents(messages)

    # 2. Inject the system instructions via GenerateContentConfig
    api_config = types.GenerateContentConfig(
        system_instruction=config.SYSTEM_PROMPT
    )

    # 3. Call the cloud streaming service
    return client.models.generate_content_stream(
        model=config.GEMINI_MODEL,
        contents=gemini_payload,
        config=api_config
    )

def parse_stream_chunks(raw_stream):
    """
    A generator function that cleanly extracts text from Gemini's response chunks.
    """
    for chunk in raw_stream:
        # Extract the text string property from the current stream packet
        if chunk.text:
            yield chunk.text
