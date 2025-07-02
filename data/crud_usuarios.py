# data/crud_usuarios.py
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import sqlite3
from datetime import datetime

router = APIRouter(prefix="/usuarios", tags=["usuarios"])
templates = Jinja2Templates(directory="data/templates")

DB_PATH = "data/soporte_db.db"

@router.get("/", response_class=HTMLResponse)
def listar_usuarios(request: Request):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT u.id, u.nombre, u.email, u.celular, m.Nombre, u.id_rol, u.token_validacion
        FROM usuarios u
        LEFT JOIN Municipios m ON u.id_municipio = m.ID
    """)
    usuarios = cur.fetchall()
    conn.close()
    return templates.TemplateResponse("usuarios_list.html", {"request": request, "usuarios": usuarios})

@router.get("/nuevo", response_class=HTMLResponse)
def nuevo_usuario(request: Request):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT ID, Nombre FROM Municipios")
    municipios = cur.fetchall()
    cur.execute("SELECT ID, Nombre FROM Roles")
    roles = cur.fetchall()
    conn.close()
    return templates.TemplateResponse("usuarios_form.html", {"request": request, "modo": "crear", "municipios": municipios, "roles": roles})

@router.post("/nuevo")
def crear_usuario(
    id: str = Form(...),
    nombre: str = Form(""),
    email: str = Form(...),
    celular: str = Form(...),
    id_municipio: int = Form(None),
    id_rol: int = Form(...),
    token_validacion: str = Form("")
):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("""
        INSERT INTO usuarios (id, nombre, email, celular, id_municipio, fecha_registro, id_rol, token_validacion)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (id, nombre, email, celular, id_municipio, fecha, id_rol, token_validacion))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/usuarios", status_code=303)

@router.get("/{id}/editar", response_class=HTMLResponse)
def editar_usuario_form(request: Request, id: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, nombre, email, celular, id_municipio, id_rol, token_validacion FROM usuarios WHERE id = ?", (id,))
    usuario = cur.fetchone()
    cur.execute("SELECT ID, Nombre FROM Municipios")
    municipios = cur.fetchall()
    cur.execute("SELECT ID, Nombre FROM Roles")
    roles = cur.fetchall()
    conn.close()
    return templates.TemplateResponse("usuarios_form.html", {
        "request": request, "modo": "editar", "usuario": usuario,
        "municipios": municipios, "roles": roles
    })

@router.post("/{id}/editar")
def editar_usuario(
    id: str,
    nombre: str = Form(""),
    email: str = Form(...),
    celular: str = Form(...),
    id_municipio: int = Form(None),
    id_rol: int = Form(...),
    token_validacion: str = Form("")
):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        UPDATE usuarios
        SET nombre = ?, email = ?, celular = ?, id_municipio = ?, id_rol = ?, token_validacion = ?
        WHERE id = ?
    """, (nombre, email, celular, id_municipio, id_rol, token_validacion, id))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/usuarios", status_code=303)

@router.post("/{id}/eliminar")
def eliminar_usuario(id: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM usuarios WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/usuarios", status_code=303)
