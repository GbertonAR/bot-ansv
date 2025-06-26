# bot/services/db_services.py

import sqlite3
import os
import logging
import traceback

# No longer using logging.basicConfig here. Logging is configured in app.py.

# Obtener la ruta del directorio raíz del proyecto (bot-ansv)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Construir la ruta a la base de datos desde la raíz del proyecto
DB_PATH = os.path.join(PROJECT_ROOT, "data", "soporte_db.db")

print(f"DEBUG_DB: Ruta de la base de datos: {DB_PATH}")

def connect_db():
    """Establece una conexión a la base de datos."""
    return sqlite3.connect(DB_PATH)

def init_db():
    """Inicializa la base de datos y crea las tablas si no existen."""
    conn = None
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS parametros_seteos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre_parametro TEXT NOT NULL UNIQUE,
                valor TEXT
            )
        """)
        conn.commit()
        logging.info(f"Base de datos y tabla 'parametros_seteos' inicializadas en: {DB_PATH}")
    except sqlite3.Error as e:
        logging.error(f"Error al inicializar la base de datos: {e}")
        traceback.print_exc()
    finally:
        if conn:
            conn.close()

def populate_initial_parameters():
    """
    Puebla la tabla de parámetros con valores iniciales si no existen.
    Se ejecuta solo INSERT OR IGNORE para no sobrescribir datos existentes.
    """
    conn = None
    try:
        conn = connect_db()
        cursor = conn.cursor()
        logging.info("DEBUG_DB: Intentando poblar parámetros iniciales...")

        initial_params = {
            "AZURE_OPENAI_API_KEY": "TU_AZURE_OPENAI_API_KEY", # ¡IMPORTANTE! Reemplazar con tu clave real
            "AZURE_OPENAI_ENDPOINT": "TU_AZURE_OPENAI_ENDPOINT", # ¡IMPORTANTE! Reemplazar con tu endpoint real
            "AZURE_OPENAI_DEPLOYMENT_NAME": "TU_MODELO_CHAT_DEPLOYMENT_NAME", # ¡IMPORTANTE! Reemplazar
            "EMAIL_USERNAME": "tu_email@gmail.com",
            "EMAIL_PASSWORD": "tu_password_app", # Usar contraseña de aplicación si es Gmail
            "EMAIL_SENDER": "smtp.gmail.com",
            "EMAIL_PORT": "587",
            "DIRECT_LINE_SECRET": "TU_DIRECT_LINE_SECRET", # ¡IMPORTANTE! Reemplazar
            "MicrosoftAppId": "", # Puede estar vacío si usas Direct Line secret
            "MicrosoftAppPassword": "", # Puede estar vacío si usas Direct Line secret
            "ORGANIZACION": "Agencia Nacional de Seguridad Vial (ANSV)",
            "EMAIL_ORG": "contacto@ansv.gob.ar",
            # Agrega más parámetros según sea necesario
        }

        for nombre, valor in initial_params.items():
            cursor.execute("INSERT OR IGNORE INTO parametros_seteos (nombre_parametro, valor) VALUES (?, ?)", (nombre, valor))
        conn.commit()
        logging.info("DEBUG_DB: Parámetros iniciales poblados/verificados.")
    except sqlite3.Error as e:
        logging.error(f"Error al poblar parámetros iniciales: {e}")
        traceback.print_exc()
    finally:
        if conn:
            conn.close()

def load_all_bot_parameters():
    """Carga todos los parámetros del bot desde la base de datos en un diccionario."""
    conn = None
    parameters = {}
    try:
        conn = connect_db()
        cursor = conn.cursor()
        logging.info(f"DEBUG_DB: Cargando todos los parámetros del bot desde la DB... {DB_PATH}")
        cursor.execute("select nombre_parametro, valor_parametro from parametros_seteos;")
        rows = cursor.fetchall()
        for row in rows:
            nombre, valor = row
            parameters[nombre] = valor
            logging.debug(f"DEBUG_DB: Parámetro cargado - {nombre}: {valor}") # Keep this for per-parameter debug
            # Removed: logging.debug(f"DEBUG_DB: Parámetro cargado - {row}")
        logging.info(f"DEBUG_DB: Todos los parámetros cargados. Total: {len(parameters)}")
        return parameters
    except sqlite3.Error as e:
        logging.error(f"Error al cargar todos los parámetros del bot: {e}")
        traceback.print_exc()
        return {}
    finally:
        if conn:
            conn.close()

def get_parametro(nombre_parametro: str):
    """Obtiene el valor de un parámetro específico por su nombre."""
    conn = None
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT valor FROM parametros_seteos WHERE nombre_parametro = ?", (nombre_parametro,))
        result = cursor.fetchone()
        return result[0] if result else None
    except sqlite3.Error as e:
        logging.error(f"Error al obtener el parámetro '{nombre_parametro}': {e}")
        return None
    finally:
        if conn:
            conn.close()

def set_parametro(nombre_parametro: str, valor: str):
    """Establece o actualiza el valor de un parámetro."""
    conn = None
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO parametros_seteos (nombre_parametro, valor) VALUES (?, ?)",
            (nombre_parametro, valor)
        )
        conn.commit()
        logging.info(f"Parámetro '{nombre_parametro}' seteado con valor '{valor}'.")
    except sqlite3.Error as e:
        logging.error(f"Error al setear el parámetro '{nombre_parametro}': {e}")
        traceback.print_exc()
    finally:
        if conn:
            conn.close()

# Si se ejecuta este archivo directamente para probar la DB
if __name__ == "__main__":
    print("--- Probando db_services.py ---")
    init_db() # Asegura que la DB y tablas existen
    populate_initial_parameters() # Puebla con datos iniciales si no existen

    # --- Pruebas de lectura ---
    print("\n--- Leyendo parámetros ---")
    print(f"Endpoint OpenAI: {get_parametro('AZURE_OPENAI_ENDPOINT')}")
    print(f"Modelo Chat: {get_parametro('AZURE_OPENAI_DEPLOYMENT_NAME')}")
    print(f"AZURE_OPENAI_API_KEY: {get_parametro('AZURE_OPENAI_API_KEY')}")
    print(f"Puerto del Bot: {get_parametro('Puerto del Bot')}")

    # --- Prueba de actualización ---
    # set_parametro("Puerto del Bot", "8860")
    # print(f"Puerto del Bot (actualizado): {get_parametro('Puerto del Bot')}")

    all_params = load_all_bot_parameters()
    print("\n--- Todos los parámetros cargados (load_all_bot_parameters): ---")
    for key, value in all_params.items():
        print(f"{key}: {value}")