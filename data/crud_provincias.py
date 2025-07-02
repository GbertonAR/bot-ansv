# data/crud_provincias.py
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import sqlite3
from datetime import datetime

router = APIRouter(prefix="/provincias", tags=["provincias"])
templates = Jinja2Templates(directory="data/templates")
DB_PATH = "data/soporte_db.db"

@router.get("/", response_class=HTMLResponse)
def listar_provincias(request: Request):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT ID, Nombre FROM Provincias")
    provincias = cur.fetchall()
    conn.close()
    return templates.TemplateResponse("provincias_list.html", {"request": request, "provincias": provincias})


@router.get("/nueva", response_class=HTMLResponse)
def mostrar_formulario_crear(request: Request):
    return templates.TemplateResponse("provincias_form.html", {"request": request, "modo": "crear"})


@router.post("/nueva")
def crear_provincia(nombre: str = Form(...)):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT INTO Provincias (Nombre) VALUES (?)", (nombre,))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/provincias", status_code=303)


@router.get("/{id}/editar", response_class=HTMLResponse)
def mostrar_editar(request: Request, id: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT ID, Nombre FROM Provincias WHERE ID = ?", (id,))
    provincia = cur.fetchone()
    conn.close()
    return templates.TemplateResponse("provincias_form.html", {"request": request, "modo": "editar", "provincia": provincia})


@router.post("/{id}/editar")
def editar_provincia(id: int, nombre: str = Form(...)):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("UPDATE Provincias SET Nombre = ? WHERE ID = ?", (nombre, id))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/provincias", status_code=303)


@router.post("/{id}/eliminar")
def eliminar_provincia(id: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM Provincias WHERE ID = ?", (id,))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/provincias", status_code=303)
