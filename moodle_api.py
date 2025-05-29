import os
import requests
import json # Importar json para pretty print

# Cargar variables de entorno
MOODLE_URL = os.getenv("moodle_url")
MOODLE_TOKEN = os.getenv("moodle_token")

if not MOODLE_URL or not MOODLE_TOKEN:
    # Esto detendrá la aplicación si las variables no están definidas.
    # Asegúrate de que estén configuradas correctamente en tu entorno (ej. .env, Heroku Config Vars).
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
    
    print(f"DEBUG: Llamando a Moodle API: {function_name} con parámetros: {all_params}") # DEBUG
    
    try:
        response = requests.get(MOODLE_URL, params=all_params)
        response.raise_for_status() # Lanza una excepción para códigos de estado HTTP 4xx/5xx
        
        data = response.json()
        print(f"DEBUG: Respuesta de Moodle API para {function_name}: {json.dumps(data, indent=2)}") # DEBUG
        
        # Moodle a veces devuelve errores en el cuerpo JSON con status 200
        if isinstance(data, dict) and 'exception' in data:
            error_message = data.get('message', 'Error desconocido de Moodle API')
            raise Exception(f"🔴 Error de Moodle API para {function_name}: {error_message} (Código: {data.get('errorcode', 'N/A')})")

        return data
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Error de conexión/HTTP al llamar a Moodle API ({function_name}): {e}") # DEBUG
        raise Exception(f"🔴 Error de conexión o HTTP al llamar a Moodle: {e}")
    except json.JSONDecodeError as e:
        print(f"ERROR: Error al decodificar JSON de Moodle API ({function_name}): {e}. Respuesta: {response.text}") # DEBUG
        raise Exception(f"🔴 Error al procesar la respuesta JSON de Moodle: {e}")
    except Exception as e:
        print(f"ERROR: Error inesperado al llamar a Moodle API ({function_name}): {e}") # DEBUG
        raise Exception(f"🔴 Error inesperado al llamar a Moodle: {e}")


# 🔹 Títulos de todos los cursos
def get_all_course_titles():
    try:
        cursos = call_moodle_function("core_course_get_courses")
        if not cursos:
            print("DEBUG: No se encontraron cursos al obtener títulos.") # DEBUG
            return "No se encontraron cursos disponibles en la plataforma."
        
        titulos = "\n".join(f"- {curso['fullname']}" for curso in cursos)
        print(f"DEBUG: Títulos de cursos obtenidos: \n{titulos}") # DEBUG
        return titulos
    except Exception as e:
        print(f"ERROR: Fallo al obtener títulos de cursos: {e}") # DEBUG
        return f"⚠️ Error al obtener los títulos de los cursos generales: {e}"

# 🔹 Contenidos de todos los cursos (esta función no se usa actualmente en app.py, pero la mantengo)
def get_all_course_contents():
    try:
        cursos = call_moodle_function("core_course_get_courses")
    except Exception as e:
        print(f"ERROR: Fallo al obtener la lista de cursos para todos los contenidos: {e}") # DEBUG
        return f"⚠️ Error al obtener la lista de cursos para contenido general: {e}"

    all_contents = []

    for curso in cursos:
        course_id = curso.get("id")
        course_name = curso.get("fullname", "Sin nombre")
        try:
            secciones = call_moodle_function("core_course_get_contents", {"courseid": course_id})
            # Lógica de formateo de contenido (duplicada, considerar refactorizar)
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
            print(f"ERROR: Fallo al cargar contenidos para el curso {course_name} (ID: {course_id}): {e}") # DEBUG
            all_contents.append(f"[{course_name}] ❌ Error específico al cargar contenidos: {e}")

    return "\n".join(all_contents) if all_contents else "No se pudo recuperar contenido detallado general desde Moodle."

# 🔹 Contenidos completos de los cursos del usuario por email
def get_user_course_contents_by_email(email):
    print(f"DEBUG: Intentando obtener contenidos para el email: {email}") # DEBUG
    try:
        # Paso 1: Obtener el usuario por email
        users_response = call_moodle_function("core_user_get_users", {
            "criteria[0][key]": "email",
            "criteria[0][value]": email
        })

        if not users_response or not isinstance(users_response, dict) or not users_response.get('users'):
            print(f"DEBUG: No se encontró ningún usuario con el email '{email}'. Respuesta: {users_response}") # DEBUG
            return "⚠️ No se encontró ningún usuario con ese correo electrónico en Moodle."

        user_id = users_response['users'][0]["id"]
        print(f"DEBUG: Usuario encontrado: ID={user_id}, Email={email}") # DEBUG

        # Paso 2: Obtener los cursos en los que el usuario está matriculado
        cursos_usuario = call_moodle_function("core_enrol_get_users_courses", {"userid": user_id})

        if not cursos_usuario:
            print(f"DEBUG: El usuario {user_id} no está matriculado en ningún curso.") # DEBUG
            return "⚠️ No estás matriculado en ningún curso en Moodle."

        print(f"DEBUG: Cursos matriculados para el usuario {user_id}: {len(cursos_usuario)} cursos.") # DEBUG

        all_contents = []

        # Paso 3: Obtener el contenido de cada curso matriculado
        for curso in cursos_usuario:
            course_id = curso.get("id")
            course_name = curso.get("fullname", "Sin nombre")
            print(f"DEBUG: Procesando curso: {course_name} (ID: {course_id})") # DEBUG
            try:
                secciones = call_moodle_function("core_course_get_contents", {"courseid": course_id})
                if not secciones:
                    print(f"DEBUG: Curso {course_name} (ID: {course_id}) no tiene secciones o contenido.") # DEBUG
                    all_contents.append(f"[{course_name}] No hay contenido detallado disponible.")
                    continue # Pasar al siguiente curso si no hay secciones

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
                print(f"ERROR: Fallo al cargar contenidos para el curso {course_name} (ID: {course_id}): {e}") # DEBUG
                all_contents.append(f"[{course_name}] ❌ Error al cargar contenidos: {e}")

        final_result = "\n".join(all_contents) if all_contents else "No se pudo recuperar contenido detallado específico del usuario desde Moodle."
        print(f"DEBUG: Contenido final del usuario:\n{final_result}") # DEBUG
        return final_result

    except Exception as e:
        print(f"ERROR: Fallo general en get_user_course_contents_by_email para {email}: {e}") # DEBUG
        return f"❌ Error general al obtener contenidos del usuario: {e}. Por favor, verifica el email y los permisos."

