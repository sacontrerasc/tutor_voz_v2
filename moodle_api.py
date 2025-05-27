import os
import requests

MOODLE_URL = os.getenv("moodle_url")
MOODLE_TOKEN = os.getenv("moodle_token")

if not MOODLE_URL or not MOODLE_TOKEN:
    raise ValueError("❌ Las variables de entorno 'moodle_url' o 'moodle_token' no están definidas.")

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

def get_all_course_titles():
    try:
        cursos = call_moodle_function("core_course_get_courses")
        if not cursos:
            return "No se encontraron cursos disponibles."
        return "\n".join(f"- {curso['fullname']}" for curso in cursos)
    except Exception as e:
        return f"⚠️ Error al obtener los títulos de los cursos: {e}"

def get_all_course_contents():
    try:
        cursos = call_moodle_function("core_course_get_courses")
    except Exception as e:
        return f"⚠️ Error al obtener la lista de cursos: {e}"

    all_contents = []

    for curso in cursos:
        course_id = curso.get("id")
        course_name = curso.get("fullname", "Sin nombre")
        try:
            secciones = call_moodle_function("core_course_get_contents", {"courseid": course_id})
            for seccion in secciones:
                nombre_sec = seccion.get("name", "")
                for modulo in seccion.get("modules", []):
                    nombre_modulo = modulo.get("name", "")
                    tipo_modulo = modulo.get("modname", "")
                    descripcion = modulo.get("description", "")
                    contenido = f"[{course_name}] {nombre_sec} - {nombre_modulo} ({tipo_modulo})"
                    if descripcion:
                        contenido += f": {descripcion}"
                    all_contents.append(contenido)
        except Exception as e:
            all_contents.append(f"[{course_name}] ❌ Error al cargar contenidos: {e}")

    return "\n".join(all_contents) if all_contents else "No se pudo recuperar contenido detallado desde Moodle."
