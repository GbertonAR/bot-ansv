import sqlite3
import json
import os

DB_PATH = "normativas.db"
EXPORT_DIR = "export"
NDJSON_PATH = os.path.join(EXPORT_DIR, "normativas.ndjson")
JSON_PATH = os.path.join(EXPORT_DIR, "normativas.json")

def exportar_normativas():
    os.makedirs(EXPORT_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT
            n.id,
            n.tipo,
            n.fecha,
            n.titulo,
            n.contenido,
            c.nombre AS categoria,
            f.nombre AS fuente
        FROM normativas2 n
        LEFT JOIN categorias c ON n.id_categoria = c.id
        LEFT JOIN fuentes f ON n.id_fuente = f.id
        ORDER BY n.fecha DESC
    """)

    filas = cur.fetchall()
    conn.close()

    export_json = []
    with open(NDJSON_PATH, "w", encoding="utf-8") as ndjson_file:
        for fila in filas:
            obj = {
                "id": str(fila["id"]),
                "tipo": str(fila["tipo"]) if fila["tipo"] else "",
                "fecha": str(fila["fecha"]) if fila["fecha"] else "",
                "titulo": str(fila["titulo"]) if fila["titulo"] else "",
                "contenido": str(fila["contenido"]) if fila["contenido"] else "",
                "categoria": str(fila["categoria"]) if fila["categoria"] else "",
                "fuente": str(fila["fuente"]) if fila["fuente"] else ""
            }
            export_json.append(obj)
            ndjson_file.write(json.dumps(obj, ensure_ascii=False) + "\n")

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(export_json, f, indent=2, ensure_ascii=False)

    print(f"✅ Exportado {len(filas)} normativas a:")
    print(f"  • {JSON_PATH}")
    print(f"  • {NDJSON_PATH}")

if __name__ == "__main__":
    exportar_normativas()
