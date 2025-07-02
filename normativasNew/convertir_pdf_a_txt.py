# convertir_pdf_a_txt.py

import os
from pathlib import Path
from PyPDF2 import PdfReader

# 📌 Base path: detecta automáticamente el directorio raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent  # → bot-ansv/

# 📁 Carpeta de entrada y salida relativa a BASE_DIR
PDF_FOLDER = BASE_DIR / "data" / "textos_nuevos"
TXT_FOLDER = BASE_DIR / "normativasNew" / "entrada"

print(f"📂 Carpeta de PDFs: {PDF_FOLDER}")
print(f"📂 Carpeta de salida: {TXT_FOLDER}")

# Crear carpeta de salida si no existe
TXT_FOLDER.mkdir(parents=True, exist_ok=True)

def extraer_texto_pdf(pdf_path):
    try:
        reader = PdfReader(str(pdf_path))
        texto = ""
        for page in reader.pages:
            texto += page.extract_text() or ""
        return texto.strip()
    except Exception as e:
        print(f"❌ Error leyendo {pdf_path.name}: {e}")
        return None

def convertir_todos_los_pdfs():
    archivos_pdf = list(PDF_FOLDER.glob("*.pdf"))
    
    if not archivos_pdf:
        print("📂 No se encontraron archivos PDF en:", PDF_FOLDER)
        return
    
    for pdf in archivos_pdf:
        print(f"📄 Procesando: {pdf.name}")
        texto = extraer_texto_pdf(pdf)
        
        if texto:
            nombre_txt = pdf.stem + ".txt"
            ruta_salida = TXT_FOLDER / nombre_txt
            with open(ruta_salida, "w", encoding="utf-8") as f:
                f.write(texto)
            print(f"✅ Guardado: {ruta_salida}")
        else:
            print(f"⚠️ No se pudo extraer texto de {pdf.name}")

if __name__ == "__main__":
    convertir_todos_los_pdfs()
