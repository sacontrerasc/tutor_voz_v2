from moodle_api import get_user_courses_by_email

email_estudiante = "tu_correo@cun.edu.co"
respuesta = get_user_courses_by_email(email_estudiante)
print(respuesta)
