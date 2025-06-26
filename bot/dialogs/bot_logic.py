###### BOT LOGIC FOR ANSV BOT ######
import os
import logging

from botbuilder.core import ActivityHandler, TurnContext, ConversationState, UserState, MessageFactory
from botbuilder.schema import ChannelAccount
from botbuilder.dialogs import Dialog, DialogSet, WaterfallDialog, TextPrompt, DialogTurnStatus

# Importar cliente de OpenAI (asegúrate de tener 'openai' instalado: pip install openai)
from openai import AsyncAzureOpenAI, AzureOpenAI # ¡CAMBIO CRÍTICO!
from dotenv import load_dotenv

# Cargar variables de entorno al inicio del archivo (esto está bien si también se usa .env)
load_dotenv()

# No longer using logging.basicConfig here. Logging is configured in app.py.
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

        if not self.AZURE_OPENAI_API_KEY or not self.AZURE_OPENAI_ENDPOINT or not self.AZURE_OPENAI_CHAT_DEPLOYMENT_NAME:
            logging.error("❌ Faltan credenciales de Azure OpenAI. El bot no podrá interactuar con el LLM.")
            self.openai_client = None
        else:
            try:
                self.openai_client = AsyncAzureOpenAI(
                    api_key=self.AZURE_OPENAI_API_KEY,
                    azure_endpoint=self.AZURE_OPENAI_ENDPOINT,
                    api_version="2024-02-15-preview" # O la versión que estés usando
                )
                logging.info("Cliente de Azure OpenAI inicializado correctamente.")
            except Exception as e:
                logging.error(f"❌ Error al inicializar el cliente de Azure OpenAI: {e}")
                self.openai_client = None

        self._add_dialogs()

    def _add_dialogs(self):
        """Añade los diálogos al conjunto de diálogos."""
        self.dialogs.add(TextPrompt("text_prompt"))
        self.dialogs.add(WaterfallDialog("main_dialog", [self.intro_step, self.handle_choice_step]))

    async def on_turn(self, turn_context: TurnContext):
        """
        Método principal que se ejecuta en cada turno de la conversación.
        """
        if turn_context.activity.type == "message":
            dialog_context = await self.dialogs.create_context(turn_context)

            if dialog_context.active_dialog is not None:
                await dialog_context.continue_dialog()
            else:
                await dialog_context.begin_dialog("main_dialog")

        elif turn_context.activity.type == "conversationUpdate":
            if turn_context.activity.members_added:
                for member in turn_context.activity.members_added:
                    if member.id != turn_context.activity.recipient.id:
                        await turn_context.send_activity(f"¡Hola! Soy tu asistente de soporte de la {os.environ.get('ORGANIZACION', 'Agencia Nacional de Seguridad Vial (ANSV)')}. ¿En qué puedo ayudarte hoy?")
                        await self.intro_step(turn_context, None) # Llama al paso de introducción para mostrar opciones
        await self.conversation_state.save_changes(turn_context)
        await self.user_state.save_changes(turn_context)

    async def intro_step(self, step_context, options):
        """Primer paso del diálogo, introduce al usuario y ofrece opciones."""
        # Se puede usar una tarjeta adaptativa para opciones más ricas
        # Por ahora, un simple mensaje con opciones de texto
        await step_context.context.send_activity("Puedo ayudarte con lo siguiente:")
        await step_context.context.send_activity("1. Consultar estado de trámite\n2. Preguntas frecuentes\n3. Contactar un agente")
        return Dialog.EndOfTurn

    async def handle_choice_step(self, step_context):
        """Maneja la elección del usuario."""
        user_input = step_context.context.activity.text.strip()
        
        if user_input == "1":
            await step_context.context.send_activity("Para consultar el estado de tu trámite, por favor, ingresa el número de expediente o DNI.")
        elif user_input == "2":
            await step_context.context.send_activity("Aquí tienes algunas preguntas frecuentes que podrían ayudarte:")
            # Aquí podrías integrar la consulta al LLM o a una base de conocimientos de FAQ
            llm_response = await self._query_llm("Dame 3 preguntas frecuentes sobre trámites de seguridad vial y sus respuestas concisas.")
            await step_context.context.send_activity(llm_response)
        elif user_input == "3":
            await step_context.context.send_activity("Entendido. Para contactar a un agente, por favor, envíame tu nombre completo, número de teléfono y una breve descripción de tu consulta para que podamos canalizarla.")
            # Aquí podrías iniciar otro diálogo para recopilar la información del usuario
            # Por ejemplo, usar un WaterfallDialog para pedir nombre, teléfono, etc.
        else:
            llm_response = await self._query_llm(f"El usuario preguntó: '{user_input}'. Responde de forma útil como asistente de la ANSV y sugiere las opciones principales nuevamente.")
            await step_context.context.send_activity(llm_response)

        return await step_context.end_dialog()

    async def _query_llm(self, prompt: str) -> str:
        """
        Función para realizar una consulta al LLM de Azure OpenAI.
        """
        if not self.openai_client:
            logging.error("Cliente de OpenAI no inicializado. No se puede consultar el LLM.")
            return "Lo siento, no puedo procesar tu solicitud en este momento. Parece que hay un problema con mi conexión de IA."

        try:
            logging.info(f"Iniciando consulta al LLM con prompt: {prompt[:50]}...")
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
            return "Lo siento, hubo un error al procesar tu solicitud de IA."