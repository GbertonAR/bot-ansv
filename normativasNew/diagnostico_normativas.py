import sqlite3

def diagnosticar_db(ruta_db):
    print(f"🔍 Inspeccionando la base de datos: {ruta_db}")
    conn = sqlite3.connect(ruta_db)
    cursor = conn.cursor()

    # Obtener lista de tablas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tablas = [t[0] for t in cursor.fetchall()]
    
    for tabla in tablas:
        print(f"\n📦 Tabla encontrada: {tabla}")
        
        # Obtener esquema
        cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{tabla}'")
        esquema = cursor.fetchone()[0]
        print("📄 Esquema:")
        print(esquema)
        
        # Mostrar primeras filas
        cursor.execute(f"SELECT * FROM {tabla} LIMIT 5")
        filas = cursor.fetchall()
        print("📝 Primeras filas:")
        for fila in filas:
            print(fila)

    conn.close()
    print("\n✅ Diagnóstico finalizado.")

if __name__ == "__main__":
    diagnosticar_db("normativas.db")
