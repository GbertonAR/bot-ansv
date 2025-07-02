import json
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

# 📌 Parámetros de Azure Search (usá tus valores reales)
AZURE_SEARCH_ENDPOINT = "https://ansv-search.search.windows.net"
AZURE_SEARCH_INDEX_NAME = "normativas-index"  # o el nombre real que usás
AZURE_SEARCH_API_KEY = "j4aDzLBGWBo4VplEQMudE7HhhHbg7cRMmTRifk3ENpAzSeCrg5ph"
NDJSON_FILE = "export/normativas.ndjson"

def cargar_documentos_a_search():
    # Cliente de búsqueda
    search_client = SearchClient(
        endpoint=AZURE_SEARCH_ENDPOINT,
        index_name=AZURE_SEARCH_INDEX_NAME,
        credential=AzureKeyCredential(AZURE_SEARCH_API_KEY)
    )

    # Leer NDJSON
    documentos = []
    with open(NDJSON_FILE, "r", encoding="utf-8") as f:
        for linea in f:
            doc = json.loads(linea)
            documentos.append(doc)

    # Enviar en lotes de hasta 1000 documentos (límite de Azure)
    batch_size = 1000
    total = len(documentos)
    for i in range(0, total, batch_size):
        lote = documentos[i:i + batch_size]
        resultado = search_client.upload_documents(documents=lote)
        print(f"📤 Subidos {len(lote)} documentos. Resultado:")
        for r in resultado:
            print(f" - ID {r.key}: {r.status}")

    print(f"✅ Subida completa: {total} documentos procesados.")

if __name__ == "__main__":
    cargar_documentos_a_search()
