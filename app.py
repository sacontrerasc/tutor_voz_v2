import streamlit as st
import os
from utils import get_answer, text_to_speech, autoplay_audio, speech_to_text
from moodle_api import get_user_courses_by_email, get_all_course_contents_by_email
from audio_recorder_streamlit import audio_recorder
from streamlit_float import *

# Inicializa elementos flotantes
float_init()

def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "¿Cómo puedo ayudarte hoy?"}
        ]
    if "user_email" not in st.session_state:
        st.session_state.user_email = ""

initialize_session_state()

st.title("Tutor de Voz IA CUN")

# Captura automática desde URL si se pasa por ?email=
query_params = st.experimental_get_query_params()
if "email" in query_params and not st.session_state.user_email:
    st.session_state.user_email = query_params["email"][0]

# Campo editable por si no llega desde la URL
if not st.session_state.user_email:
    st.text_input("Ingresa tu correo institucional CUN:", key="user_email")

# Micrófono en el footer
footer_container = st.container()
with footer_container:
    audio_bytes = audio_recorder()

# Mostrar el historial del chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Si hay audio, transcribe y agrega como mensaje del usuario
if audio_bytes:
    with st.spinner("Transcribiendo..."):
        webm_file_path = "temp_audio.mp3"
        with open(webm_file_path, "wb") as f:
            f.write(audio_bytes)
        transcript = speech_to_text(webm_file_path)
        if transcript:
            st.session_state.messages.append({"role": "user", "content": transcript})
            with st.chat_message("user"):
                st.write(transcript)
            os.remove(webm_file_path)

# Procesar si el último mensaje fue del usuario
if st.session_state.messages[-1]["role"] != "assistant":
    last_user_message = st.session_state.messages[-1]["content"].lower()
    with st.chat_message("assistant"):
        with st.spinner("Pensando🤔..."):

            # Si el usuario pregunta por sus cursos
            if (
                "qué cursos tengo" in last_user_message
                or "estoy inscrito" in last_user_message
            ) and st.session_state.user_email:
                final_response = get_user_courses_by_email(st.session_state.user_email)

            # Si se pregunta algo general y hay correo → IA con contexto
            elif st.session_state.user_email:
                moodle_context = get_all_course_contents_by_email(st.session_state.user_email)
                system_intro = {
                    "role": "system",
                    "content": f"Eres el Tutor IA de la CUN. Usa los siguientes contenidos reales de Moodle para responder preguntas:\n\n{moodle_context[:5000]}"
                }
                final_response = get_answer([system_intro] + st.session_state.messages)
            
            # Si no hay correo, responde sin contexto
            else:
                final_response = get_answer(st.session_state.messages)

        with st.spinner("Generando respuesta del audio..."):
            audio_file = text_to_speech(final_response)
            autoplay_audio(audio_file)

        st.write(final_response)
        st.session_state.messages.append({"role": "assistant", "content": final_response})
        os.remove(audio_file)

# Flotar el micrófono en el fondo
footer_container.float("bottom: 0rem;")
