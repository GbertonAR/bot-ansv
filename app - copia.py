import os
import asyncio
import datetime
import smtplib
from email.mime.text import MIMEText
from aiohttp import web
from typing import Callable, Awaitable
import json
import urllib.parse
import traceback # Importar traceback para depuración
from dotenv import load_dotenv # NUEVO: Importar load_dotenv para leer .env


# MODIFICACIÓN: Importar db_manager para interactuar con la DB de parámetros
from utils.db_manager import get_parameter, get_db_connection

# Cargar variables de entorno desde .env al inicio
load_dotenv()

# NUEVO: Importar el módulo logging
import logging

# NUEVO: Configuración básica del logging
# Crea un logger para tu aplicación
logger = logging.getLogger(__name__)
# Configura el nivel de logging (DEBUG para máxima verbosidad)
logger.setLevel(logging.DEBUG)
##############################################################
# Crea un handler para imprimir en la consola
console_handler = logging.StreamHandler()
# Configura el formato del mensaje
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
# Añade el handler al logger
logger.addHandler(console_handler)

# Puedes cambiar todos tus 'print' por 'logger.info', 'logger.debug', 'logger.warning', etc.
# Ejemplo: print("Cargando parámetros...") se convertiría en logger.info("Cargando parámetros...")

# MODIFICACIÓN: Importar db_manager (ya lo tienes)
from utils.db_manager import get_parameter, get_db_connection

# ... el resto de tu app.py ...

# Puedes usar logger.debug, logger.info, logger.warning, logger.error en tu código
# Ejemplo de uso en handle_messages:
async def handle_messages(request: web.Request):
    logger.debug(f"Received request headers: {request.headers}") # Ejemplo de uso
    # ... (resto de la función) ...

# Ejemplo de uso en load_bot_parameters:
async def load_bot_parameters():
    global AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_CHAT_MODEL_NAME, AZURE_OPENAI_EMBEDDING_MODEL_NAME
    global ORG_NOMBRE, ORG_DIRECCION, ORG_EMAIL, BOT_PORT

    logger.info("Cargando parámetros del bot desde la base de datos...")
    # ... (resto de la función) ...
    logger.info(f"Parámetros cargados: Endpoint OpenAI: {AZURE_OPENAI_ENDPOINT}") # Ejemplo

# Y en los try-except blocks:
# except sqlite3.Error as e:
#     logger.error(f"Error al leer parámetro '{key}' de la base de datos: {e}") # Usar logger.error
#     return None



###############################################################
# Asegúrate de que este archivo exista y esté configurado correctamente.
# Ejemplo de config_canje.py:
# MAIL_ACCOUNTS = {
#     "mesa_entradas": {
#         "email": "tu_email_remitente@gmail.com",
#         "password": "tu_contraseña_de_aplicacion_de_gmail"
#     }
# }
try:
    from config_canje import MAIL_ACCOUNTS
except ImportError:
    print("ADVERTENCIA: No se pudo importar 'config_canje'. La funcionalidad de envío de correo no funcionará.")
    MAIL_ACCOUNTS = {"mesa_entradas": {}} # Fallback para evitar errores de NameError

from botbuilder.core import (
    Bot,
    BotFrameworkAdapter,
    BotFrameworkAdapterSettings,
    TurnContext,
    MemoryStorage,
    ConversationState,
    UserState,
    MessageFactory,
    CardFactory,
)
from botbuilder.schema import Activity, ActivityTypes, HeroCard, CardAction, ActionTypes, CardImage, Attachment

import json # Para serializar styleOptions para el Web Chat
import urllib.parse 

ORG_NOMBRE = "Agencia Nacional de Seguridad Vial (ANSV)"
ORG_DIRECCION = "Av. Santa Fe 3968, C1425BHG CABA, Argentina"
ORG_EMAIL = "gberton1967@gmail.com" # Email genérico de ejemplo
BOT_PORT = int(os.environ.get("PORT", 8850)) # Puerto del bot, usado para construir URLs estáticas

# --- Configuración de Credenciales y Parámetros ---
# MODIFICACIÓN: Leer APP_ID, PASSWORD y AZURE_OPENAI_API_KEY desde .env (más seguro)
APP_ID = os.environ.get("BOT_APP_ID", "")
APP_PASSWORD = os.environ.get("BOT_APP_PASSWORD", "")
AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY", "") # Necesario para la IA

# NUEVO: Variables globales para parámetros leídos de la DB
AZURE_OPENAI_ENDPOINT = ""
AZURE_OPENAI_CHAT_MODEL_NAME = ""
AZURE_OPENAI_EMBEDDING_MODEL_NAME = ""
ORG_NOMBRE = ""
ORG_DIRECCION = ""
ORG_EMAIL = ""
BOT_PORT = 8850 # Valor por defecto, se intentará cargar de DB

# NUEVO: Función asíncrona para cargar los parámetros de la DB
async def load_bot_parameters():
    global AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_CHAT_MODEL_NAME, AZURE_OPENAI_EMBEDDING_MODEL_NAME
    global ORG_NOMBRE, ORG_DIRECCION, ORG_EMAIL, BOT_PORT

    print("Cargando parámetros del bot desde la base de datos...")
    AZURE_OPENAI_ENDPOINT = get_parameter('AZURE_OPENAI_ENDPOINT') or AZURE_OPENAI_ENDPOINT
    AZURE_OPENAI_CHAT_MODEL_NAME = get_parameter('AZURE_OPENAI_CHAT_MODEL_NAME') or AZURE_OPENAI_CHAT_MODEL_NAME
    AZURE_OPENAI_EMBEDDING_MODEL_NAME = get_parameter('AZURE_OPENAI_EMBEDDING_MODEL_NAME') or AZURE_OPENAI_EMBEDDING_MODEL_NAME
    ORG_NOMBRE = get_parameter('ORG_NOMBRE') or ORG_NOMBRE
    ORG_DIRECCION = get_parameter('ORG_DIRECCION') or ORG_DIRECCION
    ORG_EMAIL = get_parameter('ORG_EMAIL') or ORG_EMAIL
    
    db_port = get_parameter('BOT_PORT')
    if db_port:
        try:
            BOT_PORT = int(db_port)
        except ValueError:
            print(f"ADVERTENCIA: El puerto '{db_port}' en DB no es un número. Usando puerto por defecto: {BOT_PORT}")

    print(f"Parámetros cargados:")
    print(f"  Endpoint OpenAI: {AZURE_OPENAI_ENDPOINT}")
    print(f"  Modelo Chat: {AZURE_OPENAI_CHAT_MODEL_NAME}")
    print(f"  Puerto del Bot: {BOT_PORT}")
    print(f"  Organización: {ORG_NOMBRE}")
    print(f"  Email Org: {ORG_EMAIL}") # Añadir esta línea para confirmar la carga

# Define el tipo de la función de manejador para facilitar la tipificación
HandlerFunction = Callable[[TurnContext], Awaitable[None]]

# ========================== Clase principal del bot ==========================
class MyBot(Bot):
    def __init__(self, conversation_state: ConversationState, user_state: UserState):
        self.conversation_state = conversation_state
        self.user_state = user_state
        self.dialog_state = self.conversation_state.create_property("DialogState")
        
        # Diccionario para almacenar las rutas de los archivos de prueba
        # Estas rutas son relativas a la carpeta 'static'
        self.image_paths = {
            "objetivo": "objetivo.png", 
            "objetivo1": "objetivo1.png",
            "objetivo2": "objetivo2.png",
            "image_c4d26e": "image_c4d26e.png",
            "image_c4707d": "image_c4707d.png",
            "image_c63313": "image_c63313.png",
            "image_c64919": "image_c64919.png"
        }

    async def on_turn(self, turn_context: TurnContext):
        # Esta es la lógica principal que el bot ejecutará en cada turno.
        # Imprime la actividad entrante para depuración
        print(f"Actividad entrante: {turn_context.activity.type}")

        if turn_context.activity.type == ActivityTypes.MESSAGE:
            await self.on_message_activity(turn_context)
        elif turn_context.activity.type == ActivityTypes.CONVERSATION_UPDATE:
            await self.on_conversation_update_activity(turn_context)
        else:
            await turn_context.send_activity(
                Activity(
                    type=ActivityTypes.TRACE,
                    text=f"[{turn_context.activity.type}] activity detected"
                )
            )

    async def on_message_activity(self, turn_context: TurnContext):
        # Lógica para manejar mensajes entrantes
        user_message = turn_context.activity.text.strip().lower()
        print(f"Mensaje del usuario: '{user_message}'")

        if "hola" in user_message or "menu" in user_message or "start" in user_message:
            await self._send_main_menu(turn_context)
        elif "informacion" in user_message:
            await turn_context.send_activity("Has seleccionado 'Información ANSV'. Aquí podrás consultar sobre Licencias Nacionales de Conducir y documentación legal.")
            # Aquí iría la lógica para interactuar con la IA
            # (Más adelante integraremos la llamada a utils/llm_manager.py)
            await turn_context.send_activity("¿Sobre qué tema específico de la ANSV o LNC te gustaría informarte?")
        elif "tickets" in user_message or "soporte" in user_message:
            await turn_context.send_activity("Has seleccionado 'Soporte y Tickets'.")
            await self._send_ticket_options(turn_context)
        elif "crear ticket" in user_message:
            await turn_context.send_activity("Iniciando proceso para crear un nuevo ticket. Por favor, describe brevemente tu problema:")
            # Aquí iniciaríamos un diálogo para recopilar info del ticket
            # Por ahora, un placeholder
            await turn_context.send_activity("Función de creación de ticket en desarrollo.")
        elif "ver estado ticket" in user_message:
            await turn_context.send_activity("Por favor, ingresa el número de ticket que deseas consultar:")
            # Aquí iniciaríamos un diálogo para consultar el estado del ticket
            await turn_context.send_activity("Función de consulta de estado de ticket en desarrollo.")
        elif "documentos" in user_message:
            await turn_context.send_activity("Aquí tienes acceso a nuestra biblioteca de documentos. ¿Qué tipo de documento buscas?")
            await self._send_document_options(turn_context)
        elif "formularios" in user_message:
            await turn_context.send_activity("Aquí puedes completar formularios en línea. ¿Qué formulario necesitas?")
            # Aquí se podrían presentar Adaptive Cards de formularios
            await turn_context.send_activity("Función de formularios en desarrollo.")
        elif "contacto" in user_message or "email" in user_message:
            await self._send_contact_info(turn_context)
        elif "test image" in user_message: # NUEVA FUNCIONALIDAD: Testear imagenes adjuntas
            await self._send_test_images(turn_context)
        else:
            # MODIFICACIÓN FUTURA: Aquí se integrará la lógica del LLM con RAG
            # Por ahora, es una respuesta genérica
            await turn_context.send_activity(f"Lo siento, no entendí '{turn_context.activity.text}'. "
                                             f"Por favor, intenta con 'menú' para ver las opciones principales, o 'informacion' para consultar a la IA.")
        
        await self.conversation_state.save_changes(turn_context)
        await self.user_state.save_changes(turn_context)

    async def on_conversation_update_activity(self, turn_context: TurnContext):
        # Envía un mensaje de bienvenida solo si el bot se une a la conversación
        # o si hay un nuevo miembro que no sea el bot.
        if turn_context.activity.members_added:
            for member in turn_context.activity.members_added:
                if member.id != turn_context.activity.recipient.id:
                    await turn_context.send_activity(
                        "¡Hola! Soy el asistente virtual de la ANSV. ¿En qué puedo ayudarte hoy?"
                    )
                    await self._send_main_menu(turn_context) # Envía el menú principal al iniciar

    async def _send_main_menu(self, turn_context: TurnContext):
        # Crea y envía un Adaptive Card con el menú principal
        card = CardFactory.hero_card(
            HeroCard(
                title="Menú Principal",
                subtitle="Selecciona una opción para continuar:",
                images=[CardFactory.image(url=f"http://127.0.0.1:{BOT_PORT}/static/objetivo.png")], # Imagen principal
                buttons=[
                    CardAction(
                        type=ActionTypes.ImBack,
                        title="📚 Información ANSV",
                        value="informacion",
                    ),
                    CardAction(
                        type=ActionTypes.ImBack,
                        title="📝 Soporte y Tickets",
                        value="tickets",
                    ),
                    CardAction(
                        type=ActionTypes.ImBack,
                        title="📄 Documentos",
                        value="documentos",
                    ),
                    CardAction(
                        type=ActionTypes.ImBack,
                        title="✍️ Formularios",
                        value="formularios",
                    ),
                    CardAction(
                        type=ActionTypes.ImBack,
                        title="📧 Contacto", # Añadido el botón de Contacto
                        value="contacto",
                    ),
                ],
            )
        )
        reply = MessageFactory.attachment(card)
        await turn_context.send_activity(reply)

    async def _send_ticket_options(self, turn_context: TurnContext):
        # Opciones para la gestión de tickets
        card = CardFactory.hero_card(
            HeroCard(
                title="Opciones de Tickets",
                subtitle="¿Qué te gustaría hacer con los tickets?",
                buttons=[
                    CardAction(
                        type=ActionTypes.ImBack,
                        title="➕ Crear Ticket",
                        value="crear ticket",
                    ),
                    CardAction(
                        type=ActionTypes.ImBack,
                        title="🔍 Ver Estado Ticket",
                        value="ver estado ticket",
                    ),
                    CardAction(
                        type=ActionTypes.ImBack,
                        title="⬅️ Volver al Menú Principal",
                        value="menu",
                    ),
                ],
            )
        )
        reply = MessageFactory.attachment(card)
        await turn_context.send_activity(reply)

    async def _send_document_options(self, turn_context: TurnContext):
        # Opciones de documentos
        card = CardFactory.hero_card(
            HeroCard(
                title="Documentos Disponibles",
                subtitle="Elige un tipo de documento:",
                buttons=[
                    CardAction(
                        type=ActionTypes.ImBack,
                        title="⚖️ Normativa Legal",
                        value="normativa legal",
                    ),
                    CardAction(
                        type=ActionTypes.ImBack,
                        title="📊 Estadísticas",
                        value="estadisticas",
                    ),
                    CardAction(
                        type=ActionTypes.ImBack,
                        title="⬅️ Volver al Menú Principal",
                        value="menu",
                    ),
                ],
            )
        )
        reply = MessageFactory.attachment(card)
        await turn_context.send_activity(reply)

    async def _send_contact_info(self, turn_context: TurnContext):
        """
        Envía la información de contacto de la organización.
        """
        # Se utilizan las variables globales/cargadas al inicio del script.
        contact_message = (
            f"Claro, aquí tienes la información de contacto de la {ORG_NOMBRE}:\n\n"
            f"**Dirección:** {ORG_DIRECCION}\n"
            f"**Email:** {ORG_EMAIL}\n\n"
            "Puedes visitar nuestro sitio web oficial para más detalles. ¿Necesitas algo más?"
        )
        await turn_context.send_activity(MessageFactory.text(contact_message))

    async def _send_test_images(self, turn_context: TurnContext):
        """
        Envía una serie de Hero Cards con las imágenes de prueba.
        """
        # Para cada imagen en el diccionario, crea una Hero Card y envíala.
        # Asegúrate de que BOT_PORT esté definido globalmente o accesible aquí.
        attachments = []
        
        # Ejemplo de URL base, asumiendo que el servidor está en 127.0.0.1:BOT_PORT
        # turn_context.activity.recipient.name normalmente es '127.0.0.1' en desarrollo local
        # turn_context.activity.service_url puede ser 'http://localhost:8850' o similar
        base_url = f"http://{turn_context.activity.recipient.name}:{BOT_PORT}"
        # Puedes intentar también:
        # base_url = turn_context.activity.service_url.replace("api/messages", "") # Si service_url incluye la ruta api

        for name, path in self.image_paths.items():
            # Construye la URL completa para la imagen estática
            image_url = f"{base_url}/static/{path}"
            
            hero_card = CardFactory.hero_card(
                HeroCard(
                    title=f"Imagen de Prueba: {name.replace('_', ' ').title()}",
                    images=[CardFactory.image(url=image_url)],
                    buttons=[
                        CardAction(
                            type=ActionTypes.ImBack,
                            title="Volver al Menú",
                            value="menu",
                        )
                    ],
                )
            )
            attachments.append(CardFactory.attachment(hero_card))
        
        # Envía todas las Hero Cards como un solo mensaje de actividad (si el canal lo soporta)
        # O envía una por una si prefieres
        if attachments:
            await turn_context.send_activity(MessageFactory.list(attachments))
        else:
            await turn_context.send_activity("No se encontraron imágenes de prueba para mostrar.")


    async def on_conversation_update_activity(self, turn_context: TurnContext):
        # Lógica para manejar actualizaciones de la conversación (ej. bot añadido, usuario unido)
        if turn_context.activity.members_added:
            for member in turn_context.activity.members_added:
                if member.id != turn_context.activity.recipient.id:
                    # El bot fue añadido a la conversación o un nuevo usuario se unió
                    await turn_context.send_activity("¡Hola! Soy el Bot de Asistencia de la ANSV. ¿En qué puedo ayudarte hoy?")
                    await self._send_main_menu(turn_context)
        await self.conversation_state.save_changes(turn_context)
        await self.user_state.save_changes(turn_context)

    async def _send_main_menu(self, turn_context: TurnContext):
        # Crea una HeroCard para el menú principal
        card = HeroCard(
            title="Bienvenido al Bot de Asistencia de la ANSV",
            subtitle="¿En qué puedo ayudarte?",
            images=[CardImage(url=f"http://127.0.0.1:{BOT_PORT}/static/image_c4d26e.png")], # MODIFICACIÓN: Usar BOT_PORT
            buttons=[
                CardAction(type=ActionTypes.IM_BACK, title="📚 Información ANSV", value="informacion"),
                CardAction(type=ActionTypes.IM_BACK, title="🎟️ Soporte y Tickets", value="tickets"),
                CardAction(type=ActionTypes.IM_BACK, title="📄 Documentos", value="documentos"),
                CardAction(type=ActionTypes.IM_BACK, title="📝 Formularios", value="formularios"),
                CardAction(type=ActionTypes.IM_BACK, title="📧 Contacto", value="contacto"),
                CardAction(type=ActionTypes.IM_BACK, title="🔄 Menú Principal", value="menu")
            ]
        )
        # Crea un adjunto de tipo HeroCard
        attachment = CardFactory.hero_card(card)
        # Envía la actividad con el adjunto
        await turn_context.send_activity(MessageFactory.attachment(attachment))

    async def _send_ticket_options(self, turn_context: TurnContext):
        card = HeroCard(
            title="Opciones de Soporte",
            subtitle="¿Qué deseas hacer?",
            buttons=[
                CardAction(type=ActionTypes.IM_BACK, title="➕ Crear Ticket", value="crear ticket"),
                CardAction(type=ActionTypes.IM_BACK, title="❓ Ver Estado de Ticket", value="ver estado ticket"),
                CardAction(type=ActionTypes.IM_BACK, title="🔙 Volver al Menú", value="menu")
            ]
        )
        attachment = CardFactory.hero_card(card)
        await turn_context.send_activity(MessageFactory.attachment(attachment))

    async def _send_document_options(self, turn_context: TurnContext):
        card = HeroCard(
            title="Biblioteca de Documentos",
            subtitle="Selecciona una categoría o busca un documento:",
            buttons=[
                CardAction(type=ActionTypes.IM_BACK, title="🔎 Buscar por tema", value="buscar documento"),
                CardAction(type=ActionTypes.IM_BACK, title="📜 Licencias de Conducir", value="documentos licencias"),
                CardAction(type=ActionTypes.IM_BACK, title="⚖️ Normativa ANSV", value="documentos normativa"),
                CardAction(type=ActionTypes.IM_BACK, title="🔙 Volver al Menú", value="menu")
            ]
        )
        attachment = CardFactory.hero_card(card)
        await turn_context.send_activity(MessageFactory.attachment(attachment))

    async def _send_contact_info(self, turn_context: TurnContext):
        # MODIFICACIÓN: Usar variables globales cargadas de la DB
        contact_message = (
            f"Puedes contactarnos a través de:\n\n"
            f"**Nombre de la Organización:** {ORG_NOMBRE}\n"
            f"**Dirección:** {ORG_DIRECCION}\n"
            f"**Correo Electrónico:** {ORG_EMAIL}\n\n"
            "También puedes crear un ticket de soporte para asistencia personalizada."
        )
        await turn_context.send_activity(contact_message)
        await self._send_main_menu(turn_context) # Opcional: volver al menú después del contacto

    async def _send_test_images(self, turn_context: TurnContext):
        """Envía las imágenes de prueba adjuntas como actividades separadas."""
        await turn_context.send_activity("Aquí están las imágenes de prueba:")
        for name, path in self.image_paths.items():
            # Construir URL completa para la imagen servida estáticamente
            image_url = f"http://127.0.0.1:{BOT_PORT}/{path}"
            attachment = Attachment(
                name=name,
                contentType="image/png", # Asegúrate de que el tipo de contenido sea correcto
                contentUrl=image_url
            )
            message = MessageFactory.attachment(attachment)
            await turn_context.send_activity(message)
            print(f"Enviada imagen de prueba: {image_url}") # Para depuración


# Configuración del adaptador
settings = BotFrameworkAdapterSettings(
    app_id=APP_ID,
    app_password=APP_PASSWORD
)
adapter = BotFrameworkAdapter(settings)

# Manejo de errores del adaptador
async def on_error(turn_context: TurnContext, error: Exception):
    print(f"\n[on_turn_error] Error no controlado: {error}")
    traceback.print_exc() # Imprimir el stack trace completo para depuración
    await turn_context.send_activity("¡Lo siento! Algo salió mal. Por favor, intenta de nuevo.")
    # Envía un mensaje de error al usuario
    if turn_context.activity.channel_id == "emulator":
        await turn_context.send_activity(
            f"```\n{error}\n```"
        )
adapter.on_turn_error = on_error

# Configuración del estado
memory = MemoryStorage()
conversation_state = ConversationState(memory)
user_state = UserState(memory)

# Instancia del bot
mybot = MyBot(conversation_state, user_state)

# Ruta para manejar los mensajes del Bot Framework Service
async def handle_messages(request: web.Request):
    if "application/json" in request.headers["Content-Type"]:
        body = await request.json()
    else:
        body = await request.post()
    
    activity = Activity().deserialize(body)
    auth_header = request.headers.get("Authorization", "")
    
    response = await adapter.process_activity(activity, auth_header, mybot.on_turn)
    if response:
        return web.json_response(data=response.body, status=response.status)
    return web.Response(status=200)

# MODIFICACIÓN: Ruta para servir archivos estáticos (imágenes, etc.)
# Esto es crucial para que las imágenes de tus tests sean accesibles por el Web Chat
async def static_handler(request):
    file_path = os.path.join("static", request.match_info['name'])
    if not os.path.exists(file_path):
        return web.Response(status=404, text="Archivo no encontrado")
    
    # Determinar el tipo de contenido (solo para imágenes por ahora)
    if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
        content_type = "image/png" # Asume PNG por defecto si no se especifica
    else:
        content_type = "application/octet-stream" # Tipo genérico para otros archivos

    return web.FileResponse(file_path, headers={"Content-Type": content_type})

# Ruta para el Web Chat (ajustada para servir el index.html de static/)
async def handle_root(request: web.Request):
    html_file_path = os.path.join("static", "index.html")
    if not os.path.exists(html_file_path):
        return web.Response(status=404, text="index.html no encontrado en la carpeta 'static'.")
    
    # Enviar el archivo HTML directamente
    return web.FileResponse(html_file_path)

# NUEVO: Endpoint para la configuración del Web Chat (para obtener el token de Direct Line)
# Esto es necesario si index.html hace fetch('/chat-config')
async def chat_config(request: web.Request):
    # Aquí puedes generar un token de Direct Line si estás en un entorno de producción de Azure Bot Service.
    # Para desarrollo local, simplemente usa el APP_ID y APP_PASSWORD.
    # O, puedes usar un Direct Line Secret si tienes uno configurado para tu bot.
    # Por ahora, un placeholder.
    
    # Para simplicidad en desarrollo local, a menudo el Web Chat puede conectarse directamente
    # usando el APP_ID y APP_PASSWORD como secret, o un secret de Direct Line si está configurado en Azure.
    # Si vas a usar el endpoint /chat-config, necesitarás una librería para generar el token
    # de Direct Line, lo cual es un paso más avanzado.
    # Por ahora, asumiremos que el Web Chat se conectará con un secret o via emulator.
    
    # Si quieres que el Web Chat use un token real, necesitarás algo como esto (simplificado):
    # from botframework.connector.auth import JwtToken
    # direct_line_secret = os.environ.get("DIRECT_LINE_SECRET") # Deberías obtenerlo de Azure Direct Line
    # if not direct_line_secret:
    #     print("ADVERTENCIA: DIRECT_LINE_SECRET no configurado. El Web Chat en el navegador puede no funcionar.")
    #     token = None
    # else:
    #     # Esto es una simplificación; la generación real de token implica más pasos
    #     token = direct_line_secret # No es un JWT real, pero para prueba simple

    # Para el propósito de esta integración, el index.html en static/ ya está configurado
    # para intentar obtener un token de `/chat-config` o usar un ID de usuario fijo.
    # La solución más simple para desarrollo local es que el webchat no requiera token dinámico
    # o que uses el canal de Direct Line con un secreto real de tu bot.
    
    # Para que el Web Chat funcione con un token de Direct Line, normalmente se haría un fetch
    # a un endpoint que devuelve un token generado por el Direct Line API.
    # Por ahora, simplemente devolveremos un ID de usuario aleatorio para el Web Chat,
    # y el Web Chat se conectará sin un token de Direct Line si no se requiere por la configuración del bot.
    # Si quieres que el Web Chat se conecte con tu bot LOCAL, el secret del Web Chat
    # debe ser el mismo que el BOT_APP_PASSWORD en desarrollo, o usar un token real de Direct Line.
    
    # Para la prueba inicial, podemos simular que el Web Chat usa un UserID fijo.
    # El archivo static/index.html ya genera un UserID aleatorio.
    # Entonces, este endpoint podría no ser estrictamente necesario para la prueba local inicial
    # si el index.html ya tiene la lógica de conexión básica.
    
    # Si el index.html *realmente* necesita un token del backend:
    # return web.json_response({
    #     "token": "YOUR_DIRECT_LINE_TOKEN_HERE", # Esto vendría de una llamada a la API de Direct Line
    #     "directLineEndpoint": f"http://127.0.0.1:{BOT_PORT}/api/messages", # O tu endpoint de Azure
    #     "userID": f"user_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}" # ID de usuario único
    # })
    
    # Por ahora, para simplificar y alinear con el index.html ya generado, este endpoint puede
    # simplemente devolver una configuración básica.
    # El index.html ya genera un userID aleatorio y usa el endpoint /api/messages.
    # Por lo tanto, este handler de /chat-config puede ser muy simple o incluso omitido
    # si el Web Chat se conecta directamente a /api/messages.
    
    # Si el index.html espera un JSON de /chat-config, devolvemos uno simple:
    return web.json_response({
        "token": "YOUR_DIRECT_LINE_TOKEN_HERE_IF_NEEDED", # Placeholder
        "directLineEndpoint": "", # No es necesario si el Web Chat se conecta directamente al bot
        "userID": f"user_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    })


app = web.Application()
app.router.add_post("/api/messages", handle_messages) # Ruta para que el Bot Framework Service envíe mensajes
app.router.add_get("/", handle_root) # Ruta para mostrar el Web Chat
app.router.add_get("/static/{name}", static_handler) # NUEVO: Ruta para servir archivos estáticos
app.router.add_get("/chat-config", chat_config) # NUEVO: Ruta para la configuración del Web Chat


# ========================== ¡AGREGA ESTA LÍNEA! ==========================
# Ruta para servir archivos estáticos (imágenes, CSS, JS, etc.)
# Esto mapea la URL /static a la carpeta 'static' en tu proyecto.
app.router.add_static('/static/', path=os.path.join(os.path.dirname(__file__), 'static'))
# =========================================================================


# ========================== Punto de Entrada Principal ==========================\
def main():
    # Ejecutar load_bot_parameters de forma asíncrona ANTES de iniciar la app web.
    # asyncio.run() crea un nuevo bucle de eventos, lo ejecuta y lo cierra.
    # Esto asegura que no haya un bucle de eventos activo cuando web.run_app() se llame.
    try:
        asyncio.run(load_bot_parameters()) # <<< ESTA ES LA CLAVE: LLAMADA ASÍNCRONA AQUÍ
    except Exception as e:
        print(f"Error al cargar parámetros del bot desde la base de datos: {e}")
        traceback.print_exc()
        # Considera si la aplicación debe salir aquí si la configuración de la DB es crítica
        # Por ahora, permitimos que continúe con valores por defecto/vacíos si falla la carga.

    # Usamos la variable global BOT_PORT que se ha poblado
    port = BOT_PORT 
    
    print(f"🌐 Servidor del bot iniciado en http://127.0.0.1:{port}")
    print(f"🔗 Endpoint para el Bot Framework Service: http://127.0.0.1:{port}/api/messages")
    print(f"💬 Web Chat disponible en: http://127.0.0.1:{port}/\n")
    
    try:
        # web.run_app() se encarga de crear y gestionar su propio bucle de eventos.
        # NO SE DEBE LLAMAR asyncio.run() AQUÍ.
        web.run_app(app, host="127.0.0.1", port=port) # <<< ESTA ES LA CLAVE: LLAMADA DIRECTA AQUÍ
    except Exception as error:
        print(f"Error al iniciar la aplicación web: {error}")
        traceback.print_exc()

# Este es el punto de entrada real cuando ejecutas el script.
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nServidor detenido por el usuario.")
    except Exception as e:
        print(f"Error fatal en la ejecución principal: {e}")
        traceback.print_exc()
