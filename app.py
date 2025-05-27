import streamlit as st
import os
from utils import get_answer, text_to_speech, autoplay_audio, speech_to_text
from moodle_api import get_all_course_titles, get_all_course_contents
from audio_recorder_streamlit import audio_recorder
from streamlit_float import *

# Inicializa visuales flotantes
float_init()

# Estilo, encabezado y componentes visuales
st.markdown("""
    <style>
    header {visibility: hidden;}

    .chat-bubble {
        padding: 14px 20px;
        border-radius: 14px;
        color: white;
        font-family: "Segoe UI", sans-serif;
        margin: 8px 0;
        max-width: 80%;
        word-wrap: break-word;
    }

    .assistant-bubble {
        background: linear-gradient(to right, #0089FF, #3435A1);
        text-align: left;
        margin-right: auto;
        border-top-left-radius: 0;
    }

    .user-bubble {
        background: linear-gradient(to right, #0D192E, #0A2332);
        text-align: right;
        margin-left: auto;
        border-top-right-radius: 0;
    }

    .title-block {
        text-align: center;
        font-family: "Segoe UI", sans-serif;
        margin-top: 10px;
        margin-bottom: 0;
    }

    .title-block h1 {
        margin: 0;
        color: #0089FF;
    }

    div[data-testid="stAudioRecorder"] {
        background-color: red !important;
        border-radius: 50% !important;
        padding: 12px !important;
        display: flex;
        justify-content: center;
        align-items: center;
    }

    div[data-testid="stAudioRecorder"] button {
        background: linear-gradient(135deg, #0089FF, #3435A1) !important;
        border: none !important;
        border-radius: 50% !important;
        width: 65px !important;
        height: 65px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    div[data-testid="stAudioRecorder"] span {
        display: none !important;
    }

    </style>

    <div class='title-block'>
        <h1>Tutor de Voz IA</h1>
        <h1>CUN</h1>
    </div>
    <div style='text-align: center; margin-bottom: 20px;'>
        <img src='https://i.ibb.co/43wVB5D/Cunia.png' width='140' alt='Logo CUN'/>
    </div>
""", unsafe_allow_html=True)

# Estado de la sesión
def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hola, soy tu tutor IA. ¿En qué puedo ayudarte?"}
        ]
    if "moodle_context" not in st.session_state:
        st.session_state.moodle_context = ""

initialize_session_state()

# Micrófono centrado y flotante
footer_container = st.container()
with footer_container:
    audio_bytes = audio_recorder(text=None)
footer_container.float("bottom: 0rem;")

# Mostrar historial del chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        css_class = "assistant-bubble" if message["role"] == "assistant" else "user-bubble"
        st.markdown(f"""
            <div class="chat-bubble {css_class}">
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
                    <div class="chat-bubble user-bubble">
                        {transcript}
                    </div>
                """, unsafe_allow_html=True)
            os.remove(webm_file_path)

# Procesar respuesta del asistente
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            if not st.session_state.moodle_context:
                try:
                    titulos = get_all_course_titles()
                    contenidos = get_all_course_contents()
                    st.session_state.moodle_context = f"{titulos}\n\n{contenidos}"
                except Exception as e:
                    st.session_state.moodle_context = f"No se pudo cargar el contenido desde Moodle: {e}"

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
            <div class="chat-bubble assistant-bubble">
                {final_response}
            </div>
        """, unsafe_allow_html=True)
        st.session_state.messages.append({"role": "assistant", "content": final_response})
        os.remove(audio_file)
