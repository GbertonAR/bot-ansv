# data/crud_roles.py
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import sqlite3
from datetime import datetime

router = APIRouter(prefix="/roles", tags=["roles"])
templates = Jinja2Templates(directory="data/templates")

DB_PATH = "data/soporte_db.db"


# def listar_roles(request: Request):
#     conn = sqlite3.connect(DB_PATH)
#     cur = conn.cursor()
#     cur.execute("SELECT id, nombre_rol, Descripcion FROM Roles")
#     roles = cur.fetchall()
#     conn.close()
#     return templates.TemplateResponse("roles_list.html", {"request": request, "roles": roles})
@router.get("/", response_class=HTMLResponse)
def listar_usuarios(request: Request):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            u.id AS usuario_id,
            u.nombre AS usuario_nombre,
            u.email,
            u.celular,
            m.Nombre AS municipio_nombre,
            u.fecha_registro,
            r.nombre_rol,
            u.token_validacion
        FROM usuarios u
        LEFT JOIN roles r ON u.id_rol = r.id
        LEFT JOIN municipios m ON u.id_municipio = m.ID
    """)
    usuarios = cur.fetchall()
    print("Joined usuarios:", usuarios)
    conn.close()
    return templates.TemplateResponse("usuarios_list.html", {"request": request, "usuarios": usuarios})


@router.get("/nuevo", response_class=HTMLResponse)
def mostrar_form_nuevo(request: Request):
    return templates.TemplateResponse("roles_form.html", {"request": request, "modo": "crear"})

@router.post("/nuevo")
def crear_rol(nombre: str = Form(...), descripcion: str = Form("")):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT INTO Roles (Nombre, Descripcion) VALUES (?, ?)", (nombre, descripcion))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/roles", status_code=303)

@router.get("/{id}/editar", response_class=HTMLResponse)
def mostrar_form_editar(request: Request, id: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT ID, Nombre, Descripcion FROM Roles WHERE ID = ?", (id,))
    rol = cur.fetchone()
    conn.close()
    return templates.TemplateResponse("roles_form.html", {"request": request, "modo": "editar", "rol": rol})

@router.post("/{id}/editar")
def editar_rol(id: int, nombre: str = Form(...), descripcion: str = Form("")):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("UPDATE Roles SET Nombre = ?, Descripcion = ? WHERE ID = ?", (nombre, descripcion, id))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/roles", status_code=303)

@router.post("/{id}/eliminar")
def eliminar_rol(id: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM Roles WHERE ID = ?", (id,))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/roles", status_code=303)
