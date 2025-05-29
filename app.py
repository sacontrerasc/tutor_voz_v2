import streamlit as st
import os
from utils import get_answer, text_to_speech, autoplay_audio, speech_to_text
from moodle_api import get_all_course_titles, get_user_course_contents_by_email
from audio_recorder_streamlit import audio_recorder
from streamlit_float import float_init

# Importar Authlib
from authlib.integrations.requests_client import OAuth2Session
import urllib.parse # Para manejar URLs

# --- Configuración de OAuth2 desde Variables de Entorno ---
MOODLE_CLIENT_ID = os.environ.get("MOODLE_CLIENT_ID")
MOODLE_CLIENT_SECRET = os.environ.get("MOODLE_CLIENT_SECRET")
MOODLE_AUTHORIZATION_URL = os.environ.get("MOODLE_AUTHORIZATION_URL")
MOODLE_TOKEN_URL = os.environ.get("MOODLE_TOKEN_URL")
MOODLE_USERINFO_URL = os.environ.get("MOODLE_USERINFO_URL")
MOODLE_REDIRECT_URI = os.environ.get("MOODLE_REDIRECT_URI")

# --- Comprobación de configuración esencial ---
# Se verifica que todas las variables de entorno para OAuth2 estén presentes.
# Si alguna falta, se muestra un mensaje de error y se detiene la aplicación.
if not all([MOODLE_CLIENT_ID, MOODLE_CLIENT_SECRET, MOODLE_AUTHORIZATION_URL,
            MOODLE_TOKEN_URL, MOODLE_USERINFO_URL, MOODLE_REDIRECT_URI]):
    st.error("Error: Las variables de entorno de configuración de Moodle OAuth2 no están completas. Por favor, revisa tus Config Vars en Heroku.")
    st.stop() # Detiene la ejecución si la configuración es incompleta

# --- Inicializa visuales flotantes ---
float_init()

# --- Estilo, encabezado y componentes visuales (Tu CSS permanece igual) ---
# Este bloque contiene el CSS para la apariencia de la interfaz de usuario,
# incluyendo los estilos para las burbujas de chat, el título y el grabador de audio.
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
# Inicializa las variables de estado de la sesión si no existen,
# lo que es crucial para mantener la información a través de las interacciones de Streamlit.
def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hola, soy tu tutor IA. ¿En qué puedo ayudarte?"}
        ]
    if "moodle_context" not in st.session_state:
        st.session_state.moodle_context = ""
    if "user_authenticated" not in st.session_state:
        st.session_state.user_authenticated = False
    if "user_email" not in st.session_state:
        st.session_state.user_email = None
    if "moodle_context_loaded" not in st.session_state:
        st.session_state.moodle_context_loaded = False # Para asegurar que el contexto solo se carga una vez por sesión


initialize_session_state()

# --- Lógica de Autenticación OAuth2 ---
# Esta sección maneja el flujo de autenticación OAuth2 con Moodle.

# 1. Comprobar si hay un código de autorización en la URL (callback de Moodle)
# Cuando Moodle redirige de vuelta a la aplicación después del inicio de sesión,
# incluirá un 'code' en los parámetros de la URL.
query_params = st.query_params
code = query_params.get("code")

if code and not st.session_state.user_authenticated:
    try:
        # Crea una sesión OAuth2 para intercambiar el código por un token de acceso.
        client = OAuth2Session(
            client_id=MOODLE_CLIENT_ID,
            client_secret=MOODLE_CLIENT_SECRET,
            redirect_uri=MOODLE_REDIRECT_URI,
            scope='openid profile email offline_access' # Los ámbitos solicitados a Moodle.
        )
        
        # Intercambia el código de autorización por tokens (access_token, id_token, etc.).
        # 'authorization_response' se usa para que Authlib procese los parámetros de la URL de redirección.
        tokens = client.fetch_token(
            MOODLE_TOKEN_URL,
            authorization_response=st.experimental_get_query_params(), 
            # Si Moodle usa client_secret_post para la autenticación de tokens (es común), podrías necesitar:
            # client_auth_method='client_secret_post'
        )

        # Extrae el email del ID Token si está presente (parte de OpenID Connect).
        user_info = client.parse_id_token(tokens.get('id_token'))
        st.session_state.user_email = user_info.get('email')

        # Si el email no se obtuvo del ID Token, se intenta el endpoint de Userinfo.
        if not st.session_state.user_email and 'access_token' in tokens:
            user_data_response = client.get(MOODLE_USERINFO_URL, token=tokens)
            user_data_response.raise_for_status() # Lanza una excepción para errores HTTP (ej. 404, 500)
            user_data = user_data_response.json()
            st.session_state.user_email = user_data.get('email')

        # Si se obtiene el email, se marca al usuario como autenticado.
        if st.session_state.user_email:
            st.session_state.user_authenticated = True
            st.success(f"¡Autenticado como {st.session_state.user_email}!")
            # Limpia los parámetros de la URL para una URL más limpia y evita re-procesar el código.
            st.query_params.clear() 
            st.rerun() # Fuerza una recarga de la aplicación para mostrar la interfaz completa.
        else:
            st.error("No se pudo obtener el correo electrónico del usuario desde Moodle.")
            st.session_state.user_authenticated = False

    except Exception as e:
        # Manejo de errores durante el proceso de autenticación.
        st.error(f"Error durante la autenticación OAuth2: {e}")
        st.session_state.user_authenticated = False
        st.session_state.user_email = None


# 2. Si el usuario no está autenticado, mostrar botón de inicio de sesión.
# Esta es la interfaz inicial que ve el usuario si no ha iniciado sesión.
if not st.session_state.user_authenticated:
    st.info("Por favor, inicia sesión con tu cuenta de Moodle para obtener información personalizada de tus cursos.")
    
    # Crea la URL de autorización a la que se redirigirá al usuario.
    client = OAuth2Session(
        client_id=MOODLE_CLIENT_ID,
        redirect_uri=MOODLE_REDIRECT_URI,
        scope='openid profile email offline_access'
    )
    authorization_url, state = client.create_authorization_url(MOODLE_AUTHORIZATION_URL)
    
    # Guarda el estado para verificarlo en el callback (medida de seguridad contra CSRF).
    st.session_state.oauth_state = state 

    # Muestra el botón de inicio de sesión.
    st.link_button("Iniciar Sesión con Moodle", authorization_url)
    st.stop() # Detiene la ejecución del resto de la aplicación hasta que el usuario se autentique.

# --- Si el usuario está autenticado, procede con el resto de la aplicación ---
# Este bloque solo se ejecuta si st.session_state.user_authenticated es True.

# Micrófono centrado y flotante
# Configura el grabador de audio para que flote en la parte inferior de la pantalla.
footer_container = st.container()
with footer_container:
    audio_bytes = audio_recorder(text=None)
footer_container.float("bottom: 0rem;")

# Mostrar historial del chat
# Itera sobre los mensajes en el estado de la sesión y los muestra en burbujas de chat.
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        css_class = "assistant-bubble" if message["role"] == "assistant" else "user-bubble"
        st.markdown(f"""
            <div class="chat-bubble {css_class}">
                {message["content"]}
            </div>
        """, unsafe_allow_html=True)

# Transcripción del audio del usuario
# Procesa el audio grabado por el usuario, lo transcribe a texto y lo añade al chat.
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
            os.remove(webm_file_path) # Elimina el archivo de audio temporal.

# Procesar respuesta del asistente
# Genera una respuesta de la IA basada en el historial del chat y el contexto de Moodle.
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            # Solo cargar el contexto de Moodle si aún no está cargado y el usuario está autenticado.
            if not st.session_state.moodle_context_loaded and st.session_state.user_authenticated:
                titulos_globales = ""
                contenidos_usuario = ""
                try:
                    # Obtiene títulos de cursos globales y contenido específico del usuario desde Moodle.
                    titulos_globales = get_all_course_titles()

                    if st.session_state.user_email:
                        contenidos_usuario = get_user_course_contents_by_email(st.session_state.user_email)
                    else:
                        contenidos_usuario = "No se pudo obtener el email del usuario autenticado para buscar contenido específico."

                    # Combina la información de Moodle en un único contexto para la IA.
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
                
                st.session_state.moodle_context_loaded = True # Marca que el contexto ya fue cargado.

            # Define el rol del sistema para la IA, instruyéndola a usar el contexto de Moodle.
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

            # Prepara los mensajes para el modelo de IA, incluyendo la introducción del sistema.
            mensajes_ajustados = [system_intro] + st.session_state.messages[-6:]
            final_response = get_answer(mensajes_ajustados)

        with st.spinner("Generando respuesta en audio..."):
            audio_file = text_to_speech(final_response)
            autoplay_audio(audio_file) # Reproduce la respuesta de audio automáticamente.

        # Muestra la respuesta del asistente en la interfaz de chat.
        st.markdown(f"""
            <div class="chat-bubble assistant-bubble">
                {final_response}
            </div>
        """, unsafe_allow_html=True)
        st.session_state.messages.append({"role": "assistant", "content": final_response})
        os.remove(audio_file) # Elimina el archivo de audio temporal.