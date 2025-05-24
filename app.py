import streamlit as st
import os
from utils import get_answer, text_to_speech, autoplay_audio, speech_to_text
from moodle_api import get_all_course_titles, get_all_course_contents
from audio_recorder_streamlit import audio_recorder
from streamlit_float import *

# Inicializa visuales flotantes
float_init()

# Encabezado visual oculto y título personalizado
st.markdown("""
    <style>
    header {visibility: hidden;}
    </style>
    <h1 style='text-align: center; color: #0089FF; font-family: "Segoe UI", sans-serif; margin-top: 10px;'>
        Tutor de Voz IA CUN
    </h1>
""", unsafe_allow_html=True)

def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hola, soy tu tutor IA. ¿En qué puedo ayudarte?"}
        ]
    if "moodle_context" not in st.session_state:
        st.session_state.moodle_context = ""

initialize_session_state()

# Micrófono flotante
footer_container = st.container()
with footer_container:
    audio_bytes = audio_recorder()

# Mostrar historial del chat con estilo personalizado
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        color = "#0089FF" if message["role"] == "assistant" else "#0D192E"
        icon = "🤖" if message["role"] == "assistant" else "👤"
        st.markdown(f"""
            <div style='background-color: {color}; padding: 14px 20px; border-radius: 14px;
                        color: white; font-family: "Segoe UI", sans-serif; position: relative;
                        margin: 8px 0;'>
                <span style='position: absolute; left: -30px; font-size: 20px;'>{icon}</span>
                {message["content"]}
            </div>
        """, unsafe_allow_html=True)

# Transcripción del audio del usuario
if audio_bytes:
    with st.spinner("Transcribiendo..."):
        webm_file_path = "temp_audio.mp3"
        with open(webm_file_path, "wb") as f:
            f.write(audio_bytes)
        transcript = speech_to_text(webm_file_path)
        if transcript:
            st.session_state.messages.append({"role": "user", "content": transcript})
            with st.chat_message("user"):
                st.markdown(f"""
                    <div style='background-color: #0D192E; padding: 14px 20px; border-radius: 14px;
                                color: white; font-family: "Segoe UI", sans-serif; position: relative;
                                margin: 8px 0;'>
                        <span style='position: absolute; left: -30px; font-size: 20px;'>👤</span>
                        {transcript}
                    </div>
                """, unsafe_allow_html=True)
            os.remove(webm_file_path)

# Procesar respuesta del asistente
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Pensando 🤖..."):

            if not st.session_state.moodle_context:
                try:
                    titulos = get_all_course_titles()
                    contenidos = get_all_course_contents()
                    st.session_state.moodle_context = f"{titulos}\n\n{contenidos}"
                except Exception as e:
                    st.session_state.moodle_context = f"No se pudo cargar el contenido desde Moodle: {e}"

            with st.expander("📚 Ver contexto cargado desde Moodle"):
                st.text(st.session_state.moodle_context[:1000])

            system_intro = {
                "role": "system",
                "content": (
                    "Eres el Tutor IA de la CUN. Usa la siguiente información real extraída de Moodle "
                    "para responder sobre cursos, recursos (PDF, SCORM, enlaces, libros, páginas, etc):\n\n"
                    f"{st.session_state.moodle_context[:5000]}"
                )
            }

            mensajes_ajustados = [system_intro] + st.session_state.messages[-6:]
            final_response = get_answer(mensajes_ajustados)

        with st.spinner("Generando respuesta en audio..."):
            audio_file = text_to_speech(final_response)
            autoplay_audio(audio_file)

        st.markdown(f"""
            <div style='background-color: #0089FF; padding: 14px 20px; border-radius: 14px;
                        color: white; font-family: "Segoe UI", sans-serif; position: relative;
                        margin: 8px 0;'>
                <span style='position: absolute; left: -30px; font-size: 20px;'>🤖</span>
                {final_response}
            </div>
        """, unsafe_allow_html=True)
        st.session_state.messages.append({"role": "assistant", "content": final_response})
        os.remove(audio_file)

# Posición del micrófono
footer_container.float("bottom: 0rem;")
