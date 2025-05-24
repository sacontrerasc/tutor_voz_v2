from moodle_api import call_moodle_function

cursos = call_moodle_function("core_course_get_courses")

for curso in cursos:
    print(f"{curso['id']}: {curso['fullname']}")
