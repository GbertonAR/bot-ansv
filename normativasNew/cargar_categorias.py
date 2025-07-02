import sqlite3

def cargar_categorias():
    ruta_db = "normativas.db"
    conn = sqlite3.connect(ruta_db)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categorias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL UNIQUE,
        descripcion TEXT
    );
    """)

    categorias = [
        ("Seguridad Vial", "Normas generales de tránsito y prevención"),
        ("Licencias de Conducir", "Requisitos, clases, otorgamiento y vigencia"),
        ("Transporte Público", "Normativa sobre colectivos, escolares, taxis"),
        ("Infracciones y Penalidades", "Multas, puntos y sanciones aplicables"),
        ("Educación y Concientización", "Campañas, educación vial y cultura ciudadana"),
        ("Alcohol Cero", "Regulación sobre consumo de alcohol en conductores"),
        ("Motovehículos", "Normas para motociclistas y ciclomotores"),
        ("Normativa Institucional", "Reglamentos, decretos internos ANSV"),
        ("Discapacidad y Accesibilidad", "Adaptaciones y normas específicas")
    ]

    for nombre, descripcion in categorias:
        try:
            cursor.execute("INSERT INTO categorias (nombre, descripcion) VALUES (?, ?)", (nombre, descripcion))
        except sqlite3.IntegrityError:
            print(f"⚠️ Categoría ya existente: {nombre}")

    conn.commit()
    conn.close()
    print("✅ Categorías insertadas correctamente.")

if __name__ == "__main__":
    cargar_categorias()
