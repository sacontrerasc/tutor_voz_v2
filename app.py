import os
import streamlit as st
import streamlit.components.v1 as components
from audio_recorder_streamlit import audio_recorder
from streamlit_float import float_init
from utils import get_answer, text_to_speech, autoplay_audio, speech_to_text
from moodle_api import get_user_course_contents_by_email

float_init()

# ---------- Estilos ----------
st.markdown("""
    <style>
        .chat-container {
            font-family: 'Arial', sans-serif;
            margin-bottom: 20px;
        }
        .user, .bot {
            border-radius: 10px;
            padding: 10px 15px;
            margin: 5px 0;
            max-width: 90%;
        }
        .user {
            background-color: #0f172a;
            color: white;
            text-align: right;
            align-self: flex-end;
        }
        .bot {
            background: linear-gradient(90deg, #0ea5e9, #312e81);
            color: white;
            text-align: left;
            align-self: flex-start;
        }
        .chat-box {
            display: flex;
            flex-direction: column;
        }
        .logo {
            display: block;
            margin: 0 auto;
            width: 180px;
        }
        .avatar {
            border-radius: 50%;
            height: 160px;
            margin: 0 auto 10px auto;
            display: block;
        }
        .email-banner {
            text-align: center;
            margin-bottom: 10px;
            font-weight: bold;
        }
    </style>
""", unsafe_allow_html=True)

# ---------- JavaScript para recibir email ----------
components.html("""
    <script>
    window.addEventListener("message", (event) => {
        const email = event.data.email;
        if (email) {
            const streamlitDoc = window.parent || window;
            streamlitDoc.postMessage({ type: "streamlit:setComponentValue", value: email }, "*");
        }
    });
    </script>
""", height=0)

# ---------- Obtener el email del usuario desde mensaje recibido ----------
if "email" not in st.session_state:
    st.session_state["email"] = ""

email_placeholder = st.text_input("Tu correo detectado es:", value=st.session_state["email"], disabled=True, label_visibility="collapsed")

# Cabecera
st.image("https://i.imgur.com/h8qO5Rf.png", use_column_width=False, width=150)
st.markdown("<h2 style='text-align: center; color: #1e40af;'>CUN</h2>", unsafe_allow_html=True)
st.markdown(f"<div class='email-banner'>Tu correo detectado es: {st.session_state['email']}</div>", unsafe_allow_html=True)
st.image("https://i.imgur.com/tLVo6Q7.png", width=130, class_='avatar')

# Chat inicial
st.markdown("<div class='bot chat-container'>Hola, soy tu tutor IA. ¿En qué puedo ayudarte?</div>", unsafe_allow_html=True)

# Grabación de voz
audio_bytes = audio_recorder(text="🎙️", icon_size="2x", pause_threshold=1.0)

# Procesamiento
if audio_bytes:
    question = speech_to_text(audio_bytes)

    if question:
        st.markdown(f"<div class='user chat-container'>{question}</div>", unsafe_allow_html=True)

        if "curso" in question.lower():
            email = st.session_state["email"]
            if email and "@" in email:
                answer = get_user_course_contents_by_email(email)
            else:
                answer = "⚠️ No se detectó tu correo electrónico. No puedo consultar tus cursos."
        else:
            answer = get_answer(question)

        st.markdown(f"<div class='bot chat-container'>{answer}</div>", unsafe_allow_html=True)
        audio_response = text_to_speech(answer)
        autoplay_audio(audio_response)
    else:
        st.markdown("<div class='bot chat-container'>No entendí tu pregunta. Por favor, intenta de nuevo.</div>", unsafe_allow_html=True)
