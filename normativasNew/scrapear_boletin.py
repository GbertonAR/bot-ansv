# Obtiene normas nuevas

import sqlite3
import os

RUTA_DB = "normativas.db"
RUTA_ENTRADA = "boletin_simulado"

def parsear_boletin(ruta_archivo):
    with open(ruta_archivo, "r", encoding="utf-8") as f:
        lineas = f.readlines()

    tipo = numero = fecha = titulo = ""
    contenido = []
    leyendo_cuerpo = False

    for linea in lineas:
        linea = linea.strip()
        if not linea and not leyendo_cuerpo:
            leyendo_cuerpo = True
            continue

        if not leyendo_cuerpo:
            if linea.lower().startswith("tipo:"):
                tipo = linea.split(":", 1)[1].strip()
            elif linea.lower().startswith("número:") or linea.lower().startswith("numero:"):
                numero = linea.split(":", 1)[1].strip()
            elif linea.lower().startswith("fecha:"):
                fecha = linea.split(":", 1)[1].strip()
            elif linea.lower().startswith("título:") or linea.lower().startswith("titulo:"):
                titulo = linea.split(":", 1)[1].strip()
        else:
            contenido.append(linea)

    return tipo, numero, fecha, titulo, "\n".join(contenido)

def obtener_id_fuente_boletin():
    conn = sqlite3.connect(RUTA_DB)
    cur = conn.cursor()
    cur.execute("SELECT id FROM fuentes WHERE nombre LIKE '%Boletín Oficial%' LIMIT 1")
    fila = cur.fetchone()
    conn.close()
    return fila[0] if fila else None

def insertar_normativa(tipo, numero, fecha, titulo, contenido, id_fuente):
    conn = sqlite3.connect(RUTA_DB)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO normativas2 (tipo, numero, fecha, titulo, contenido, id_fuente)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (tipo, numero, fecha, titulo, contenido, id_fuente))
    conn.commit()
    conn.close()
    print(f"✅ Insertado: {tipo} {numero} - {titulo}")

def main():
    archivos = [f for f in os.listdir(RUTA_ENTRADA) if f.endswith(".txt")]
    id_fuente = obtener_id_fuente_boletin()

    if not id_fuente:
        print("❌ Fuente 'Boletín Oficial' no encontrada. Cargala con actualizar_fuentes.py")
        return

    for archivo in archivos:
        ruta = os.path.join(RUTA_ENTRADA, archivo)
        print(f"🔍 Procesando {archivo}...")
        tipo, numero, fecha, titulo, contenido = parsear_boletin(ruta)

        if not all([tipo, numero, fecha, titulo, contenido]):
            print(f"⚠️ Archivo incompleto o malformado: {archivo}")
            continue

        insertar_normativa(tipo, numero, fecha, titulo, contenido, id_fuente)

if __name__ == "__main__":
    main()
