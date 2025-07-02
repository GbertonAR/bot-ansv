from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import sqlite3

router = APIRouter()
DB_PATH = "data/soporte_db.db"

def conectar_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@router.get("/api/provincias")
def obtener_provincias():
    #print("🔄 Obteniendo provincias...")
    conn = conectar_db()
    cur = conn.cursor()
    cur.execute("SELECT ID, Nombre FROM Provincias ORDER BY Nombre")
    filas = cur.fetchall()
    # Transformar las filas en JSON friendly
    resultado = [{"ID": row[0], "Nombre": row[1]} for row in filas]
    #print(f"📊 Provincias obtenidas: {len(resultado)} registros")
    conn.close()
    # 🔁 Transformar claves a minúsculas para el frontend
    #resultado = [{"ID": row[0], "Nombre": row[1]} for row in provincias_json]
    #print("✅ Provincias devueltas al cliente", resultado)
    return JSONResponse(content=resultado)

@router.get("/api/municipios/{id_provincia}")
def obtener_municipios(id_provincia: int):
    conn = conectar_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT ID, Nombre FROM municipios
        WHERE Id_provincia = ?
        ORDER BY Nombre
    """, (id_provincia,))
    municipios = [dict(row) for row in cur.fetchall()]
    conn.close()
    return municipios
