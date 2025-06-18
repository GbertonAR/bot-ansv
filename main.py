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
from dotenv import load_dotenv
import uuid

# --- Configuración de Logging ---
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
# --- Fin Configuración de Logging ---

load_dotenv()

app = web.Application()

# --- Configuración del Bot ---
BOT_PORT = int(os.getenv("BOT_PORT", 8850)) # Puerto para el servidor web
APP_ID = os.getenv("APP_ID")
APP_PASSWORD = os.getenv("APP_PASSWORD")

# Para fines de demostración, no necesitamos APP_ID ni APP_PASSWORD
# para la simulación local de Direct Line.
# Puedes dejarlos en None o vacío si solo vas a usar la simulación.
# APP_ID = None
# APP_PASSWORD = None


# --- SIMULACIÓN DE DIRECT LINE (PARA DESARROLLO LOCAL) ---
# Este diccionario simulará las conversaciones y actividades almacenadas.
# En un entorno de producción, esto sería una base de datos o un servicio de cola.
simulated_directline_data = {}

async def handle_create_conversation(request):
    """
    Simula el endpoint de Direct Line para crear una nueva conversación.
    Devuelve un conversationId y un token.
    """
    conversation_id = str(uuid.uuid4())
    # En un caso real, generarías un token de Direct Line seguro.
    # Para la simulación, cualquier cadena es suficiente.
    token = f"simulated_token_{conversation_id}"
    
    simulated_directline_data[conversation_id] = {
        "activities": [],
        "last_activity_time": datetime.datetime.now().isoformat()
    }
    
    logger.info(f"🆕 Conversación Direct Line simulada creada: {conversation_id}")
    
    response_payload = {
        "conversationId": conversation_id,
        "token": token,
        "expires_in": 3600, # Token válido por 1 hora (simulado)
        "streamUrl": f"http://127.0.0.1:{BOT_PORT}/directline/conversations/{conversation_id}/activities"
    }
    return web.json_response(response_payload, status=200)

# async def handle_directline_activities(request):
#     """
#     Simula los endpoints de Direct Line para enviar (POST) y recibir (GET - polling) actividades.
#     """
#     conversation_id = request.match_info.get("conversationId")

#     if request.method == "POST":
#         activity_data = await request.json()
        
#         logger.info(f"📥 Recibida actividad POST en conversación {conversation_id}: {json.dumps(activity_data, indent=2)}")

#         # --- FIX 2: Asegurar que conversation.id esté presente y sea correcto ---
#         # El Web Chat siempre debe enviar un objeto 'conversation' con 'id'.
#         # Si por alguna razón no viene (ej. un tipo de actividad muy específico o un error del cliente),
#         # nos aseguramos de que el ID de la conversación del URL sea el que se use.
#         if "conversation" not in activity_data or "id" not in activity_data["conversation"]:
#             logger.warning(f"Actividad POST sin conversation.id. Usando el de la URL: {conversation_id}")
#             if "conversation" not in activity_data:
#                 activity_data["conversation"] = {}
#             activity_data["conversation"]["id"] = conversation_id
        
#         # Asegurarse de que el ID de la conversación en la actividad coincida con el de la URL, por consistencia.
#         activity_data["conversation"]["id"] = conversation_id
#         # --- FIN FIX 2 ---
        
#         # Aquí es donde normalmente enviarías la actividad al bot real (Microsoft Bot Framework).
#         # Por ahora, simplemente la "almacenamos" en un diccionario simulado para polling.
#         if conversation_id not in simulated_directline_data:
#             simulated_directline_data[conversation_id] = {"activities": []}
        
#         simulated_directline_data[conversation_id]["activities"].append(activity_data)
#         simulated_directline_data[conversation_id]["last_activity_time"] = datetime.datetime.now().isoformat()

#         # Respuesta de éxito para POST de actividades
#         return web.json_response({}, status=200)

#     elif request.method == "GET":
#         # --- FIX 1: Manejo robusto del watermark ---
#         watermark_param = request.query.get("watermark")
        
#         try:
#             watermark = int(watermark_param) if watermark_param is not None and watermark_param != '' else 0
#         except ValueError:
#             logger.warning(f"Watermark inválido '{watermark_param}'. Usando 0.")
#             watermark = 0
#         # --- FIN FIX 1 ---

#         logger.info(f"📥 Recibida solicitud GET (Direct Line - polling) en /conversations/{conversation_id}/activities con watermark {watermark}")

#         # Para la simulación, devolver actividades desde el último watermark.
#         activities_to_return = []
#         if conversation_id in simulated_directline_data:
#             all_activities = simulated_directline_data[conversation_id]["activities"]
#             # Devolver actividades que tienen un índice mayor o igual al watermark
#             # (simulando que el watermark es el índice de la última actividad recibida)
#             activities_to_return = [act for i, act in enumerate(all_activities) if i >= watermark]

#         # Para mantener el polling funcionando, siempre incrementamos el watermark
#         # y devolvemos las actividades. El watermark debe ser único para cada conjunto de actividades.
#         # Una forma simple es usar la longitud actual de actividades si no se ha recibido nada,
#         # o el índice de la última actividad más 1 si se recibieron nuevas.
#         current_activities_count = len(simulated_directline_data.get(conversation_id, {}).get("activities", []))
#         next_watermark = current_activities_count # El siguiente watermark es la cantidad total de actividades

#         response_payload = {"activities": activities_to_return, "watermark": str(next_watermark)}
#         logger.info(f"📤 Respondiendo GET (Direct Line - polling) para conversación {conversation_id} con {len(activities_to_return)} actividades, nuevo watermark {next_watermark}")
#         return web.json_response(response_payload, status=200)

#     return web.Response(status=405, text="Method Not Allowed")

# Asegúrate de que 'simulated_directline_data' esté definido en algún lugar globalmente, por ejemplo:
# simulated_directline_data = {}

async def handle_directline_activities(request):
    conversation_id = request.match_info.get("conversationId")
    if not conversation_id or conversation_id not in simulated_directline_data:
        logger.error(f"Conversación {conversation_id} no encontrada para la solicitud {request.method} /activities.")
        raise web.HTTPNotFound(reason=f"Conversation {conversation_id} not found")

    conversation_state = simulated_directline_data[conversation_id]

    if request.method == 'GET':
        watermark = int(request.query.get("watermark", 0))
        # Filtra actividades solo si tienen un timestamp posterior al último watermark si watermark es un timestamp,
        # o si es un índice, simplemente toma desde ese índice.
        # Para esta simulación, watermark es un índice, así que toma desde watermark en adelante.
        activities_to_send = conversation_state['activities'][watermark:]
        new_watermark = len(conversation_state['activities'])

        logger.info(f"📥 Recibida solicitud GET (Direct Line - polling) en /conversations/{conversation_id}/activities con watermark {watermark}")
        response_data = {
            "activities": activities_to_send,
            "watermark": str(new_watermark)
        }
        logger.info(f"📤 Respondiendo GET (Direct Line - polling) para conversación {conversation_id} con {len(activities_to_send)} actividades, nuevo watermark {new_watermark}")
        return web.json_response(response_data)

    elif request.method == 'POST':
        try:
            incoming_activity = await request.json()
        except json.JSONDecodeError:
            logger.error(f"Error decodificando JSON en POST /conversations/{conversation_id}/activities")
            raise web.HTTPBadRequest(reason="Invalid JSON")

        # Asegúrate de que la actividad sea de tipo 'message' para responder a ella.
        if incoming_activity.get("type") == "message":
            # Si la actividad entrante no tiene conversation.id en su cuerpo, la tomamos de la URL
            if not incoming_activity.get("conversation", {}).get("id"):
                incoming_activity["conversation"] = {"id": conversation_id}
                logger.warning(f"Actividad POST sin conversation.id. Usando el de la URL: {conversation_id}")

            # Añadir la actividad del usuario a la lista de actividades de la conversación
            conversation_state['activities'].append(incoming_activity)
            logger.info(f"📥 Recibida actividad POST en conversación {conversation_id}: {json.dumps(incoming_activity, indent=2)}")

            # SIMULACIÓN: El bot responde al mensaje del usuario
            # En un bot real, esto sería gestionado por un SDK de bot o un servicio de IA
            # user_message_text = incoming_activity.get('text', '')
            # bot_response_text = f"Eco: {user_message_text}" if user_message_text else "Recibí tu mensaje (sin texto específico)."

            # bot_response_activity = {
            #     "type": "message",
            #     "from": {"id": "bot", "name": "Bot Simulador"}, # ID y nombre del bot
            #     "text": bot_response_text,
            #     "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            #     "id": str(uuid.uuid4()), # ID único para esta actividad
            #     "conversation": {"id": conversation_id} # Asegura que la actividad del bot también tenga el conversation ID
            # }
            # # Añadir la respuesta del bot a la lista de actividades
            # conversation_state['activities'].append(bot_response_activity)
            # logger.info(f"📤 Bot simulado responde en conversación {conversation_id}: {json.dumps(bot_response_activity, indent=2)}")

            user_message_text = incoming_activity.get('text', '')
            bot_response_text = f"Eco: {user_message_text}" if user_message_text else "Recibí tu mensaje (sin texto específico)."

            bot_response_activity = {
                "type": "message",
                "from": {"id": "bot", "name": "Bot Simulador"}, # ID y nombre del bot
                "text": bot_response_text,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "id": str(uuid.uuid4()), # ID único para esta actividad
                "conversation": {"id": conversation_id} # Asegura que la actividad del bot también tenga el conversation ID
            }
            # Añadir la respuesta del bot a la lista de actividades
            conversation_state['activities'].append(bot_response_activity)
            logger.info(f"📤 Bot simulado responde en conversación {conversation_id}: {json.dumps(bot_response_activity, indent=2)}")


            # Direct Line espera un objeto con un 'id' en la respuesta de un POST de actividad
            return web.json_response({"id": str(uuid.uuid4())}, status=200)
        else:
            logger.info(f"📥 Recibida actividad POST de tipo '{incoming_activity.get('type')}' en conversación {conversation_id}. No es un mensaje de texto. No se genera respuesta del bot.")
            # Si no es un mensaje de texto, simplemente acepta la actividad sin responder
            return web.json_response({"id": str(uuid.uuid4())}, status=200)

    else:
        logger.error(f"Método HTTP no permitido: {request.method} para /activities.")
        raise web.HTTPMethodNotAllowed(request.method, ["GET", "POST"])


# Nueva función para manejar la ruta raíz y servir index.html explícitamente
async def index_handler(request):
    """Sirve el archivo index.html explícitamente para la ruta raíz."""
    static_files_path = os.path.join(os.path.dirname(__file__), 'static')
    index_file_path = os.path.join(static_files_path, 'index.html')
    if os.path.exists(index_file_path):
        logger.info(f"🌐 Solicitud GET recibida en /. Sirviendo index.html desde '{index_file_path}'.")
        return web.FileResponse(index_file_path)
    else:
        logger.error(f"Error: index.html no encontrado en '{index_file_path}'.")
        raise web.HTTPNotFound(reason="index.html not found")

# --- Rutas del Servidor Web ---

# 1. Ruta específica para el index.html en la raíz
# ESTA LÍNEA DEBE IR ANTES DE CUALQUIER OTRA RUTA ESTÁTICA O DINÁMICA QUE PUEDA INTERCEPTAR '/'
app.router.add_get('/', index_handler)

# 2. Rutas para la creación de conversaciones (Direct Line)
app.router.add_post("/directline/conversations", handle_create_conversation)

# 3. Rutas para el manejo de actividades (Direct Line - polling)
app.router.add_post("/directline/conversations/{conversationId}/activities", handle_directline_activities)
app.router.add_get("/directline/conversations/{conversationId}/activities", handle_directline_activities)

# 4. Sirve otros archivos estáticos (CSS, JS, imágenes) desde la carpeta 'static' bajo el prefijo /static/
static_files_path = os.path.join(os.path.dirname(__file__), 'static')
if os.path.exists(static_files_path):
    # IMPORTANTE: Cambiado de app.router.add_static('/', ...) a app.router.add_static('/static/', ...)
    # Esto significa que los assets como 'user_avatar.png' deben ser referenciados como '/static/user_avatar.png' en tu HTML/CSS
    app.router.add_static('/static/', path=static_files_path, name='static_assets')
    logger.info(f"Serviendo archivos estáticos adicionales desde: {static_files_path} bajo el prefijo /static/")
else:
    logger.warning(f"La carpeta 'static' no se encontró en {static_files_path}. Los archivos estáticos no se servirán.")
    
if __name__ == "__main__":
    web.run_app(app, port=BOT_PORT)