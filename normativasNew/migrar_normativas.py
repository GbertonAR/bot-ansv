import sqlite3

def migrar_normativas():
    ruta_db = "normativas.db"
    conn = sqlite3.connect(ruta_db)
    cursor = conn.cursor()

    # Verificamos existencia de la nueva tabla
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS normativas2 (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo TEXT,
        numero INTEGER,
        fecha TEXT,
        titulo TEXT,
        contenido TEXT,
        id_categoria INTEGER,
        id_fuente INTEGER,
        fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (id_categoria) REFERENCES categorias(id),
        FOREIGN KEY (id_fuente) REFERENCES fuentes(id)
    );
    """)

    # Obtener todas las normativas actuales
    cursor.execute("SELECT tipo, numero, fecha, titulo, contenido FROM normativas")
    normativas = cursor.fetchall()

    for n in normativas:
        cursor.execute("""
            INSERT INTO normativas2 (tipo, numero, fecha, titulo, contenido)
            VALUES (?, ?, ?, ?, ?)
        """, n)

    conn.commit()
    conn.close()
    print(f"✅ Migradas {len(normativas)} normativas a normativas2.")

if __name__ == "__main__":
    migrar_normativas()
