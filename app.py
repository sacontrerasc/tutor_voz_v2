import streamlit as st
import os
from utils import get_answer, text_to_speech, autoplay_audio, speech_to_text
from moodle_api import get_all_course_titles, get_user_course_contents_by_email
from audio_recorder_streamlit import audio_recorder
from streamlit_float import float_init

# --- Configuración (solo API Key de OpenAI si es la única variable de entorno) ---
# OPENAI_API_KEY se asume que sigue siendo una variable de entorno
# Puedes añadir una comprobación si es necesaria para OPENAI_API_KEY
# if not os.environ.get("OPENAI_API_KEY"):
#     st.error("Error: La variable de entorno OPENAI_API_KEY no está configurada.")
#     st.stop()

# --- Inicializa visuales flotantes ---
float_init()

# --- Estilo, encabezado y componentes visuales (Tu CSS permanece igual) ---
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


# --- Estado de la sesión ---
def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hola, soy tu tutor IA. ¿En qué puedo ayudarte?"}
        ]
    if "moodle_context" not in st.session_state:
        st.session_state.moodle_context = ""
    # En esta versión, no necesitamos 'user_authenticated' ni la lógica de OAuth2
    # El email se obtiene directamente de la URL
    if "user_email" not in st.session_state:
        st.session_state.user_email = None
    if "moodle_context_loaded" not in st.session_state:
        st.session_state.moodle_context_loaded = False 


initialize_session_state()

# --- Lógica para obtener el email de la URL ---
query_params = st.query_params
# Obtener el email del parámetro 'email' en la URL
user_email_from_url = query_params.get("email")

if user_email_from_url:
    st.session_state.user_email = user_email_from_url
    st.success(f"¡Bienvenido! Usuario: {st.session_state.user_email}")
    # Opcional: Limpiar el parámetro 'email' de la URL después de obtenerlo
    # st.experimental_set_query_params() # Esto borraría todos los query params
else:
    # Si no hay email en la URL, se puede mostrar un mensaje o detener la app
    st.info("Por favor, accede a la aplicación con tu email en la URL (ej: ?email=tu_correo@cun.edu.co).")
    # Puedes detener la ejecución si el email es obligatorio
    # st.stop()


# --- El resto de la aplicación funciona si se ha obtenido el email ---

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
            # Solo cargar el contexto de Moodle si aún no está cargado
            # Aquí la carga del contexto depende de si st.session_state.user_email tiene un valor
            if not st.session_state.moodle_context_loaded and st.session_state.user_email:
                titulos_globales = ""
                contenidos_usuario = ""
                try:
                    titulos_globales = get_all_course_titles()

                    # Usamos el email del usuario obtenido de la URL
                    contenidos_usuario = get_user_course_contents_by_email(st.session_state.user_email)
                    
                    if "⚠️" in contenidos_usuario or "❌" in contenidos_usuario or not contenidos_usuario.strip() or "No se encontró ningún usuario" in contenidos_usuario:
                        st.session_state.moodle_context = (
                            f"Información de Moodle específica del usuario (limitada/error, o usuario no encontrado): {contenidos_usuario}\n\n"
                            f"Contexto general de cursos disponibles en la plataforma:\n{titulos_globales}"
                        )
                    else:
                        st.session_state.moodle_context = (
                            f"Contenido de Moodle relevante para el usuario (validado):\n{contenidos_usuario}\n\n"
                            f"Otros cursos disponibles en la plataforma (no necesariamente del usuario):\n{titulos_globales}"
                        )

                except Exception as e:
                    st.session_state.moodle_context = f"No se pudo cargar el contenido desde Moodle debido a un error: {e}"
                    if not titulos_globales and not contenidos_usuario:
                        st.session_state.moodle_context += "\nNo hay información de Moodle disponible en absoluto."
                
                st.session_state.moodle_context_loaded = True # Marca que el contexto ya fue cargado para esta sesión

            # Definición del rol del sistema para la IA, con instrucciones claras sobre el uso del contexto
            system_intro = {
                "role": "system",
                "content": (
                    "Eres el Tutor IA de la CUN. **Tu principal objetivo es responder preguntas del usuario ÚNICAMENTE con la información proporcionada a continuación, que ha sido extraída directamente de Moodle.**\n\n"
                    "**Considera esta información como la fuente de verdad absoluta para responder sobre los cursos y sus contenidos (PDF, SCORM, enlaces, libros, páginas, etc.).**\n"
                    "**Si el usuario pregunta por 'sus cursos' o 'mis cursos', debes listar los cursos que se mencionan en la sección 'Contenido de Moodle relevante para el usuario'. Si esa sección está vacía o indica un error/usuario no encontrado, informa al usuario que no tienes acceso a esa información específica pero puedes hablar de cursos generales.**\n"
                    "Si la información solicitada no está explícitamente en el contexto de Moodle, indica que no la tienes pero no inventes.\n"
                    "Evita respuestas genéricas sobre privacidad si el contexto ya incluye la información solicitada. ¡Tú ya tienes acceso a esta información para responder al usuario!\n\n"
                    f"**Información de Moodle para responder:**\n{st.session_state.moodle_context[:5000]}"
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