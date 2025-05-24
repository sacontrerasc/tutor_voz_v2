# moodle_api.py
import os
import requests

# Leer variables desde entorno de Heroku o local
MOODLE_URL = os.getenv("moodle_url")
MOODLE_TOKEN = os.getenv("moodle_token")

if not MOODLE_URL or not MOODLE_TOKEN:
    raise ValueError("❌ Las variables de entorno 'moodle_url' o 'moodle_token' no están definidas.")

# 🔧 Función base para llamar cualquier función de Moodle
def call_moodle_function(function_name, params=None):
    if params is None:
        params = {}
    base_params = {
        "wstoken": MOODLE_TOKEN,
        "moodlewsrestformat": "json",
        "wsfunction": function_name,
    }
    all_params = {**base_params, **params}
    response = requests.get(MOODLE_URL, params=all_params)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"🔴 Error {response.status_code} al llamar a Moodle: {response.text}")

# 📘 Obtener todos los títulos de cursos
def get_all_course_titles():
    try:
        cursos = call_moodle_function("core_course_get_courses")
        if not cursos:
            return "No se encontraron cursos disponibles."
        return "\n".join(f"- {curso['fullname']}" for curso in cursos)
    except Exception as e:
        return f"⚠️ Error al obtener los títulos de los cursos: {e}"

# 📚 Obtener todos los contenidos de los cursos (incluso vacíos o sin descripción)
def get_all_course_contents():
    try:
        cursos = call_moodle_function("core_course_get_courses")
    except Exception as e:
        return f"⚠️ Error al obtener la lista de cursos: {e}"

    all_contents = []

    for curso in cursos:
        course_id = curso.ge_

