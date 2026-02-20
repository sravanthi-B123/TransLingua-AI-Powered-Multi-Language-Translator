from dotenv import load_dotenv
import streamlit as st
import os
try:
    import google.generativeai as genai
    from google.api_core import exceptions as api_exceptions
except Exception:
    genai = None
    st.error("Missing 'google-generative-ai' package. Install it with: pip install google-generative-ai")
    st.stop()

# Load environment variables
load_dotenv()

# Read API key from environment (can be overridden in the UI)
api_key_env = os.getenv("GOOGLE_API_KEY", "")

# Store API key in session state so the UI can update it at runtime
if "api_key" not in st.session_state:
    st.session_state.api_key = api_key_env

st.sidebar.header("Google API Key")
api_input = st.sidebar.text_input("Paste Google API Key (keeps in session only)", value=st.session_state.api_key, type="password")
def test_api_key(key: str) -> tuple[bool, str]:
    """Quickly validate an API key by attempting a tiny generation.

    Returns (ok, message). Does not raise.
    """
    try:
        genai.configure(api_key=key)
        test_model = genai.GenerativeModel("gemini-2.5-flash")
        # Small test prompt that should be fast and cheap
        resp = test_model.generate_content("Hello")
        # If we get a response object with text, treat as success
        if getattr(resp, "text", None):
            return True, "Key valid"
        return True, "Key appears valid"
    except api_exceptions.PermissionDenied as e:
        return False, f"PermissionDenied: {e}"
    except api_exceptions.InvalidArgument as e:
        return False, f"InvalidArgument: {e}"
    except Exception as e:
        # Generic failure — treat as invalid for safety
        return False, f"Error testing key: {e}"

if st.sidebar.button("Set API Key"):
    ok, msg = test_api_key(api_input)
    if ok:
        st.session_state.api_key = api_input
        genai.configure(api_key=st.session_state.api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        st.sidebar.success("API key set and validated.")
    else:
        st.sidebar.error(f"API key rejected: {msg}")
        # Clear any stored (possibly blocked) key to avoid repeated errors
        st.session_state.api_key = ""

if not st.session_state.api_key:
    st.sidebar.warning("No API key configured. Paste a valid key here or set GOOGLE_API_KEY in a .env file.")

# Configure the client with the (possibly updated) API key
if st.session_state.api_key:
    genai.configure(api_key=st.session_state.api_key)
    # Initialize model after configuring API key
    model = genai.GenerativeModel("gemini-2.5-flash")
else:
    model = None
    

# Translation function
def translate_text(text, source_language, target_language):
    prompt = f"Translate the following text from {source_language} to {target_language}: {text}"
    try:
        response = model.generate_content(prompt)
        return response.text
    except api_exceptions.PermissionDenied as e:
        st.error("API key blocked or reported leaked. Create a new key in Google Cloud Console and update GOOGLE_API_KEY.")
        return f"Error: API key blocked (PermissionDenied). {str(e)}"
    except api_exceptions.InvalidArgument as e:
        st.error("Invalid API key. Check your GOOGLE_API_KEY value.")
        return f"Error: InvalidArgument. {str(e)}"
    except Exception as e:
        st.error("An unexpected error occurred while calling the Google Generative API.")
        return f"Error: {str(e)}"

# Streamlit UI
st.set_page_config(page_title="AI-Powered Language Translator", page_icon="🌍")
st.header("🌍 AI-Powered Language Translator")

text = st.text_area("📝 Enter text to translate:")
source_language = st.selectbox(
    "🌐 Select source language:",
    ["English", "Telugu", "Hindi", "Spanish", "French", "German", "Chinese"]
)

target_language = st.selectbox(
    "🎯 Select target language:",
    ["English", "Telugu", "Hindi", "Spanish", "French", "German", "Chinese"]
)

if st.button("🔁 Translate"):
    if text:
        translated_text = translate_text(text, source_language, target_language)
        st.subheader("📘 Translated Text:")
        st.write(translated_text)
    else:
        st.warning("⚠️ Please enter text to translate")
