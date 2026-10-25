"""
FUNCIONES:
- Verificar integridad de los datos
- Respaldar datos con un ZIP
- Obtener información del sistema

para verificar la integridad, debe de utilizarse el hash SHA-256 y compararlo con el hash previo de los datos (se debe guardar en datos.sha256)
si se actualiza la información, se actualiza el hash
si no coincide la verificación de integridad, se da un aviso al usuario

para la información del sistema, deben verse los metadatos del archivo (fecha creación, permisos, tamaño...)


"""