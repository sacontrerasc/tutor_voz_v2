<<<<<<< HEAD
from openai import OpenAI
import os
from dotenv import load_dotenv
import base64
import streamlit as st

# Cargar variables de entorno
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")  # Asegúrate que esté en mayúscula como en Heroku

# Validación de clave
if not api_key:
    raise ValueError("❌ Falta la variable de entorno OPENAI_API_KEY")

# Inicializa el cliente OpenAI
client = OpenAI(api_key=api_key)

# 🔹 Función para obtener respuesta de la IA
def get_answer(messages):
=======
# utils.py
import os
import uuid
from openai import OpenAI
from gtts import gTTS
import speech_recognition as sr

# Inicializa el cliente OpenAI con solo la API Key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_answer(messages):
    if isinstance(messages, str):
        messages = [{"role": "user", "content": messages}]
    
>>>>>>> 0eb274d74e259565b9eb6715ba84687ab12ccf71
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
<<<<<<< HEAD
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ Ocurrió un error al generar la respuesta: {e}"

# 🔊 Transcripción de voz a texto usando Whisper
def speech_to_text(audio_data):
    try:
        with open(audio_data, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                response_format="text",
                file=audio_file
            )
        return transcript
    except Exception as e:
        return f"⚠️ Error en transcripción de audio: {e}"

# 🗣️ Texto a voz con TTS
def text_to_speech(input_text):
    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=input_text
        )
        webm_file_path = "temp_audio_play.mp3"
        with open(webm_file_path, "wb") as f:
            response.stream_to_file(webm_file_path)
        return webm_file_path
    except Exception as e:
        print(f"⚠️ Error en síntesis de voz: {e}")
        return None

# ▶️ Reproduce el audio automáticamente en el navegador
def autoplay_audio(file_path: str):
    if file_path and os.path.exists(file_path):
        with open(file_path, "rb") as f:
            data = f.read()
        b64 = base64.b64encode(data).decode("utf-8")
        md = f"""
        <audio autoplay>
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
        """
        st.markdown(md, unsafe_allow_html=True)
    else:
        st.warning("⚠️ No se pudo reproducir el audio.")
=======
            max_tokens=500
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Ocurrió un error al generar la respuesta: {e}"

def text_to_speech(text, filename=None):
    if not filename:
        filename = f"{uuid.uuid4()}.mp3"

    filepath = os.path.join("static/audio", filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    tts = gTTS(text=text, lang="es")
    tts.save(filepath)

    return filename

def speech_to_text(file_path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(file_path) as source:
        audio = recognizer.record(source)
    try:
        return recognizer.recognize_google(audio, language="es-ES")
    except sr.UnknownValueError:
        return "Lo siento, no pude entender el audio."
    except sr.RequestError as e:
        return f"Error en el reconocimiento de voz: {e}"

>>>>>>> 0eb274d74e259565b9eb6715ba84687ab12ccf71
