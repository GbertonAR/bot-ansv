import os
import logging
import traceback
import requests
import re
import time


from fastapi import FastAPI, Request, Response, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from pydantic import BaseModel
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
#from openai import AzureOpenAI
from data import auth, admin
from data.crud_parametros import router as router_parametros
from data.crud_provincias import router as router_provincias
from data.crud_municipios import router as router_municipios
#from data.crud_municipios import router as router_municipios
from data.crud_roles import router as router_roles
from data.crud_usuarios import router as router_usuarios
from fastapi.templating import Jinja2Templates


from data.auth_routes import router as auth_router_login

import sqlite3
import uuid
from datetime import datetime


from dotenv import load_dotenv
load_dotenv()

from openai import AzureOpenAI

from bot.services.db_service import (
    init_db,
    populate_initial_parameters,
    load_all_bot_parameters
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ================== Carga configuración ==================
try:
    init_db()
    populate_initial_parameters()
    BOT_PARAMS = load_all_bot_parameters()

    # Variables fallback desde .env si no están en DB
    BOT_PARAMS.setdefault("AZURE_OPENAI_API_KEY", os.getenv("AZURE_OPENAI_API_KEY", ""))
    BOT_PARAMS.setdefault("AZURE_OPENAI_ENDPOINT", os.getenv("AZURE_OPENAI_ENDPOINT", ""))
    BOT_PARAMS.setdefault("AZURE_OPENAI_DEPLOYMENT_NAME", os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", ""))
    BOT_PARAMS.setdefault("DIRECT_LINE_SECRET", os.getenv("DIRECT_LINE_SECRET", ""))
    BOT_PARAMS.setdefault("BOT_NAME", os.getenv("BOT_NAME", "Soporte ANSV"))
    BOT_PARAMS.setdefault("WELCOME_MESSAGE", os.getenv("WELCOME_MESSAGE", "Hola, ¿en qué puedo ayudarte?"))

    # Validar parámetros mínimos
    if not all([BOT_PARAMS["AZURE_OPENAI_API_KEY"], BOT_PARAMS["AZURE_OPENAI_ENDPOINT"], BOT_PARAMS["AZURE_OPENAI_DEPLOYMENT_NAME"]]):
        raise RuntimeError("Faltan parámetros obligatorios para Azure OpenAI en DB o .env")

    logger.info("✔️ Parámetros cargados desde DB y .env")

except Exception as e:
    logger.critical(f"❌ Error crítico al cargar la configuración: {e}")
    traceback.print_exc()
    BOT_PARAMS = {}
    raise RuntimeError("Error crítico al cargar la configuración")

# ================== App y CORS ==================
app = FastAPI()
router = APIRouter()

templates = Jinja2Templates(directory="data/templates")

# Modelo de entrada
class MessageRequest(BaseModel):
    message: str
    
# class SettingsModel(BaseModel):
#     azure_openai_api_key: str
#     azure_openai_endpoint: str
#     azure_openai_deployment: str
#     api_version: str = "2025-03-01-preview"    

# Cliente Azure OpenAI
#settings = get_settingsModel()
# settings = SettingsModel()
# client = AzureOpenAI(
#     api_key=BOT_PARAMS["AZURE_OPENAI_API_KEY"],
#     api_version="2024-02-15-preview",
#     azure_endpoint=BOT_PARAMS["AZURE_OPENAI_ENDPOINT"]
# )

origins_env = os.getenv("CORS_ORIGINS")
# if origins_env:
#     origins = [origin.strip() for origin in origins_env.split(",")]
# else:
#     origins = [
#         "http://localhost:8850",
#         "https://ai-bot-ansv-web-huh3g8cqgcfjgjga.westus-01.azurewebsites.net",
#     ]

if origins_env:
    origins = [origin.strip() for origin in origins_env.split(",")]
else:
    origins = [
        "https://ai-bot-ansv-web-huh3g8cqgcfjgjga.westus-01.azurewebsites.net",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

TEMAS_PERMITIDOS = [
    "ansv", "agencia nacional de seguridad vial", "ley", "decreto", "resolución", "linti", "procedimientos", "normativa nacional",
    "seguridad vial", "normativa", "provincias", "provincia", "municipios", "municipio","autoridades", "categorias", "categoría", "licencia de conducir",
    "sitio web", "contacto", "ministerio", "tránsito", "licencia", "vialidad", "procedimientos", "regulaciones"
    "reglamento", "cnrt", "licencias", "educación vial", "registro", "transporte", "accidentes", "controles", "sanciones", "infraestructura",
    "seguridad", "prevención", "conducción", "vehículos", "peatones", "ciclistas", "motociclistas", "transporte público", "controles de tránsito",
    "ley de tránsito", "reglamento de tránsito", "seguridad en rutas", "seguridad en caminos", "seguridad en autopistas", "seguridad en calles", "seguridad en avenidas", "seguridad en carreteras"
]

app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(auth_router_login) 
app.include_router(router_parametros)
app.include_router(router_provincias)
app.include_router(router_municipios)
app.include_router(router_roles)
app.include_router(router_usuarios)




######## Nuevo testeo
# from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient
# from azure.identity import DefaultAzureCredential


# def verificar_deployment_azure(subscription_id, resource_group, account_name, deployment_name):
#     try:
#         logger.info(f"🔎 Verificando si el deployment '{deployment_name}' existe en Azure OpenAI...")
#         credential = DefaultAzureCredential()
#         client = CognitiveServicesManagementClient(credential, subscription_id)
#         deployments = client.deployments.list(resource_group, account_name)
#         deployment_names = [d.name for d in deployments]
#         logger.info(f"📋 Deployments disponibles en Azure: {deployment_names}")
#         if deployment_name in deployment_names:
#             logger.info(f"✅ Deployment '{deployment_name}' verificado correctamente.")
#             return True
#         else:
#             logger.critical(f"❌ Deployment '{deployment_name}' NO existe en Azure.")
#             return False
#     except Exception as e:
#         logger.critical(f"❌ Error al verificar deployment en Azure: {e}")
#         return False

# # Parámetros necesarios
subscription_id = "2cc76474-0fad-45b2-8035-bb21fbe8aaeb"
resource_group = "rg-bot-ansv-view"
account_name = "ai-ansv-new"
deployment_name = BOT_PARAMS["AZURE_OPENAI_DEPLOYMENT_NAME"]

# # Verificar existencia del deployment en Azure antes de inicializar cliente
# if not verificar_deployment_azure(subscription_id, resource_group, account_name, deployment_name):
#     raise RuntimeError(f"No se encontró el deployment '{deployment_name}' en Azure OpenAI.")


# ###############################################



# ================== Cliente AzureOpenAI ==================
# client = AzureOpenAI(
#     api_key=BOT_PARAMS["AZURE_OPENAI_API_KEY"],
#     base_url=BOT_PARAMS["AZURE_OPENAI_ENDPOINT"],
#     #api_type="azure",
#     api_version="2024-02-15-preview"  # Cambiar si actualizas versión en Azure
# )

def es_consulta_valida(mensaje: str) -> bool:
    mensaje_limpio = mensaje.lower()
    print(f"🔍 Verificando consulta: {mensaje_limpio}")
    return any(palabra in mensaje_limpio for palabra in TEMAS_PERMITIDOS)

def validar_urls(texto: str) -> str:
    urls = re.findall(r'https?://\S+', texto)
    for url in urls:
        try:
            r = requests.head(url, timeout=5)
            if r.status_code >= 400:
                texto = texto.replace(url, "(enlace no disponible)")
        except:
            texto = texto.replace(url, "(enlace no disponible)")
    return texto

######### Grabar consulta
# Agregar al comienzo del archivo
# import sqlite3
# import uuid
# from datetime import datetime

# Función para insertar el log de interacción en la base de datos
def registrar_interaccion(
    id_usuario: str,
    texto_consulta: str,
    texto_respuesta: str,
    tiempo_respuesta_ms: int,
    modelo_ia_usado: str,
    relevancia_ia: int = 0,
    uuid_sesion: str = None,
    ip_usuario: str = None,
    es_desde_search: bool = False,
    url_valida: bool = True,
    feedback_usuario: int = 0
):
    try:
        conn = sqlite3.connect("data/soporte_db.db")
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO interacciones_log (
                id_usuario,
                timestamp_consulta,
                tipo_consulta,
                texto_consulta,
                timestamp_respuesta,
                texto_respuesta,
                tiempo_respuesta_ms,
                modelo_ia_usado,
                relevancia_ia,
                uuid_sesion,
                ip_usuario,
                es_desde_search,
                url_valida,
                feedback_usuario
            ) VALUES (?, CURRENT_TIMESTAMP, ?, ?, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            id_usuario or "anonimo",
            "mensaje",
            texto_consulta,
            texto_respuesta,
            tiempo_respuesta_ms,
            modelo_ia_usado,
            relevancia_ia,
            uuid_sesion or str(uuid.uuid4()),
            ip_usuario or "desconocida",
            int(es_desde_search),
            int(url_valida),
            feedback_usuario
        ))

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"⚠️ Error al registrar interacción: {e}")



###############

# Cliente Azure Search
search_client = SearchClient(
    # endpoint=BOT_PARAMS["AZURE_SEARCH_ENDPOINT"],
    # index_name=BOT_PARAMS["AZURE_SEARCH_INDEX_NAME"],
    # credential=AzureKeyCredential(BOT_PARAMS["AZURE_SEARCH_API_KEY"])
    endpoint="https://ansv-search.search.windows.net",
    index_name="normativas-index",
    credential=AzureKeyCredential("j4aDzLBGWBo4VplEQMudE7HhhHbg7cRMmTRifk3ENpAzSeCrg5ph")    
)

def buscar_en_azure_search(pregunta: str) -> str:
    """
    Realiza una búsqueda en Azure Cognitive Search y devuelve los fragmentos relevantes como contexto.
    """
    try:
        resultados = search_client.search(
            search_text=pregunta,
            top=3,
            query_type="simple"
        )

        fragmentos = []
        for doc in resultados:
            contenido = doc.get("contenido", "")  # asegurate que el campo "contenido" exista en el índice
            titulo = doc.get("titulo", "")
            if contenido:
                fragmentos.append(f"Título: {titulo}\n{contenido}")

        return "\n---\n".join(fragmentos)

    except Exception as e:
        logger.warning(f"⚠️ Error al consultar Azure Search: {e}")
        return ""

print(f"🔑 Usando API Key: {BOT_PARAMS['AZURE_OPENAI_API_KEY']}")
print(f" endpoint: {BOT_PARAMS['AZURE_OPENAI_ENDPOINT']}")
client = AzureOpenAI(
    #azure_endpoint="https://ai-ansv-new.openai.azure.com/",
    azure_endpoint = BOT_PARAMS["AZURE_OPENAI_ENDPOINT"],
    api_key = BOT_PARAMS['AZURE_OPENAI_API_KEY'],
    api_version="2025-01-01-preview",
)

# ================== Modelos Pydantic ==================
class ChatRequest(BaseModel):
    user: str
    message: str

# ================== Endpoints ==================
@app.get("/")
async def root():
    index_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return Response(content="Archivo index.html no encontrado", status_code=404)


@app.post("/api/messages")
async def recibir_mensaje(request: MessageRequest):
    try:
        contexto_ansv = """
                Actuás como el asistente virtual oficial de la Agencia Nacional de Seguridad Vial (ANSV) de Argentina.

                Tu única tarea es responder preguntas estrictamente relacionadas con los siguientes temas:

                0) Todo debe estar contextualizado exclusivamente a la República Argentina.  
                1) Leyes, decretos, resoluciones o procedimientos que involucren a la ANSV.  
                2) Normativas del Estado Nacional relacionadas con seguridad vial.  
                3) Sus equivalencias o implementación en las 24 provincias y municipios del país.  
                4) Autoridades nacionales y provinciales con competencias en seguridad vial.  
                5) Sitios web oficiales y formas de contacto relacionadas.

                Si el usuario realiza una pregunta que no está directamente relacionada con estos temas, respondé con amabilidad indicando que tu alcance está limitado a la información oficial vinculada a la seguridad vial en Argentina.

                Utilizá un tono respetuoso, claro y educativo. Mantené siempre una actitud cordial y profesional.
        """

        mensaje = request.message.strip()
        print(f"📨 Mensaje recibido: {mensaje}")
        
        if not mensaje:
            return JSONResponse(content={"reply": "⚠️ El mensaje está vacío"}, status_code=400)
        
        if not es_consulta_valida(mensaje):
            return JSONResponse(content={
                "reply": "⚠️ Lo siento, mi función es ayudarte con temas relacionados con la seguridad vial en Argentina y la normativa aplicable. Si tenés otra consulta sobre la ANSV, estaré encantado de ayudarte."
            }, status_code=400)
            
        inicio = time.time()
        # response = client.chat.completions.create(
        #     model=BOT_PARAMS["AZURE_OPENAI_DEPLOYMENT_NAME"],
        #     messages=[
        #         {"role": "system", "content": "Sos un asistente útil de la ANSV. Respondé siempre en español."},
        #         {"role": "user", "content": mensaje}
        #     ],
        #     temperature=0.7,
        #     max_tokens=500
        # )
        messages=[
                {"role": "system", "content": contexto_ansv},
                {"role": "user", "content": mensaje}
        ]
        
        ###################### RAG Ver que onda        
        # 🔍 RAG: Buscar contexto adicional en Azure Search
        contexto_extraido = buscar_en_azure_search(mensaje)
        if not contexto_extraido:
            contexto_extraido = "No se encontró información adicional relevante en los documentos disponibles."

        prompt_usuario = (
            f"Teniendo en cuenta la siguiente información institucional:\n"
            f"{contexto_extraido}\n\n"
            f"Respondé la siguiente pregunta:\n{mensaje}"
        )

        messages = [
            {"role": "system", "content": contexto_ansv},
            {"role": "user", "content": prompt_usuario}
        ]


        #################################        
        completion = client.chat.completions.create(
                    model=deployment_name,
                    messages=messages,
                    max_tokens=800,
                    temperature=1,
                    top_p=1,
                    frequency_penalty=0,
                    presence_penalty=0,
                    stop=None,
                    stream=False
        )
        print(completion.to_json())
        respuesta_generada = completion.choices[0].message.content.strip()
        respuesta_filtrada = validar_urls(respuesta_generada)
        # respuesta = completion.choices[0].message.content.strip()
        # print(f"📨 Respuesta del bot: {respuesta}")
        # return JSONResponse(content={"reply": respuesta})
        
        # respuesta = completion.choices[0].message.content.strip()
        print(f"📨 Respuesta del bot: {respuesta_filtrada}")
        ############## zona de grabacion         
        fin = time.time()
        duracion_ms = int((fin - inicio) * 1000)

        # Registrar la interacción
        registrar_interaccion(
            #id_usuario=request.state.usuario["id"] if request.state.usuario else "anonimo",
            id_usuario="anonimo",
            texto_consulta=mensaje,
            texto_respuesta=respuesta_filtrada,
            tiempo_respuesta_ms=duracion_ms,
            modelo_ia_usado=deployment_name,
            relevancia_ia=1,
            es_desde_search=bool(contexto_extraido),
            url_valida="(enlace no disponible)" not in respuesta_filtrada
        )
        ####################################################        
        return JSONResponse(content={"reply": respuesta_filtrada})        
    
    except Exception as e:
        logger.error(f"❌ Error en /api/messages: {e}", exc_info=True)
        return JSONResponse(content={"reply": "❌ Error interno del bot"}, status_code=500)
    
#@app.post("/api/messages")    
# async def recibir_mensaje(request: Request):
#     try:
#         data = await request.json()
#         mensaje = data.get("message", "")

#         if not mensaje:
#             return JSONResponse(content={"reply": "⚠️ Mensaje vacío"}, status_code=400)

#         # response = client.chat.completions.create(
#         #     model=BOT_PARAMS["AZURE_OPENAI_DEPLOYMENT_NAME"],
#         #     messages=[
#         #         {"role": "system", "content": "Sos un asistente útil de la ANSV. Respondé siempre en español."},
#         #         {"role": "user", "content": mensaje}
#         #     ],
#         #     temperature=0.7,
#         #     max_tokens=500
#         # )
#         response = client.chat.completions.create(
#                 deployment_id=BOT_PARAMS["AZURE_OPENAI_DEPLOYMENT_NAME"],
#                 messages=[
#                       {"role": "system", "content": "Sos un asistente útil de la ANSV."},
#                       {"role": "user", "content": request.message}
#                 ],
#                 temperature=0.7,
#                 max_tokens=500
#         )
#         print(f"📨 Usuario: {mensaje}")
#         print(f"📨 Varios : {messages}")

#         respuesta = response.choices[0].message.content.strip()
#         return JSONResponse(content={"reply": respuesta})
#     except Exception as e:
#         logger.error(f"❌ Error en /api/messages: {e}")
#         return JSONResponse(content={"reply": "❌ Error del bot"}, status_code=500)

# @app.post("/api/chat")
# async def chat_with_bot(payload: ChatRequest):
#     try:
#         response = client.chat.completions.create(
#             model=BOT_PARAMS["AZURE_OPENAI_DEPLOYMENT_NAME"],
#             messages=[
#                 {"role": "system", "content": "Eres un asistente útil para la ANSV."},
#                 {"role": "user", "content": payload.message},
#             ],
#         )
#         reply = response.choices[0].message.content
#         return {"reply": reply}
#     except Exception as e:
#         logger.error(f"❌ Error al llamar a Azure OpenAI: {e}", exc_info=True)
#         return JSONResponse(content={"error": str(e)}, status_code=500)
    
    
# @app.post("/api/chat")
# async def chat_with_bot(request: ChatRequest):
#     try:
#         response = client.chat.completions.create(
#             model=BOT_PARAMS["AZURE_OPENAI_DEPLOYMENT_NAME"],
#             messages=[
#                 {"role": "system", "content": "You are a helpful assistant."},
#                 {"role": "user", "content": request.message}
#             ],
#             max_tokens=500
#         )
#         return {"response": response.choices[0].message.content}
#     except Exception as e:
#         logger.error(f"❌ Error al llamar a Azure OpenAI: {e}")
#         raise HTTPException(status_code=500, detail="Error interno del bot")    
    
# Endpoint real con Azure OpenAI
# @router.post("/api/messages")
# async def chat_with_bot(request: MessageRequest):
#     try:
#         response = client.chat.completions.create(
#             model=BOT_PARAMS["AZURE_OPENAI_DEPLOYMENT_NAME"],
#             messages=[
#                 {"role": "system", "content": "Sos un asistente útil de la ANSV. Respondé siempre en español."},
#                 {"role": "user", "content": request.message}
#             ],
#             temperature=0.7,
#             max_tokens=500
#         )
#         return {"response": response.choices[0].message.content.strip()}
#     except Exception as e:
#         return {"response": f"❌ Error al procesar la respuesta: {str(e)}"}    

@app.get("/chat-config")
async def chat_config():
    return {
        "botName": BOT_PARAMS.get("BOT_NAME", "Soporte ANSV"),
        "welcomeMessage": BOT_PARAMS.get("WELCOME_MESSAGE", "Hola, ¿en qué puedo ayudarte?")
    }
    
@app.middleware("http")
async def cargar_usuario_desde_cookie(request: Request, call_next):
    user_id = request.cookies.get("usuario_id")

    if user_id:
        conn = sqlite3.connect("data/soporte_db.db")
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM usuarios WHERE id = ?", (user_id,))
        request.state.usuario = cur.fetchone()
        conn.close()
    else:
        request.state.usuario = None

    response = await call_next(request)
    return response    

@router.get("/logout")
def cerrar_sesion():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("usuario_id")
    return response


@app.get("/admin", response_class=HTMLResponse)
def lanzador_admin(request: Request):
    return templates.TemplateResponse("lanzador.html", {"request": request})