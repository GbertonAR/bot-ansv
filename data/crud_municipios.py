# data/crud_municipios.py
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import sqlite3

router = APIRouter(prefix="/municipios", tags=["municipios"])
templates = Jinja2Templates(directory="data/templates")

DB_PATH = "data/soporte_db.db"

# Mostrar selector de provincia
@router.get("/", response_class=HTMLResponse)
def seleccionar_provincia(request: Request):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT ID, Nombre FROM Provincias ORDER BY Nombre")
    provincias = cur.fetchall()
    conn.close()
    return templates.TemplateResponse("municipios_selector.html", {"request": request, "provincias": provincias})

# Listar municipios de una provincia
@router.get("/listar", response_class=HTMLResponse)
def listar_municipios(request: Request, id_provincia: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT Nombre FROM Provincias WHERE ID = ?", (id_provincia,))
    nombre_provincia = cur.fetchone()[0]
    cur.execute("SELECT ID, Nombre, Id_Provincia, Mail_Institucional FROM Municipios WHERE Id_Provincia = ?", (id_provincia,))
    municipios = cur.fetchall()
    conn.close()
    return templates.TemplateResponse("municipios_list.html", {
        "request": request,
        "municipios": municipios,
        "nombre_provincia": nombre_provincia,
        "id_provincia": id_provincia
    })

# Formulario nuevo municipio
@router.get("/nuevo", response_class=HTMLResponse)
def mostrar_nuevo(request: Request, id_provincia: int):
    return templates.TemplateResponse("municipios_form.html", {
        "request": request,
        "modo": "crear",
        "id_provincia": id_provincia
    })

# Crear municipio
@router.post("/nuevo")
def crear_municipio(
    id_provincia: int = Form(...),
    nombre: str = Form(...),
    mail: str = Form("")
):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT INTO Municipios (Nombre, Id_Provincia, Mail_Institucional) VALUES (?, ?, ?)", (nombre, id_provincia, mail))
    conn.commit()
    conn.close()
    return RedirectResponse(url=f"/municipios/listar?id_provincia={id_provincia}", status_code=303)

# Formulario editar municipio
@router.get("/{id}/editar", response_class=HTMLResponse)
def mostrar_editar(request: Request, id: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT ID, Nombre, Id_Provincia, Mail_Institucional FROM Municipios WHERE ID = ?", (id,))
    municipio = cur.fetchone()
    conn.close()
    return templates.TemplateResponse("municipios_form.html", {
        "request": request,
        "modo": "editar",
        "municipio": municipio
    })

# Editar municipio
@router.post("/{id}/editar")
def editar_municipio(
    id: int,
    nombre: str = Form(...),
    id_provincia: int = Form(...),
    mail: str = Form("")
):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("UPDATE Municipios SET Nombre = ?, Mail_Institucional = ? WHERE ID = ?", (nombre, mail, id))
    conn.commit()
    conn.close()
    return RedirectResponse(url=f"/municipios/listar?id_provincia={id_provincia}", status_code=303)

# Eliminar municipio
@router.post("/{id}/eliminar")
def eliminar_municipio(id: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT Id_Provincia FROM Municipios WHERE ID = ?", (id,))
    id_provincia = cur.fetchone()[0]
    cur.execute("DELETE FROM Municipios WHERE ID = ?", (id,))
    conn.commit()
    conn.close()
    return RedirectResponse(url=f"/municipios/listar?id_provincia={id_provincia}", status_code=303)
