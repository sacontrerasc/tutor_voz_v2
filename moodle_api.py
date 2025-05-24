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
                    tipo = modulo.get("modname", "tipo desconocido")
                    descripcion = modulo.get("description", "")
                    archivo_url = None

                    # Si el módulo tiene archivos o enlaces
                    contents = modulo.get("contents", [])
                    for c in contents:
                        if c.get("fileurl"):
                            archivo_url = c["fileurl"].split('?')[0]
                            break

                    resumen = f"[{course_name}] {nombre_sec} - {nombre_modulo} ({tipo})"
                    if descripcion:
                        resumen += f": {descripcion}"
                    if archivo_url:
                        resumen += f" ➜ Recurso: {archivo_url}"

                    all_contents.append(resumen)
        except Exception as e:
            all_contents.append(f"[{course_name}] ❌ Error al cargar contenidos: {e}")

    return "\n".join(all_contents) if all_contents else "No se encontró contenido detallado desde Moodle."
