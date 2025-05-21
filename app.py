import os
import streamlit as st
import speech_recognition as sr
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from fpdf import FPDF
from io import BytesIO
from re import match

load_dotenv()

LANGUAGE_CODES = {
    "English": "en-US",
    "Hindi": "hi-IN",
    "Spanish": "es-ES",
    "French": "fr-FR",
    "German": "de-DE",
    "Telugu": "te-IN",
    "Tamil": "ta-IN",
    "Kannada": "kn-IN"
}

st.set_page_config(page_title="AI Voice Resume Builder", page_icon="🎤", layout="wide")

# Inject advanced UI styling
st.markdown("""
    <style>
        .main {
            background: linear-gradient(to right, #e0eafc, #cfdef3);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            color: #2c3e50;
        }

        .stApp {
            background-color: #f5f7fa;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
            padding: 10px;
        }

        .title-container {
            text-align: center;
            padding: 1rem 0;
        }

        .title-container h1 {
            font-size: 2.5rem;
            color: #2c3e50;
        }

        .title-container p {
            font-size: 1.2rem;
            color: #34495e;
        }

        .sidebar-ai-box {
            background-color: #ffffff;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
            font-size: 0.95rem;
        }

        .stButton>button, .stDownloadButton>button {
            background-color: #3498db;
            color: white;
            border-radius: 8px;
            padding: 10px 20px;
            font-weight: 600;
            border: none;
            transition: all 0.3s ease;
        }

        .stButton>button:hover, .stDownloadButton>button:hover {
            background-color: #2c80b4;
            color: #ecf0f1;
        }
    </style>
""", unsafe_allow_html=True)

# Sidebar AI Assistant Box
with st.sidebar:
    st.markdown("<div class='sidebar-ai-box'><h4>🤖 AI Assistant</h4>", unsafe_allow_html=True)
    st.write("Welcome to the AI Voice Resume Builder!\n\nHere's how to use this app:")
    st.markdown("""
    1. Select your **language**.
    2. Click **Start Listening** and speak.
    3. Review and edit the **transcribed text**.
    4. Generate your **AI-powered resume**.
    5. Download the resume as a **PDF**.
    """)
    st.markdown("</div>", unsafe_allow_html=True)

# Main App UI
st.markdown("""
<div class='title-container'>
    <h1>🎤 AI Voice Resume Builder</h1>
    <p>Speak in any language. We'll transcribe and generate a clean one-page resume for you in English!</p>
</div>
""", unsafe_allow_html=True)

selected_language = st.selectbox("🌍 Select your language", list(LANGUAGE_CODES.keys()))
lang_code = LANGUAGE_CODES[selected_language]

if 'is_listening' not in st.session_state:
    st.session_state.is_listening = False
if 'transcript' not in st.session_state:
    st.session_state.transcript = ""
if 'resume_content' not in st.session_state:
    st.session_state.resume_content = ""

col1, col2 = st.columns(2)
with col1:
    if st.button("🎙️ Start Listening"):
        st.session_state.is_listening = True
with col2:
    if st.button("🛑 Stop Listening"):
        st.session_state.is_listening = False

if st.session_state.is_listening:
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.info(f"🎧 Listening in {selected_language}... Speak now.")
        audio = recognizer.listen(source, phrase_time_limit=60)

    try:
        speech_text = recognizer.recognize_google(audio, language=lang_code)
        st.session_state.transcript = speech_text
        st.success("✅ Transcription successful!")
    except sr.UnknownValueError:
        st.error("❌ Could not understand the audio.")
        st.session_state.transcript = ""
    except sr.RequestError:
        st.error("❌ API unavailable or quota exceeded.")
        st.session_state.transcript = ""
    except Exception as e:
        st.error(f"❌ Error: {e}")
        st.session_state.transcript = ""
    finally:
        st.session_state.is_listening = False

if st.session_state.transcript:
    st.markdown("### ✍️ Review/Edit Transcript")
    edited_text = st.text_area("Transcribed Text", st.session_state.transcript, height=150)
    st.session_state.transcript = edited_text

    if edited_text.strip():
        with st.spinner("Generating your resume..."):
            prompt = f"""
You are a professional resume writer.
Create a clean, one-page English resume using the input below.
Include sections: Name, Contact Info, Objective, Skills, Education, Experience, and Projects (if any).
Make assumptions if necessary. Ensure formatting and tone are professional.

Input:
{edited_text}
"""
            try:
                llm = ChatGroq(api_key=os.getenv("GROQ_API_KEY"), model="your_groq_llm")
                response = llm.invoke(prompt)
                content = dict(response)['content']
                st.session_state.resume_content = content
            except Exception as e:
                st.error(f"❌ LLM Error: {e}")

if st.session_state.resume_content:
    st.markdown("### 🧾 Resume Preview")
    st.markdown(f"<div style='white-space: pre-wrap; font-family: Segoe UI; color: #2c3e50;'>{st.session_state.resume_content}</div>", unsafe_allow_html=True)

    pdf = FPDF('P', 'mm', 'A4')
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.set_font("Arial", 'B', 24)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(0, 15, "Resume", ln=True, align="C")
    pdf.ln(1)

    pdf.set_font("Arial", '', 11)
    lines = st.session_state.resume_content.split('\n')
    for line in lines:
        stripped_line = line.strip()

    # Bold headings written in Markdown like **Heading**
        if stripped_line.startswith("**") and stripped_line.endswith("**"):
            clean_text = stripped_line.strip("*")  # Remove ** from both sides
            pdf.set_font("Arial", 'B', 12)
            pdf.multi_cell(190, 6, clean_text)
    # Section headers (e.g., "Experience:", "Education:") — use slightly larger font
        elif stripped_line.endswith(":") or stripped_line.istitle():
            pdf.set_font("Arial", 'B', 12)
            pdf.multi_cell(190, 6, stripped_line)
        else:
            pdf.set_font("Arial", '', 11)
            pdf.multi_cell(190, 6, line)
    buffer = BytesIO()
    buffer.write(pdf.output(dest='S').encode('latin-1'))
    buffer.seek(0)

    st.download_button(             
        label="📅 Download Resume as PDF",
        data=buffer,
        file_name="resume.pdf",
        mime="application/pdf"
    )
