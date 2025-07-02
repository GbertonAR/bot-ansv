from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

service_endpoint = "https://ansv-search.search.windows.net"
index_name = "normativas-index"
api_key = "j4aDzLBGWBo4VplEQMudE7HhhHbg7cRMmTRifk3ENpAzSeCrg5ph"


client = SearchClient(endpoint=service_endpoint, index_name=index_name, credential=AzureKeyCredential(api_key))

results = client.search(search_text="*")  # Busca todo

for i, doc in enumerate(results):
    print(f"Documento {i+1}: {doc}")
    if i >= 4:  # Solo primeros 5
        break
