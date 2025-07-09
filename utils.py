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
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
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

