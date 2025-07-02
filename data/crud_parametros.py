# data/crud_parametros.py
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import sqlite3
from datetime import datetime

router = APIRouter(prefix="/parametros", tags=["parametros"])
templates = Jinja2Templates(directory="data/templates")

DB_PATH = "data/soporte_db.db"

@router.get("/", response_class=HTMLResponse)
def listar_parametros(request: Request):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT id, nombre_parametro, valor_parametro, valor, tipo_dato, descripcion, ultima_modificacion
        FROM parametros_seteos
    """)
    parametros = cur.fetchall()
    conn.close()
    return templates.TemplateResponse("parametros_list.html", {
        "request": request,
        "parametros": parametros
    })

@router.get("/nuevo", response_class=HTMLResponse)
def mostrar_formulario_crear(request: Request):
    return templates.TemplateResponse("parametros_form.html", {
        "request": request,
        "modo": "crear"
    })

@router.post("/nuevo")
def crear_parametro(
    nombre_parametro: str = Form(...),
    valor_parametro: str = Form(...),
    valor: str = Form(""),
    tipo_dato: str = Form(""),
    descripcion: str = Form(""),
):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("""
        INSERT INTO parametros_seteos (nombre_parametro, valor_parametro, valor, tipo_dato, descripcion, ultima_modificacion)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (nombre_parametro, valor_parametro, valor, tipo_dato, descripcion, ahora))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/parametros", status_code=303)

@router.get("/{id}/editar", response_class=HTMLResponse)
def mostrar_editar(request: Request, id: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT id, nombre_parametro, valor_parametro, valor, tipo_dato, descripcion
        FROM parametros_seteos
        WHERE id = ?
    """, (id,))
    parametro = cur.fetchone()
    conn.close()
    return templates.TemplateResponse("parametros_form.html", {
        "request": request,
        "modo": "editar",
        "parametro": parametro
    })

@router.post("/{id}/editar")
def editar_parametro(
    id: int,
    nombre_parametro: str = Form(...),
    valor_parametro: str = Form(...),
    valor: str = Form(""),
    tipo_dato: str = Form(""),
    descripcion: str = Form(""),
):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("""
        UPDATE parametros_seteos
        SET nombre_parametro = ?, valor_parametro = ?, valor = ?, tipo_dato = ?, descripcion = ?, ultima_modificacion = ?
        WHERE id = ?
    """, (nombre_parametro, valor_parametro, valor, tipo_dato, descripcion, ahora, id))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/parametros", status_code=303)

@router.post("/{id}/eliminar")
def eliminar_parametro(id: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM parametros_seteos WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/parametros", status_code=303)
