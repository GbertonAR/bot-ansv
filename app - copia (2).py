# app.py

import os
import asyncio
import datetime
import smtplib
from email.mime.text import MIMEText
from aiohttp import web
from typing import Callable, Awaitable
import json
import urllib.parse
import traceback
from dotenv import load_dotenv # Para leer .env

# Importar el módulo logging y configurarlo al inicio
import logging
# Crea un logger para tu aplicación (se recomienda el nombre del módulo __name__)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG) # Nivel de logging: DEBUG para máxima verbosidad

# Crea un handler para imprimir en la consola
console_handler = logging.StreamHandler()
# Configura el formato del mensaje para incluir timestamp, nombre del logger, nivel y mensaje
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
# Añade el handler al logger
logger.addHandler(console_handler)

# Cargar variables de entorno desde .env al inicio
load_dotenv()

# Importar las funciones de tu módulo de servicios de DB
# Asegúrate de que bot/services/db_services.py exista y contenga estas funciones

from bot.services.db_service import (
    #init_db,
    #populate_initial_parameters,
    load_all_bot_parameters,
    get_parametro, # Aunque no se usa directamente, es útil para consistencia
)


# Bloque para importar configuración de correo (opcional, si falla no detiene el bot)
try:
    from config_canje import MAIL_ACCOUNTS
    logger.info("config_canje.py importado correctamente. La funcionalidad de envío de correo estará disponible.")
except ImportError:
    logger.warning("ADVERTENCIA: No se pudo importar 'config_canje'. La funcionalidad de envío de correo no funcionará.")
    MAIL_ACCOUNTS = {"mesa_entradas": {}} # Fallback para evitar errores de NameError

# Importaciones de Bot Framework
from botbuilder.core import (
    BotFrameworkAdapter,
    BotFrameworkAdapterSettings,
    TurnContext,
    MemoryStorage,
    ConversationState,
    UserState,
    MessageFactory,
    CardFactory,
)
from botbuilder.schema import (
    Activity, 
    ActivityTypes, 
    HeroCard, 
    CardAction, 
    ActionTypes, 
    CardImage, 
    Attachment
)

# Importar la lógica principal del bot
from bot.dialogs.bot_logic import BotANSV

# --- Inicialización de la Base de Datos y Carga de Parámetros ---
# Estas funciones aseguran que la DB exista y esté poblada al inicio de la aplicación
# Si `db_services.py` tiene un `if __name__ == "__main__":` block para testear
# no necesitas ejecutarlo por separado en el main; estas llamadas aquí son suficientes.
# init_db() # Asegura que la DB y las tablas existen
# populate_initial_parameters() # Rellena la DB con valores por defecto si no existen
BOT_PARAMS = load_all_bot_parameters() # Carga todos los parámetros en un diccionario

# --- Configuración de Credenciales y Parámetros del Bot ---
# Se obtienen de BOT_PARAMS (que vienen de la DB).
# Si la DB no los tiene, se intenta de las variables de entorno, sino, un string vacío.
APP_ID = BOT_PARAMS.get("MicrosoftAppId") or os.environ.get("BOT_APP_ID", "")
APP_PASSWORD = BOT_PARAMS.get("MicrosoftAppPassword") or os.environ.get("BOT_APP_PASSWORD", "")

OPENAI_KEY = BOT_PARAMS.get("AZURE_OPENAI_API_KEY") or os.environ.get("AZURE_OPENAI_API_KEY", "")
OPENAI_ENDPOINT = BOT_PARAMS.get("Endpoint OpenAI") # Asume que este nombre está en tu DB
OPENAI_CHAT_DEPLOYMENT = BOT_PARAMS.get("Modelo Chat") # Asume que este nombre está en tu DB

# Otras variables de la organización que podrían estar en la DB
ORG_NOMBRE = BOT_PARAMS.get("Organización", "Organización por Defecto")
ORG_DIRECCION = BOT_PARAMS.get("Dirección Org", "Dirección por Defecto") # Asegúrate que este nombre esté en tu DB
ORG_EMAIL = BOT_PARAMS.get("Email Org", "email@defecto.com")

# Puerto del Bot: Prioridad DB > Entorno > Defecto
BOT_PORT = 8850 # Valor por defecto
try:
    db_port = BOT_PARAMS.get("Puerto del Bot")
    if db_port:
        BOT_PORT = int(db_port)
    elif os.environ.get("PORT"):
        BOT_PORT = int(os.environ.get("PORT"))
except ValueError:
    logger.warning(f"ADVERTENCIA: El puerto en DB/Env no es un número válido. Usando puerto por defecto: {BOT_PORT}")


# === LÍNEAS DE DEPURACIÓN DE PARÁMETROS FINALES (usando logger) ===
logger.info(f"APP_ID configurado = '{APP_ID}'")
logger.info(f"APP_PASSWORD configurado = '...{APP_PASSWORD[-4:]}'" if APP_PASSWORD else "APP_PASSWORD NO CONFIGURADO")
logger.info(f"AZURE_OPENAI_API_KEY (últimos 4) = '...{OPENAI_KEY[-4:]}'" if OPENAI_KEY else "AZURE_OPENAI_API_KEY NO CONFIGURADO")
logger.info(f"AZURE_OPENAI_ENDPOINT = '{OPENAI_ENDPOINT}'" if OPENAI_ENDPOINT else "AZURE_OPENAI_ENDPOINT NO CONFIGURADO")
logger.info(f"AZURE_OPENAI_CHAT_DEPLOYMENT = '{OPENAI_CHAT_DEPLOYMENT}'" if OPENAI_CHAT_DEPLOYMENT else "AZURE_OPENAI_CHAT_DEPLOYMENT NO CONFIGURADO")
logger.info(f"Organización: {ORG_NOMBRE}")
logger.info(f"Email Org: {ORG_EMAIL}")
logger.info(f"Puerto del Bot: {BOT_PORT}")
# =======================================================


# Crear adaptador del Bot Framework
SETTINGS = BotFrameworkAdapterSettings(APP_ID, APP_PASSWORD)
ADAPTER = BotFrameworkAdapter(SETTINGS)

# Manejo de errores en el adaptador
async def on_error(turn_context: TurnContext, error: Exception):
    logger.error(f"\n[on_turn_error] Error no controlado: {error}")
    traceback.print_exc() # Imprimir el stack trace completo para depuración
    await turn_context.send_activity("¡Lo siento! Algo salió mal. Por favor, intenta de nuevo.")
    # Envía un mensaje de error detallado al usuario si está en el emulador
    if turn_context.activity.channel_id == "emulator":
        await turn_context.send_activity(f"```\n{error}\n```")
    # Limpiar el estado de la conversación para evitar bucles de error
    if CONVERSATION_STATE: # Asegurarse de que CONVERSATION_STATE esté definido
        await CONVERSATION_STATE.delete(turn_context)

ADAPTER.on_turn_error = on_error

# Configuración del estado (definido antes de la instancia del bot)
MEMORY = MemoryStorage()
CONVERSATION_STATE = ConversationState(MEMORY)
USER_STATE = UserState(MEMORY)

# Instancia de tu bot principal
# Se le pasan los objetos de estado y los parámetros de OpenAI cargados
BOT = BotANSV(
    CONVERSATION_STATE, 
    USER_STATE,
    openai_api_key=OPENAI_KEY,
    openai_endpoint=OPENAI_ENDPOINT,
    openai_chat_deployment_name=OPENAI_CHAT_DEPLOYMENT
)

# === Rutas del Servidor Web (aiohttp) ===
app = web.Application()

# Ruta para manejar los mensajes del Bot Framework Service
async def handle_messages(request: web.Request):
    logger.debug(f"Received request headers: {request.headers}")
    if "application/json" in request.headers.get("Content-Type", ""):
        body = await request.json()
    else:
        # Esto es un fallback, la mayoría de las actividades de bot son JSON
        body = await request.post() 
    
    activity = Activity().deserialize(body)
    auth_header = request.headers.get("Authorization", "")
    
    # Procesar la actividad con el adaptador y la lógica del bot
    response = await ADAPTER.process_activity(activity, auth_header, BOT.on_turn)
    if response:
        return web.json_response(data=response.body, status=response.status)
    return web.Response(status=200)

# Ruta para el Web Chat (sirve el index.html de static/)
async def handle_root(request: web.Request):
    html_file_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if not os.path.exists(html_file_path):
        logger.error(f"index.html no encontrado en la ruta: {html_file_path}")
        return web.Response(status=404, text="index.html no encontrado en la carpeta 'static'.")
    
    return web.FileResponse(html_file_path)

# Ruta para la configuración del chat (ej. token de Direct Line)
async def chat_config_handler(request: web.Request):
    # NOTA: Para producción, este token debería ser generado de forma segura
    # a través de una API de Direct Line o similar, no hardcodeado.
    response_data = {
        "token": "YOUR_DIRECT_LINE_TOKEN_HERE_OR_FETCH_SECURELY", 
        "userID": f"user_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    }
    return web.json_response(response_data)


# Configuración de rutas para la aplicación web
app.router.add_post("/api/messages", handle_messages)
app.router.add_post("/api/messages{tail:.*}", handle_messages) # Permite sub-rutas
app.router.add_get("/", handle_root) # Ruta para el Web Chat
app.router.add_get("/chat-config", chat_config_handler) # Ruta para la configuración del chat

# Sirve los archivos estáticos desde la carpeta 'static'
# Esto permite que index.html, avatares, imágenes, etc., sean accesibles
app.router.add_static('/static/', path=os.path.join(os.path.dirname(__file__), 'static'), name='static')


# ========================== Punto de Entrada Principal ==========================
def main():
    # El puerto ya se ha determinado y logueado al inicio del script
    port = BOT_PORT 
    
    logger.info(f"🌐 Servidor del bot iniciado en http://127.0.0.1:{port}")
    logger.info(f"🔗 Endpoint para el Bot Framework Service: http://127.0.0.1:{port}/api/messages")
    logger.info(f"💬 Web Chat disponible en: http://127.0.0.1:{port}/\n")
    
    try:
        web.run_app(app, host="127.0.0.1", port=port)
    except Exception as error:
        logger.critical(f"❌ Error fatal al iniciar la aplicación web: {error}")
        traceback.print_exc()

# Este es el punto de entrada real cuando ejecutas el script.
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nServidor detenido por el usuario (Ctrl+C).")
    except Exception as e:
        logger.critical(f"Error inesperado en la ejecución principal: {e}")
        traceback.print_exc()