import os
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = "normativas.db"
TXT_FOLDER = Path("entrada")
TIPO_DOC = "Manual"  # O "Instructivo", según el contenido

def cargar_documento(nombre_archivo, contenido):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    print(f"\n📄 Procesando: {nombre_archivo}")

    # Entrada manual por teclado
    numero = input("🔢 Ingresar número de documento (ej: 101): ")
    titulo = input("📝 Ingresar título descriptivo: ")
    fecha = input("📅 Ingresar fecha (YYYY-MM-DD): ")
    id_categoria = input("📁 Ingresar ID de categoría: ")
    id_fuente = input("🏛️ Ingresar ID de fuente: ")

    # Insertar en la base
    cur.execute("""
        INSERT INTO normativas2 
        (tipo, numero, fecha, titulo, contenido, id_categoria, id_fuente)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        TIPO_DOC,
        int(numero),
        fecha,
        titulo,
        contenido.strip(),
        int(id_categoria),
        int(id_fuente)
    ))

    conn.commit()
    conn.close()
    print("✅ Documento insertado correctamente.")

def main():
    print(f"📂 Carpeta de entrada: {TXT_FOLDER.resolve()}")
    for archivo in TXT_FOLDER.glob("*.txt"):
        with open(archivo, "r", encoding="utf-8") as f:
            contenido = f.read()
            cargar_documento(archivo.name, contenido)

if __name__ == "__main__":
    main()
