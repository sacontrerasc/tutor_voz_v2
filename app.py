<<<<<<< HEAD
# app.py
import os
import streamlit as st
from utils import get_answer, text_to_speech, autoplay_audio, speech_to_text
from moodle_api import get_user_course_contents_by_email
from audio_recorder_streamlit import audio_recorder
from streamlit_float import float_init
import streamlit.components.v1 as components

float_init()

# --- Estilos CSS ---
st.markdown("""
<style>
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
</style>
""", unsafe_allow_html=True)

# --- Escuchar postMessage para recibir el correo desde Moodle ---
components.html("""
<script>
window.addEventListener("message", (event) => {
    const email = event.data.email;
    if (email) {
        const streamlitDoc = window.parent || window;
        streamlitDoc.postMessage(
            { type: "streamlit:setComponentValue", value: email },
            "*"
        );
    }
});
</script>
""", height=0)

# --- Obtener y guardar correo en session_state ---
if "email" not in st.session_state:
    st.session_state["email"] = ""

# Actualizar si se recibe nuevo email por postMessage
received_email = st.query_params.get("email", None)
if received_email:
    st.session_state["email"] = received_email

email = st.session_state["email"]

# --- Cabecera ---
st.markdown(f"""
<div class='title-block'>
    <h1>CUN</h1>
    <p><b>Tu correo detectado es:</b> {email}</p>
    <img src='https://i.ibb.co/43wVB5D/Cunia.png' width='140' alt='Logo CUN'/>
</div>
""", unsafe_allow_html=True)

# --- Primer mensaje del tutor ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hola, soy tu tutor IA. ¿En qué puedo ayudarte?"}]

# Mostrar mensajes anteriores
for message in st.session_state.messages:
    css_class = "assistant-bubble" if message["role"] == "assistant" else "user-bubble"
    st.markdown(f"<div class='chat-bubble {css_class}'>{message['content']}</div>", unsafe_allow_html=True)

# Micrófono
audio_bytes = audio_recorder(text=None)
st.container().float("bottom: 1rem;")

# Si hay audio, transcribir y responder
if audio_bytes:
    with st.spinner("Transcribiendo..."):
        path = "temp_audio.mp3"
        with open(path, "wb") as f:
            f.write(audio_bytes)
        question = speech_to_text(path)
        os.remove(path)

    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        st.markdown(f"<div class='chat-bubble user-bubble'>{question}</div>", unsafe_allow_html=True)

        # Si la pregunta tiene la palabra "curso"
        if "curso" in question.lower() and "@" in email:
            answer = get_user_course_contents_by_email(email)
        else:
            answer = get_answer(question)

        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.markdown(f"<div class='chat-bubble assistant-bubble'>{answer}</div>", unsafe_allow_html=True)

        # Reproducir audio
        audio_response = text_to_speech(answer)
        autoplay_audio(audio_response)


=======
import os
from flask import Flask, request, jsonify, send_from_directory, render_template
from werkzeug.utils import secure_filename
from utils import get_answer, text_to_speech, speech_to_text
from moodle_api import get_user_course_contents_by_email

app = Flask(__name__)
UPLOAD_FOLDER = "static/audio"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Asegúrate de que la carpeta de audio exista
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/")
def home():
    # Obtener el parámetro "email" desde la URL
    email = request.args.get("email", "usuario@cun.edu.co")  # Valor por defecto
    return render_template("index.html", email=email)

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    message = data.get("message", "")
    email = data.get("email", "")

    if "curso" in message.lower() and "@" in email:
        answer = get_user_course_contents_by_email(email)
    else:
        answer = get_answer(message)

    # Generar audio de la respuesta
    audio_filename = text_to_speech(answer)
    return jsonify({
        "response": answer,
        "audio_url": f"/audio/{audio_filename}"
    })

@app.route("/voice", methods=["POST"])
def voice():
    if "audio" not in request.files:
        return jsonify({"error": "No se envió archivo de audio"}), 400

    file = request.files["audio"]
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    # Transcribir
    question = speech_to_text(filepath)
    os.remove(filepath)

    if not question:
        return jsonify({"error": "No se pudo transcribir"}), 500

    # Generar respuesta
    email = request.form.get("email", "")
    if "curso" in question.lower() and "@" in email:
        answer = get_user_course_contents_by_email(email)
    else:
        answer = get_answer(question)

    audio_filename = text_to_speech(answer)
    return jsonify({
        "question": question,
        "response": answer,
        "audio_url": f"/audio/{audio_filename}"
    })

@app.route("/audio/<filename>")
def audio(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

if __name__ == "__main__":
    app.run(debug=True)
>>>>>>> 0eb274d74e259565b9eb6715ba84687ab12ccf71
