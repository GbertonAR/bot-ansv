###### BOT LOGIC FOR ANSV BOT ######
import os
import logging
from botbuilder.core import ActivityHandler, TurnContext, ConversationState, UserState, MessageFactory
from botbuilder.schema import ChannelAccount
from botbuilder.dialogs import Dialog, DialogSet, WaterfallDialog, TextPrompt, DialogTurnStatus

# Importar cliente de OpenAI (asegúrate de tener 'openai' instalado: pip install openai)
from openai import AzureOpenAI
from dotenv import load_dotenv

# Cargar variables de entorno al inicio del archivo
load_dotenv()

# Configurar logging (opcional, pero buena práctica)
# Asegurarse de que el logging se configure solo una vez y de forma global
# Si ya tienes una configuración de logging en app.py, podrías omitir esta línea
# o ajustar el nivel según sea necesario.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BotANSV(ActivityHandler):
    def __init__(self, 
                 conversation_state: ConversationState, 
                 user_state: UserState,
                 openai_api_key: str = None, 
                 openai_endpoint: str = None,
                 openai_chat_deployment_name: str = None):
        self.conversation_state = conversation_state
        self.user_state = user_state
        self.dialog_state = self.conversation_state.create_property("DialogState")
        self.dialogs = DialogSet(self.dialog_state)

        # ASIGNAR LAS CREDENCIALES DIRECTAMENTE DESDE LOS PARÁMETROS DEL CONSTRUCTOR
        # ESTO ES LO QUE ESTAMOS PASANDO DESDE app.py
        self.AZURE_OPENAI_API_KEY = openai_api_key
        self.AZURE_OPENAI_ENDPOINT = openai_endpoint
        self.AZURE_OPENAI_CHAT_DEPLOYMENT_NAME = openai_chat_deployment_name
        
        # === DEPURACIÓN DE CREDENCIALES DE AZURE OPENAI EN BOT_LOGIC ===
        # Manejo de None en la depuración del API Key
        api_key_debug = self.AZURE_OPENAI_API_KEY[-4:] if self.AZURE_OPENAI_API_KEY else 'N/A'
        logging.info(f"DEBUG_BL: AZURE_OPENAI_API_KEY (últimos 4) = '...{api_key_debug}'")
        logging.info(f"DEBUG_BL: AZURE_OPENAI_ENDPOINT = '{self.AZURE_OPENAI_ENDPOINT}'")
        logging.info(f"DEBUG_BL: AZURE_OPENAI_CHAT_DEPLOYMENT_NAME = '{self.AZURE_OPENAI_CHAT_DEPLOYMENT_NAME}'")
        # =============================================================        
        
        # Inicializar el cliente de Azure OpenAI aquí
        if self.AZURE_OPENAI_API_KEY and self.AZURE_OPENAI_ENDPOINT and self.AZURE_OPENAI_CHAT_DEPLOYMENT_NAME:
            try:
                self.openai_client = AzureOpenAI(
                    api_key=self.AZURE_OPENAI_API_KEY,  
                    azure_endpoint=self.AZURE_OPENAI_ENDPOINT,
                    api_version="2025-01-01-preview" # O la versión de API que estés usando
                )
                logging.info("Cliente de Azure OpenAI inicializado correctamente.")
            except Exception as e:
                self.openai_client = None
                logging.error(f"Error al inicializar el cliente de Azure OpenAI: {e}")
                logging.warning("El LLM no funcionará debido a un error de inicialización.")
        else:
            self.openai_client = None
            logging.warning("Credenciales de Azure OpenAI incompletas en bot_logic. El LLM no funcionará. Verifique app.py o .env.")

        # Puedes añadir diálogos si los tienes definidos
        # self.dialogs.add(MainDialog(self.conversation_state, self.user_state))

    async def on_members_added_activity(self, members_added: [ChannelAccount], turn_context: TurnContext):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                # Mensaje de bienvenida más explícito
                await turn_context.send_activity("¡Hola! Soy el bot de soporte de la ANSV. Escribe 'hola' o 'menú' para ver las opciones disponibles.")
                # Aquí puedes mostrar un Adaptive Card de bienvenida si es tu comportamiento por defecto
                await self._send_main_menu(turn_context) # Esto enviará el mensaje del menú principal

    async def on_message_activity(self, turn_context: TurnContext):
        # ¡¡¡NUEVA LÍNEA DE PRUEBA!!!
        print(f"\n--- MENSAJE RECIBIDO EN on_message_activity: {turn_context.activity.text} ---") 
        # ¡¡¡FIN NUEVA LÍNEA DE PRUEBA!!!

        user_message = turn_context.activity.text.lower()
        logging.info(f"Mensaje del usuario: {user_message}")

        if user_message == "hola" or user_message == "menú" or user_message == "iniciar":
            await self._send_main_menu(turn_context)
        else:
            # Aquí es donde integramos la llamada al LLM
            if self.openai_client:
                logging.info(f"Enviando mensaje a LLM: {turn_context.activity.text}")
                llm_response = await self._query_llm(turn_context.activity.text)
                await turn_context.send_activity(llm_response)
            else:
                # Si llegamos aquí, es que self.openai_client es None
                # Se garantiza una respuesta para confirmar que el bot funciona
                await turn_context.send_activity(
                    "No entendí tu mensaje. Escribe 'hola', 'iniciar' o 'menú' para ver opciones. "
                    "(Nota: El LLM no está configurado, así que no puedo responder preguntas complejas.)"
                )

        # Guarda el estado de la conversación (opcional, pero buena práctica)
        await self.conversation_state.save_changes(turn_context)

    async def _send_main_menu(self, turn_context: TurnContext):
        # Aquí iría el código para enviar tu Adaptive Card de Menú Principal
        # Por ahora, un simple mensaje de texto de confirmación
        await turn_context.send_activity("Estas son las opciones del menú principal:")
        # Ejemplo: await turn_context.send_activity(Activity(attachments=[self._create_main_menu_card()]))
        # Puedes añadir más mensajes aquí para simular el menú, e.g.:
        # await turn_context.send_activity("1. Consultar estado de trámite\n2. Preguntas frecuentes\n3. Contactar un agente")


    async def _query_llm(self, prompt: str) -> str:
        """
        Función para realizar una consulta al LLM de Azure OpenAI.
        """
        try:
            logging.info(f"Iniciando consulta al LLM con prompt: {prompt[:50]}...") # Nuevo log para ver si entra aquí
            # Aquí construyes la lista de mensajes para el LLM
            messages = [
                {"role": "system", "content": "Eres un asistente de soporte de la Agencia Nacional de Seguridad Vial (ANSV). Responde de forma concisa y útil."},
                {"role": "user", "content": prompt}
            ]
            
            # Realizar la llamada a Azure OpenAI
            response = await self.openai_client.chat.completions.create(
                model=self.AZURE_OPENAI_CHAT_DEPLOYMENT_NAME,
                messages=messages,
                temperature=0.7, # Controla la creatividad de la respuesta
                max_tokens=150   # Límite de tokens en la respuesta
            )
            
            llm_text_response = response.choices[0].message.content
            logging.info(f"Respuesta del LLM: {llm_text_response}")
            return llm_text_response

        except Exception as e:
            logging.error(f"Error al consultar el LLM: {e}")
            return "Lo siento, no pude conectar con la IA en este momento. Por favor, intenta de nuevo más tarde."