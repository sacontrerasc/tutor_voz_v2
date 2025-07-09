# moodle_api.py
import os
import requests

# Cargar variables de entorno
MOODLE_URL = os.getenv("moodle_url")
MOODLE_TOKEN = os.getenv("moodle_token")

if not MOODLE_URL or not MOODLE_TOKEN:
    raise ValueError("❌ Las variables de entorno 'moodle_url' o 'moodle_token' no están definidas.")

# Función genérica para llamar funciones de la API de Moodle
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

# 🔹 Obtener títulos de todos los cursos
def get_all_course_titles():
    try:
        cursos = call_moodle_function("core_course_get_courses")
        if not cursos:
            return "No se encontraron cursos disponibles."
        return "\n".join(f"- {curso['fullname']}" for curso in cursos)
    except Exception as e:
        return f"⚠️ Error al obtener los títulos de los cursos: {e}"

# 🔹 Obtener contenidos solo de los cursos del usuario autenticado por email (formato ordenado y claro)
def get_user_course_contents_by_email(email):
    try:
        result = call_moodle_function("core_user_get_users", {
            "criteria[0][key]": "email",
            "criteria[0][value]": email
        })

        users = result.get("users", [])
        if not users:
            return f"⚠️ No se encontró ningún usuario con el correo {email}."

        user_id = users[0]["id"]
        cursos = call_moodle_function("core_enrol_get_users_courses", {"userid": user_id})
        if not cursos:
            return f"⚠️ El usuario con correo {email} no está matriculado en ningún curso."

        respuesta = ""

        for curso in cursos:
            course_id = curso.get("id")
            course_name = curso.get("fullname", "Sin nombre")
            respuesta += f"\n📚 *{course_name}*\n"
            try:
                secciones = call_moodle_function("core_course_get_contents", {"courseid": course_id})
                for seccion in secciones:
                    for modulo in seccion.get("modules", []):
                        nombre = modulo.get("name", "Sin título")
                        tipo = modulo.get("modname", "otro").lower()

                        # Asignar icono según tipo de recurso
                        if tipo == "url":
                            icono = "🔗"
                        elif tipo == "resource":
                            icono = "📄"
                        elif tipo == "forum":
                            icono = "💬"
                        elif tipo == "scorm":
                            icono = "🎓"
                        elif tipo == "page":
                            icono = "📘"
                        elif "práctica" in nombre.lower():
                            icono = "🎯"
                        else:
                            icono = "📎"

                        respuesta += f"• {icono} {nombre} ({tipo})\n"

            except Exception as e:
                respuesta += f"❌ Error al cargar contenidos: {e}\n"

        return respuesta.strip() if respuesta.strip() else "No se pudo recuperar contenido detallado desde Moodle."

    except Exception as e:
        return f"❌ Error al obtener contenidos del usuario: {e}"
