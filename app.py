import requests
import os

# URL base de tu Moodle
MOODLE_BASE_URL = "https://ctv.cun.edu.co"
MOODLE_TOKEN = "d5e467b9e41ffd6aeb772e779bff8d36"
MOODLE_URL = f"{MOODLE_BASE_URL}/webservice/rest/server.php"

# Función para llamar funciones REST de Moodle
def call_moodle_function(wsfunction, params):
    all_params = {
        "wstoken": MOODLE_TOKEN,
        "moodlewsrestformat": "json",
        "wsfunction": wsfunction,
    }
    all_params.update(params)
    response = requests.get(MOODLE_URL, params=all_params)
    response.raise_for_status()
    return response.json()

# Obtener el ID de usuario desde su correo
def get_user_id_by_email(email):
    result = call_moodle_function("core_user_get_users", {
        "criteria[0][key]": "email",
        "criteria[0][value]": email
    })
    if "users" in result and result["users"]:
        return result["users"][0]["id"]
    else:
        raise Exception(f"No se encontró usuario con el correo: {email}")

# Obtener cursos en los que el usuario está matriculado
def get_user_courses(user_id):
    result = call_moodle_function("core_enrol_get_users_courses", {
        "userid": user_id
    })
    return result

# Obtener solo los títulos de los cursos en los que está matriculado un usuario (por email)
def get_enrolled_course_titles_by_email(email):
    user_id = get_user_id_by_email(email)
    courses = get_user_courses(user_id)
    return "\n".join([f"- {c['fullname']}" for c in courses])

# Obtener todos los títulos de todos los cursos del sistema
def get_all_course_titles():
    result = call_moodle_function("core_course_get_courses", {})
    return "\n".join([f"- {c['fullname']}" for c in result])

# Obtener contenidos por curso (si existen)
def get_user_course_contents_by_email(email):
    user_id = get_user_id_by_email(email)
    courses = get_user_courses(user_id)
    full_output = ""
    for course in courses:
        course_id = course["id"]
        course_name = course["fullname"]
        contents = call_moodle_function("core_course_get_contents", {
            "courseid": course_id
        })
        if not contents:
            continue
        full_output += f"\n📘 {course_name}:\n"
        for section in contents:
            section_name = section.get("name", "Sin nombre")
            modules = section.get("modules", [])
            full_output += f"  ▪️ {section_name}:\n"
            for module in modules:
                modname = module.get("name", "Recurso sin nombre")
                full_output += f"    - {modname}\n"
    return full_output
