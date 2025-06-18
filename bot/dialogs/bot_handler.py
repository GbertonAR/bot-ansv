# bot/bot_handler.py
import logging
from botbuilder.core import ActivityHandler, TurnContext
from botbuilder.schema import ChannelAccount, ActivityTypes
from bot_logic import BotANSV # Importa tu lógica de bot

logger = logging.getLogger(__name__)

class MyBotActivityHandler(ActivityHandler):
    def __init__(self):
        self.bot_logic = ANSVBotLogic() # Instancia tu lógica de bot aquí

    async def on_members_added_activity(
        self,
        members_added: [ChannelAccount],
        turn_context: TurnContext
    ):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity(
                    f"¡Hola! Soy tu asistente virtual de ANSV. ¿En qué puedo ayudarte?"
                )
                await self.bot_logic._send_main_menu(turn_context) # Envía el menú al inicio

    async def on_message_activity(self, turn_context: TurnContext):
        logger.info(f"--- MENSAJE RECIBIDO EN on_message_activity: {turn_context.activity.text} ---")
        await self.bot_logic.on_message_activity(turn_context)

    # Puedes añadir más métodos como on_end_of_conversation_activity, etc.