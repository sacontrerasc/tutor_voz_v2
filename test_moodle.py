import requests

MOODLE_URL = "https://ctv.cun.edu.co/webservice/rest/server.php"
TOKEN = "d5e467b9e41ffd6aeb772e779bff8d36"
EMAIL = "admin_ctv@cun.edu.co"

def call_moodle_function(function_name, params=None):
    if params is None:
        params = {}
    base_params = {
        "wstoken": TOKEN,
        "moodlewsrestformat": "json",
        "wsfunction": function_name,
    }
    all_params = {**base_params, **params}
    response = requests.get(MOODLE_URL, params=all_params)
    response.raise_for_status()
    return response.json()

def get_user_id_by_email(email):
    result = call_moodle_function("core_user_get_users", {
        "criteria[0][key]": "email",
        "criteria[0][value]": email
    })
    if result["users"]:
        return result["users"][0]["id"]
    return None

def get_user_courses(user_id):
    result = call_moodle_function("core_enrol_get_users_courses", {
        "userid": user_id
    })
    return result

if __name__ == "__main__":
    user_id = get_user_id_by_email(EMAIL)
    if user_id:
        print(f"✅ ID del usuario {EMAIL}: {user_id}")
        cursos = get_user_courses(user_id)
        if cursos:
            print("📚 Cursos matriculados:")
            for curso in cursos:
                print(f"- {curso['fullname']} ({curso['shortname']})")
        else:
            print("⚠️ El usuario no está matriculado en ningún curso.")
    else:
        print(f"❌ No se encontró el usuario con correo: {EMAIL}")

