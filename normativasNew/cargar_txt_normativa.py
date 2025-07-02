import sqlite3
import os

def parsear_archivo(ruta_archivo):
    with open(ruta_archivo, 'r', encoding='utf-8') as f:
        lineas = f.readlines()

    tipo = numero = fecha = titulo = None
    contenido = []
    cabecera_terminada = False

    for linea in lineas:
        linea = linea.strip()
        if not linea and not cabecera_terminada:
            cabecera_terminada = True
            continue

        if not cabecera_terminada:
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

def insertar_normativa(db_path, tipo, numero, fecha, titulo, contenido):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO normativas2 (tipo, numero, fecha, titulo, contenido)
        VALUES (?, ?, ?, ?, ?)
    """, (tipo, numero, fecha, titulo, contenido))

    conn.commit()
    conn.close()
    print(f"✅ Insertada: {tipo} {numero} ({fecha}) - {titulo}")

def main():
    carpeta_entrada = "entrada"
    db_path = "bot-ansv/normativasNew/normativas.db"
    
    print("🔍 Buscando archivos .txt en la carpeta de entrada...")

    archivos = [f for f in os.listdir(carpeta_entrada) if f.endswith(".txt")]

    for archivo in archivos:
        ruta = os.path.join(carpeta_entrada, archivo)
        print(f"📄 Procesando: {archivo}")
        tipo, numero, fecha, titulo, contenido = parsear_archivo(ruta)

        if not all([tipo, numero, fecha, titulo, contenido]):
            print(f"⚠️ Archivo incompleto: {archivo}")
            continue

        insertar_normativa(db_path, tipo, numero, fecha, titulo, contenido)

if __name__ == "__main__":
    main()
