## admin.py
from fastapi import APIRouter, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import sqlite3

router = APIRouter()
templates = Jinja2Templates(directory="data/templates")
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

# 🆕 NUEVO ENDPOINT: Temas Permitidos
@router.get("/temas", response_class=HTMLResponse)
def mostrar_temas(request: Request):
    conn = conectar_db()
    cur = conn.cursor()
    cur.execute("SELECT id, tema FROM temas_permitidos ORDER BY id;")
    temas = cur.fetchall()
    conn.close()
    return templates.TemplateResponse("temas.html", {"request": request, "temas": temas})


@router.get("/temas/nuevo", response_class=HTMLResponse)
def formulario_nuevo_tema(request: Request):
    return templates.TemplateResponse("nuevo_tema.html", {"request": request})

@router.post("/temas/nuevo")
def crear_nuevo_tema(request: Request, tema: str = Form(...)):
    conn = conectar_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO temas_permitidos (tema) VALUES (?)", (tema,))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/temas", status_code=303)

@router.post("/temas/nuevo")
def crear_nuevo_tema(request: Request, tema: str = Form(...)):
    try:
        conn = conectar_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO temas_permitidos (tema) VALUES (?)", (tema,))
        conn.commit()
        conn.close()
        return RedirectResponse(url="/temas", status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        print(f"❌ Error al insertar nuevo tema: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {e}")
