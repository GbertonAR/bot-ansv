# bot_logic.py
import logging
from botbuilder.core import ActivityHandler, TurnContext
from openai import AzureOpenAI

logger = logging.getLogger(__name__)

class BotANSV(ActivityHandler):
    def __init__(self, conversation_state, user_state, openai_api_key, openai_endpoint, openai_deployment):
        self.conversation_state = conversation_state
        self.user_state = user_state
        self.openai_api_key = openai_api_key
        self.openai_endpoint = openai_endpoint
        self.AZURE_OPENAI_CHAT_DEPLOYMENT_NAME = openai_deployment

        try:
            self.openai_client = AzureOpenAI(
                api_key=openai_api_key,
                azure_endpoint=openai_endpoint,
                api_version="2024-02-15-preview"
            )
            logger.info("Azure OpenAI client inicializado correctamente.")
        except Exception as e:
            self.openai_client = None
            logger.error(f"Error inicializando Azure OpenAI: {e}")

    async def on_message_activity(self, turn_context: TurnContext):
        text = turn_context.activity.text.strip().lower()

        if text in ["hola", "men\u00fa", "menu", "iniciar"]:
            await self._send_main_menu(turn_context)
        elif self.openai_client:
            response = await self._query_llm(text)
            await turn_context.send_activity(response)
        else:
            await turn_context.send_activity("El asistente no est\u00e1 disponible temporalmente.")

    async def _send_main_menu(self, turn_context: TurnContext):
        await turn_context.send_activity("\ud83c\udf10 Bienvenido al Asistente ANSV. Puedes hacerme preguntas como:\n- \u00bfC\u00f3mo saco mi licencia?\n- \u00bfCu\u00e1les son los requisitos para renovar?\n- \u00bfC\u00f3mo accedo al curso de seguridad vial?")

    async def _query_llm(self, prompt: str) -> str:
        try:
            logger.info(f"\ud83d\udd0d Consultando LLM con prompt: {prompt}")
            messages = [
                {"role": "system", "content": "Eres un asistente de soporte de la ANSV."},
                {"role": "user", "content": prompt}
            ]

            response = await self.openai_client.chat.completions.create(
                model=self.AZURE_OPENAI_CHAT_DEPLOYMENT_NAME,
                messages=messages,
                temperature=0.6,
                max_tokens=200
            )

            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"\u274c Error en LLM: {e}")
            return "Lo siento, hubo un error al contactar con la IA."
