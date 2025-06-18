 
import sqlite3
import os

DATABASE_NAME = 'soporte_db.db'

def setup_database():
    """
    Crea las tablas roles, usuarios, interacciones_log y tickets
    en la base de datos soporte_db.db si no existen.
    También inserta roles iniciales.
    """
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()

        # 1. Crear tabla 'roles'
        # id_rol (INTEGER, PRIMARY KEY, AUTOINCREMENT)
        # nombre_rol (TEXT, UNIQUE, NOT NULL)
        # descripcion (TEXT, NULLABLE)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre_rol TEXT UNIQUE NOT NULL,
                descripcion TEXT
            )
        ''')
        print("Tabla 'roles' verificada/creada.")

        # Insertar roles iniciales si no existen
        roles_to_insert = [
            ("Usuario Estandar", "Usuario general del bot."),
            ("Agente de Soporte", "Encargado de gestionar tickets de soporte."),
            ("Administrador Global", "Acceso completo a la gestión del bot y reportes."),
            ("Operador CEL", "Personal que opera en un Centro Emisor de Licencias."),
            ("Instructor CEL", "Personal instructor en un Centro Emisor de Licencias."),
            ("Prestador", "Tercero que presta servicios en el proceso de LNC.")
        ]
        for rol, desc in roles_to_insert:
            try:
                cursor.execute("INSERT INTO roles (nombre_rol, descripcion) VALUES (?, ?)", (rol, desc))
                print(f"  Rol '{rol}' insertado.")
            except sqlite3.IntegrityError:
                print(f"  Rol '{rol}' ya existe.")
        conn.commit() # Confirmar la inserción de roles

        # 2. Crear tabla 'usuarios'
        # id (TEXT, PRIMARY KEY): ID único del usuario del bot.
        # nombre (TEXT, NULLABLE)
        # email (TEXT, NOT NULL)
        # celular (TEXT, NOT NULL)
        # id_municipio (INTEGER, FOREIGN KEY REFERENCES municipios(id), NULLABLE)
        # fecha_registro (DATETIME, DEFAULT CURRENT_TIMESTAMP)
        # id_rol (INTEGER, FOREIGN KEY REFERENCES roles(id), NOT NULL, DEFAULT 1)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id TEXT PRIMARY KEY,
                nombre TEXT,
                email TEXT NOT NULL,
                celular TEXT NOT NULL,
                id_municipio INTEGER,
                fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
                id_rol INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (id_municipio) REFERENCES municipios(id),
                FOREIGN KEY (id_rol) REFERENCES roles(id)
            )
        ''')
        print("Tabla 'usuarios' verificada/creada.")

        # 3. Crear tabla 'interacciones_log'
        # id (INTEGER, PRIMARY KEY, AUTOINCREMENT)
        # id_usuario (TEXT, FOREIGN KEY REFERENCES usuarios(id), NOT NULL)
        # timestamp_consulta (DATETIME, DEFAULT CURRENT_TIMESTAMP)
        # tipo_consulta (TEXT, NOT NULL)
        # texto_consulta (TEXT, NOT NULL)
        # timestamp_respuesta (DATETIME, NULLABLE)
        # texto_respuesta (TEXT, NULLABLE)
        # tiempo_respuesta_ms (INTEGER, NULLABLE)
        # modelo_ia_usado (TEXT, NULLABLE)
        # relevancia_ia (INTEGER, NULLABLE)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interacciones_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_usuario TEXT NOT NULL,
                timestamp_consulta DATETIME DEFAULT CURRENT_TIMESTAMP,
                tipo_consulta TEXT NOT NULL,
                texto_consulta TEXT NOT NULL,
                timestamp_respuesta DATETIME,
                texto_respuesta TEXT,
                tiempo_respuesta_ms INTEGER,
                modelo_ia_usado TEXT,
                relevancia_ia INTEGER,
                FOREIGN KEY (id_usuario) REFERENCES usuarios(id)
            )
        ''')
        print("Tabla 'interacciones_log' verificada/creada.")

        # 4. Crear tabla 'tickets'
        # id (INTEGER, PRIMARY KEY, AUTOINCREMENT)
        # id_usuario (TEXT, FOREIGN KEY REFERENCES usuarios(id), NOT NULL)
        # asunto (TEXT, NOT NULL)
        # descripcion (TEXT, NOT NULL)
        # fecha_creacion (DATETIME, DEFAULT CURRENT_TIMESTAMP)
        # estado (TEXT, NOT NULL, DEFAULT 'Abierto')
        # prioridad (TEXT, NOT NULL, DEFAULT 'Media')
        # id_agente_asignado (TEXT, FOREIGN KEY REFERENCES usuarios(id), NULLABLE)
        # fecha_cierre (DATETIME, NULLABLE)
        # comentarios_cierre (TEXT, NULLABLE)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_usuario TEXT NOT NULL,
                asunto TEXT NOT NULL,
                descripcion TEXT NOT NULL,
                fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                estado TEXT NOT NULL DEFAULT 'Abierto',
                prioridad TEXT NOT NULL DEFAULT 'Media',
                id_agente_asignado TEXT,
                fecha_cierre DATETIME,
                comentarios_cierre TEXT,
                FOREIGN KEY (id_usuario) REFERENCES usuarios(id),
                FOREIGN KEY (id_agente_asignado) REFERENCES usuarios(id)
            )
        ''')
        print("Tabla 'tickets' verificada/creada.")

        conn.commit()
        print(f"\n¡Base de datos '{DATABASE_NAME}' configurada con éxito!")

    except sqlite3.Error as e:
        print(f"Error al configurar la base de datos: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    # Verifica si el archivo de la base de datos existe
    if os.path.exists(DATABASE_NAME):
        print(f"La base de datos '{DATABASE_NAME}' ya existe. Verificando/creando tablas restantes.")
    else:
        print(f"La base de datos '{DATABASE_NAME}' no existe. Creándola y configurando tablas.")
    
    setup_database()