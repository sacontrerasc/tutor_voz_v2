# moodle_api.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()

MOODLE_URL = os.getenv("moodle_url")
MOODLE_TOKEN = os.getenv("moodle_token")

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
        raise Exception(f"Error {response.status_code}: {response.text}")

# 🔹 Cargar contenidos de TODOS los cursos
def get_all_course_contents():
    courses = call_moodle_function("core_course_get_courses")

    all_contents = []
    for course in courses:
        course_id = course["id"]
        course_name = course["fullname"]
        try:
            contents = call_moodle_function("core_course_get_contents", {
                "courseid": course_id
            })
            for section in contents:
                section_name = section.get("name", "")
                for mod in section.get("modules", []):
                    mod_name = mod.get("name", "")
                    summary = mod.get("description", "")
                    if summary:
                        all_contents.append(f"[{course_name}] {section_name} - {mod_name}: {summary}")
        except:
            continue

    return "\n".join(all_contents)
