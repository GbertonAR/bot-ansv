from aiohttp import web
from botbuilder.core import (
    BotFrameworkAdapter,
    BotFrameworkAdapterSettings,
    TurnContext,
    ConversationState,
    MemoryStorage,
    UserState
)
from botbuilder.schema import Activity
from dotenv import load_dotenv
import os, uuid, logging
from bot_logic import BotANSV

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración del adaptador
SETTINGS = BotFrameworkAdapterSettings(app_id="", app_password="")
SETTINGS.is_auth_disabled = True  # Autenticación deshabilitada para desarrollo
ADAPTER = BotFrameworkAdapter(SETTINGS)

# Estados del bot
MEMORY = MemoryStorage()
CONVERSATION_STATE = ConversationState(MEMORY)
USER_STATE = UserState(MEMORY)

# Instancia del bot
BOT = BotANSV(
    CONVERSATION_STATE,
    USER_STATE,
    os.getenv("AZURE_OPENAI_API_KEY"),
    os.getenv("AZURE_OPENAI_ENDPOINT"),
    os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")
)

# Endpoint para crear una conversación
async def handle_create_conversation(request):
    conversation_id = f"conv-{uuid.uuid4()}"
    return web.json_response({
        "conversationId": conversation_id,
        "expires_in": 3600,
        "token": "dev-token"
    }, status=201)

# Endpoint para recibir mensajes
async def handle_messages(request):
    try:
        body = await request.json()
        activity = Activity().deserialize(body)
        auth_header = request.headers.get("Authorization", "")
        response = await ADAPTER.process_activity(activity, auth_header, BOT.on_turn)
        if response:
            return web.json_response(data=response.body, status=response.status)
        return web.Response(status=200)
    except Exception as e:
        logger.error(f"Error procesando mensaje: {e}")
        return web.Response(status=500, text=str(e))

# Endpoint para servir el HTML
async def handle_root(request):
    try:
        with open("index Gemini.html", encoding="utf-8") as f:
            return web.Response(text=f.read(), content_type="text/html")
    except FileNotFoundError:
        return web.Response(status=404, text="index Gemini.html no encontrado")

# Inicializar app y rutas
app = web.Application()
app.router.add_get("/", handle_root)
app.router.add_post("/api/messages", handle_messages)
app.router.add_post("/api/messages/conversations", handle_create_conversation)

# Ejecutar servidor
if __name__ == "__main__":
    logger.info("\U0001F7E2 Servidor corriendo en http://localhost:8850")
    web.run_app(app, port=8850)
