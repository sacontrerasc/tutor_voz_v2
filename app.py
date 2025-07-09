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
