import streamlit as st
import os
from utils import get_answer, text_to_speech, autoplay_audio, speech_to_text
from moodle_api import get_all_course_titles, get_all_course_contents
from audio_recorder_streamlit import audio_recorder
from streamlit_float import *

float_init()

def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hola, soy tu tutor IA. ¿En qué puedo ayudarte?"}
        ]
    if "moodle_context" not in st.session_state:
        st.session_state.moodle_context = ""

initialize_session_state()

st.title("Tutor de Voz IA CUN")

footer_container = st.container()
with footer_container:
    audio_bytes = audio_recorder()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

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

if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Pensando🤔..."):
            if not st.session_state.moodle_context:
                try:
                    titulos = get_all_course_titles()
                    contenidos = get_all_course_contents()
                    st.session_state.moodle_context = f"{titulos}\n\n{contenidos}"
                except Exception as e:
                    st.session_state.moodle_context = f"⚠️ Error al cargar Moodle: {e}"

            with st.expander("📚 Ver contexto cargado desde Moodle"):
                st.text(st.session_state.moodle_context[:1000])

            system_intro = {
                "role": "system",
                "content": (
                    "Eres el Tutor IA de la CUN. Usa los siguientes contenidos reales de Moodle para responder con precisión:\n\n"
                    f"{st.session_state.moodle_context[:5000]}"
                )
            }
            mensajes_ajustados = [system_intro] + st.session_state.messages[-6:]
            final_response = get_answer(mensajes_ajustados)

        with st.spinner("Generando respuesta del audio..."):
            audio_file = text_to_speech(final_response)
            autoplay_audio(audio_file)

        st.write(final_response)
        st.session_state.messages.append({"role": "assistant", "content": final_response})
        os.remove(audio_file)

footer_container.float("bottom: 0rem;")
