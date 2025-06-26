# app.py

import os
import asyncio
import datetime
import smtplib
import requests
import aiohttp
from email.mime.text import MIMEText
from aiohttp import web
from typing import Callable, Awaitable
import json
import urllib.parse
import traceback
import aiohttp_cors
from openai import AzureOpenAI
#from dotenv import load_dotenv # Para leer .env

# Importar el módulo logging y configurarlo al inicio
import logging

# ========================== CONFIGURACIÓN DE LOGGING CENTRALIZADA ==========================
# Obtiene el logger raíz. Todos los demás loggers (ej. de db_service, bot_logic)
# propagarán sus mensajes a este logger si no tienen sus propios handlers.
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG) # Nivel de logging global: DEBUG para máxima verbosidad

# Crea un handler para imprimir en la consola
console_handler = logging.StreamHandler()
# Configura el formato del mensaje para incluir timestamp, nombre del logger, nivel y mensaje
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# Añade el handler al logger raíz SÓLO SI NO TIENE YA NINGUNO
if not root_logger.handlers:
    root_logger.addHandler(console_handler)

# Opcional: Obtiene un logger específico para este módulo (__main__).
logger = logging.getLogger(__name__)
# ===========================================================================================


# Cargar variables de entorno desde .env al inicio
#load_dotenv() # Todavía útil para cualquier otra variable que no esté en la DB

# Importar las funciones de tu módulo de servicios de DB
from bot.services.db_service import (
    init_db,
    populate_initial_parameters,
    load_all_bot_parameters,
    get_parametro,
)

# ========================== Inicialización de la Base de Datos ==========================
try:
    init_db()
    populate_initial_parameters()
    BOT_PARAMS = load_all_bot_parameters()
    logger.info(f"Parámetros cargados de DB: {BOT_PARAMS}")

    # === DEPURACIÓN DE PARÁMETROS EN APP.PY ===
    azure_openai_api_key_debug = BOT_PARAMS.get('AZURE_OPENAI_API_KEY')
    if azure_openai_api_key_debug:
        logger.info(f"AZURE_OPENAI_API_KEY (últimos 4) = '...{azure_openai_api_key_debug[-4:]}'")
    else:
        logger.warning("AZURE_OPENAI_API_KEY no encontrada o vacía en la DB.")

    logger.info(f"AZURE_OPENAI_ENDPOINT = '{BOT_PARAMS.get('AZURE_OPENAI_ENDPOINT')}'")
    logger.info(f"AZURE_OPENAI_CHAT_DEPLOYMENT_NAME = '{BOT_PARAMS.get('AZURE_OPENAI_DEPLOYMENT_NAME')}'")
    logger.info(f"Organización: {BOT_PARAMS.get('ORGANIZACION')}")
    logger.info(f"Email Org: {BOT_PARAMS.get('EMAIL_ORG')}")

except Exception as e:
    logger.critical(f"❌ Error crítico al inicializar la base de datos o cargar parámetros: {e}")
    traceback.print_exc()
    BOT_PARAMS = {}
    exit(1)

BOT_PORT = int(BOT_PARAMS.get("BOT_PORT", os.environ.get("PORT", 8850)))

# ========================== Configuración del Adaptador de Bot Framework ==========================
from botbuilder.core import (
    BotFrameworkAdapter,
    BotFrameworkAdapterSettings,
    ConversationState,
    MemoryStorage,
    UserState
)
from botbuilder.schema import Activity
from bot.dialogs.bot_logic import BotANSV

SETTINGS = {
    "app_id": BOT_PARAMS.get("MicrosoftAppId", ""),
    "app_password": BOT_PARAMS.get("MicrosoftAppPassword", BOT_PARAMS.get("MICROSOFT_APP_PASSWORD", "")),
}
#ADAPTER_SETTINGS = BotFrameworkAdapterSettings(**SETTINGS)
ADAPTER_SETTINGS = BotFrameworkAdapterSettings(
    app_id=BOT_PARAMS.get("MicrosoftAppId", ""),
    app_password=BOT_PARAMS.get("MicrosoftAppPassword", BOT_PARAMS.get("MICROSOFT_APP_PASSWORD", ""))
)
ADAPTER = BotFrameworkAdapter(ADAPTER_SETTINGS)

MEMORY = MemoryStorage()
CONVERSATION_STATE = ConversationState(MEMORY)
USER_STATE = UserState(MEMORY)

# ========================== Inicialización del Bot ==========================
BOT = BotANSV(
    conversation_state=CONVERSATION_STATE,
    user_state=USER_STATE,
    openai_api_key=BOT_PARAMS.get("AZURE_OPENAI_API_KEY"),
    openai_endpoint=BOT_PARAMS.get("AZURE_OPENAI_ENDPOINT"),
    openai_chat_deployment_name=BOT_PARAMS.get("AZURE_OPENAI_DEPLOYMENT_NAME")
)

# ========================== Rutas y Handlers de la Aplicación Web ==========================
app = web.Application()

# 💡 Configurar CORS justo después de crear la app:
# cors = aiohttp_cors.setup(app, defaults={
#     "http://localhost:8850": aiohttp_cors.ResourceOptions(
#         allow_credentials=True,
#         expose_headers="*",
#         allow_headers="*"
#     ),
#     "http://127.0.0.1:8850": aiohttp_cors.ResourceOptions(
#         allow_credentials=True,
#         expose_headers="*",
#         allow_headers="*"
#     ),
#     "ai-bot-ansv-web-huh3g8cqgcfjgjga.westus-01.azurewebsites.net": aiohttp_cors.ResourceOptions(
#         allow_credentials=True,
#         expose_headers="*",
#         allow_headers="*"
#     )
# })

cors = aiohttp_cors.setup(app, defaults={
    "https://ai-bot-ansv-web-huh3g8cqgcfjgjga.westus-01.azurewebsites.net": aiohttp_cors.ResourceOptions(
        allow_credentials=True,
        expose_headers="*",
        allow_headers="*"
    )
})

# ⚙️ Leer origenes permitidos desde variable de entorno o usar valores por defecto

# 📌 Aplicar CORS a todas las rutas
for route in list(app.router.routes()):
    cors.add(route)

async def generate_directline_token(secret):
    url = "https://directline.botframework.com/v3/directline/tokens/generate"
    headers = {"Authorization": f"Bearer {secret}"}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("token")
            else:
                logger.error(f"Error generando token Direct Line: {response.status}")
                return None


async def handle_messages(request: web.Request) -> web.Response:
    if "application/json" not in request.headers["Content-Type"]:
        return web.Response(status=415, text="Unsupported Media Type")

    body = await request.json()
    activity = Activity().deserialize(body)

    auth_header = request.headers.get("Authorization", "")

    try:
        response = await ADAPTER.process_activity(activity, auth_header, BOT.on_turn)
        if response:
            return web.json_response(data=response.body, status=response.status)
        return web.Response(status=200)
    except Exception as e:
        logger.error(f"Error procesando mensaje: {e}", exc_info=True)
        return web.Response(status=500, text=f"Internal Server Error: {e}")
    
def generar_token_direct_line(secret: str) -> str:
    response = requests.post(
        "https://directline.botframework.com/v3/directline/tokens/generate",
        headers={"Authorization": f"Bearer {secret}"}
    )
    return response.json()["token"]
    

# async def chat_config_handler(request: web.Request) -> web.Response:
#     """
#     Handler para la ruta /chat-config que devuelve la configuración del Web Chat
#     desde los parámetros cargados de la base de datos (BOT_PARAMS).
#     """
#     direct_line_secret = BOT_PARAMS.get("DIRECT_LINE_SECRET")
#     microsoft_app_id = BOT_PARAMS.get("MicrosoftAppId", "")

#     if not direct_line_secret:
#         logger.error("DIRECT_LINE_SECRET no encontrado en BOT_PARAMS (DB).")
#         return web.json_response({"error": "Direct Line Secret no configurado"}, status=500)

#     config = {
#         "directLineSecret": direct_line_secret,
#         "botId": microsoft_app_id,
#         "botName": BOT_PARAMS.get("BOT_NAME", "Soporte ANSV"), # Lee de DB o usa default
#         "welcomeMessage": BOT_PARAMS.get("WELCOME_MESSAGE", "Hola, soy tu asistente de soporte de ANSV. ¿En qué puedo ayudarte hoy?") # Lee de DB o usa default
#     }
#     return web.json_response(config)

async def chat_config_handler(request: web.Request) -> web.Response:
    direct_line_secret = BOT_PARAMS.get("DIRECT_LINE_SECRET")
    if not direct_line_secret:
        logger.error("DIRECT_LINE_SECRET no encontrado en BOT_PARAMS (DB).")
        return web.json_response({"error": "Direct Line Secret no configurado"}, status=500)

    token = await generate_directline_token(direct_line_secret)
    if not token:
        return web.json_response({"error": "No se pudo generar el token de Direct Line"}, status=500)

    config = {
        "token": token,
        "botId": BOT_PARAMS.get("MicrosoftAppId", ""),
        "botName": BOT_PARAMS.get("BOT_NAME", "Soporte ANSV"),
        "welcomeMessage": BOT_PARAMS.get("WELCOME_MESSAGE", "Hola, soy tu asistente de soporte de ANSV.")
    }
    return web.json_response(config)

async def handle_root(request):
    """
    Handler para la ruta raíz que sirve el archivo index.html.
    """
    index_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(index_path):
        return web.FileResponse(index_path)
    return web.Response(text="Archivo index.html no encontrado", status=404)



# ------------------- Registro de rutas -------------------
route1 = app.router.add_post("/api/messages", handle_messages)
route2 = app.router.add_post("/api/messages{tail:.*}", handle_messages)
route3 = app.router.add_get("/", handle_root)
route4 = app.router.add_get("/chat-config", chat_config_handler)

route5 = app.router.add_static('/static/', path=os.path.join(os.path.dirname(__file__), 'static'), name='static')

# 💡 Aplicar CORS a la ruta:
for route in list(app.router.routes()):
    cors.add(route)
# ========================== Punto de Entrada Principal ==========================
def main():
    #port = int(os.environ.get("PORT", 3978))  # Puerto que asigna Azure, o 3978 por defecto para local
    port = int(os.environ.get("PORT", 8000))  # Puerto que asigna Azure, o 3978 por defecto para local
    host = "0.0.0.0"  # Escucha en todas las interfaces para Azure

    logger.info(f"🌐 Servidor del bot iniciado en http://{host}:{port}")
    logger.info(f"🔗 Endpoint para el Bot Framework Service: http://{host}:{port}/api/messages")
    logger.info(f"💬 Web Chat disponible en: http://{host}:{port}/\n")

    try:
        web.run_app(app, host=host, port=port)
    except Exception as error:
        logger.critical(f"❌ Error fatal al iniciar la aplicación web: {error}")
        traceback.print_exc()

if __name__ == "__main__":
    main()