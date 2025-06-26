 
import sqlite3
import os

DATABASE_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'soporte_db.db')

def get_db_connection():
    """Establece y retorna una conexión a la base de datos SQLite."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row # Permite acceder a las columnas por nombre
    return conn

def get_parameter(key: str) -> str | None:
    """
    Obtiene el valor de un parámetro de la tabla 'parametros_seteos' por su clave.
    Retorna None si la clave no existe.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT valor FROM parametros_seteos WHERE clave = ?", (key,))
        result = cursor.fetchone()
        return result['valor'] if result else None
    except sqlite3.Error as e:
        print(f"Error al leer parámetro '{key}' de la base de datos: {e}")
        return None
    finally:
        if conn:
            conn.close()

def set_parameter(key: str, value: str, description: str = None) -> bool:
    """
    Inserta o actualiza un parámetro en la tabla 'parametros_seteos'.
    Retorna True si la operación fue exitosa, False en caso contrario.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO parametros_seteos (clave, valor, descripcion) VALUES (?, ?, ?)",
            (key, value, description)
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error al establecer parámetro '{key}': {e}")
        return False
    finally:
        if conn:
            conn.close()

# Ejemplo de uso (puedes ejecutar este archivo para probar las funciones)
if __name__ == "__main__":
    # Asegúrate de que tu DB esté en bot-ansv/data/soporte_db.db
    # Si ejecutas este archivo directamente, su directorio padre es utils,
    # por eso el path '../data/soporte_db.db'
    print(f"Intentando conectar a DB en: {DATABASE_NAME}")

    # Probar obtener parámetros
    org_name = get_parameter('ORG_NOMBRE')
    print(f"Nombre de la Organización: {org_name}")

    bot_port = get_parameter('BOT_PORT')
    print(f"Puerto del Bot: {bot_port}")

    # Probar establecer/actualizar un parámetro
    if set_parameter('BOT_PORT', '8851', 'Nuevo puerto de prueba'):
        print("Puerto del Bot actualizado a 8851.")
        print(f"Puerto del Bot (después de actualizar): {get_parameter('BOT_PORT')}")
    else:
        print("Fallo al actualizar el puerto.")

    # Probar un parámetro que no existe
    non_existent_param = get_parameter('PARAMETRO_INEXISTENTE')
    print(f"Parámetro inexistente: {non_existent_param}")