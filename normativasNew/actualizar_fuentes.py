# Administra tabla fuentes

import sqlite3

DB_PATH = "normativas.db"

def agregar_fuente():
    nombre = input("🔹 Nombre de la fuente: ").strip()
    url = input("🔗 URL (opcional): ").strip()
    fecha = input("📅 Fecha de publicación (YYYY-MM-DD): ").strip()
    obs = input("📝 Observaciones (opcional): ").strip()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO fuentes (nombre, url, fecha_publicacion, observaciones)
        VALUES (?, ?, ?, ?)
    """, (nombre, url or None, fecha or None, obs or None))

    conn.commit()
    conn.close()
    print("✅ Fuente agregada correctamente.")

def listar_fuentes():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT id, nombre, fecha_publicacion FROM fuentes ORDER BY id")
    fuentes = cur.fetchall()

    print("\n📚 Fuentes registradas:")
    for f in fuentes:
        print(f"  [{f[0]}] {f[1]} ({f[2] or 'Sin fecha'})")

    conn.close()

def main():
    print("📌 Gestión de fuentes:")
    print("1. Agregar nueva fuente")
    print("2. Listar fuentes existentes")
    opcion = input("Seleccioná una opción (1 o 2): ").strip()

    if opcion == "1":
        agregar_fuente()
    elif opcion == "2":
        listar_fuentes()
    else:
        print("❌ Opción inválida.")

if __name__ == "__main__":
    main()
