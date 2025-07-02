from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import sqlite3

router = APIRouter(prefix="/temas", tags=["Temas Permitidos"])

DB_PATH = "data/soporte_db.db"

class Tema(BaseModel):
    id: int
    tema: str

class TemaCreate(BaseModel):
    tema: str

# ──────────────── GET: Listar todos los temas ────────────────
@router.get("/", response_model=List[Tema])
def listar_temas():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, tema FROM temas_permitidos ORDER BY tema;")
        return [{"id": row[0], "tema": row[1]} for row in cursor.fetchall()]

# ──────────────── POST: Crear nuevo tema ────────────────
@router.post("/", response_model=Tema)
def crear_tema(nuevo: TemaCreate):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO temas_permitidos (tema) VALUES (?);", (nuevo.tema,))
            conn.commit()
            return {"id": cursor.lastrowid, "tema": nuevo.tema}
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="Tema ya existe")

# ──────────────── PUT: Modificar un tema ────────────────
@router.put("/{tema_id}", response_model=Tema)
def actualizar_tema(tema_id: int, data: TemaCreate):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE temas_permitidos SET tema = ? WHERE id = ?;", (data.tema, tema_id))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Tema no encontrado")
        return {"id": tema_id, "tema": data.tema}

# ──────────────── DELETE: Eliminar un tema ────────────────
@router.delete("/{tema_id}", status_code=204)
def eliminar_tema(tema_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM temas_permitidos WHERE id = ?;", (tema_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Tema no encontrado")
