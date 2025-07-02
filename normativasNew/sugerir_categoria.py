import sqlite3

REGLAS_CATEGORIA = [
    (2, ["licencia", "clase", "conducir"]),
    (6, ["alcohol", "cero", "sangre"]),
    (5, ["educación", "campaña", "concientizar"]),
    (4, ["infracción", "sanción", "multa"]),
    (7, ["motocicleta", "moto", "casco"]),
    (8, ["manual", "instructivo"]),
    (9, ["pregunta", "frecuente", "faq"]),
]

def sugerir_categoria_para(titulo, contenido):
    texto = (titulo or "") + " " + (contenido or "")
    texto = texto.lower()

    for id_categoria, palabras in REGLAS_CATEGORIA:
        if any(palabra in texto for palabra in palabras):
            return id_categoria
    return None

def procesar_normativas():
    ruta_db = "normativas.db"
    conn = sqlite3.connect(ruta_db)
    cur = conn.cursor()

    cur.execute("SELECT id, titulo, contenido FROM normativas2 WHERE id_categoria IS NULL")
    pendientes = cur.fetchall()

    asignadas = 0
    for id_normativa, titulo, contenido in pendientes:
        sugerida = sugerir_categoria_para(titulo, contenido)
        if sugerida:
            cur.execute("UPDATE normativas2 SET id_categoria = ? WHERE id = ?", (sugerida, id_normativa))
            print(f"✅ {id_normativa}: Categoría {sugerida} sugerida para '{titulo}'")
            asignadas += 1
        else:
            print(f"⚠️  {id_normativa}: No se pudo sugerir categoría para '{titulo}'")

    conn.commit()
    conn.close()
    print(f"\n🏁 Proceso finalizado. Categorías sugeridas: {asignadas}")

if __name__ == "__main__":
    procesar_normativas()
