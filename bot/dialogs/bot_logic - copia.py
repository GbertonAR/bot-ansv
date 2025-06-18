# bot/bot_logic.py

import os
import asyncio
import datetime
import json
import urllib.parse
from botbuilder.core import (
    ActivityHandler,
    TurnContext,
    MessageFactory,
    CardFactory,
    ConversationState, # <-- Añade esta importación
    UserState,         # <-- Añade esta importación
)
from botbuilder.schema import (
    Activity,
    ActivityTypes,
    HeroCard,
    CardAction,
    ActionTypes,
    ChannelAccount,    # <-- Asegúrate de que esta importación exista
    CardImage          # <-- Asegúrate de que esta importación exista si usas imágenes en tarjetas
)

# Importar la función de envío de correo desde services
#from services.mail_service import send_email_async
from ..services.mail_service import send_email_async

# === Lógica del Bot ===
class BotANSV(ActivityHandler):
    def __init__(self, conversation_state: ConversationState, user_state: UserState):
        if conversation_state is None:
            raise TypeError(
                "[DialogBot]: Missing parameter. conversation_state is required"
            )
        if user_state is None:
            raise TypeError(
                "[DialogBot]: Missing parameter. user_state is required"
            )

        self.conversation_state = conversation_state
        self.user_state = user_state

    async def on_members_added_activity(
        self,
        members_added: [ChannelAccount],
        turn_context: TurnContext
    ):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                welcome_message = MessageFactory.text(
                    "¡Hola! Soy el Bot de la ANSV. Estoy aquí para ayudarte con tus consultas. "
                    "¿En qué puedo asistirte hoy?"
                )
                await turn_context.send_activity(welcome_message)

    async def on_message_activity(self, turn_context: TurnContext):
        user_message = turn_context.activity.text.lower().strip()

        if user_message == "menu principal":
            await self._send_main_menu(turn_context)
        elif user_message == "consultar licencia":
            await turn_context.send_activity("Para consultar tu licencia, necesito que me proporciones tu DNI y el número de trámite (si lo tienes).")
            await turn_context.send_activity("Por favor, ingresa tu DNI:")
        elif user_message == "sacar turno":
            await turn_context.send_activity("Para sacar un turno, por favor, visita nuestra página oficial: [www.ansv.gob.ar/turnos](https://www.ansv.gob.ar/turnos)")
        elif user_message == "estado de tramite":
            await turn_context.send_activity("Para conocer el estado de tu trámite, por favor, visita nuestra sección de seguimiento: [www.ansv.gob.ar/seguimiento](https://www.ansv.gob.ar/seguimiento)")
        elif user_message == "contacto":
            await turn_context.send_activity("Puedes contactarnos por teléfono al 0800-XXX-XXXX o enviarnos un correo a contacto@ansv.gob.ar")
        elif user_message == "ver objetivos":
            await self._send_objective_cards(turn_context)
        elif user_message == "enviar consulta":
            await self._initiate_email_flow(turn_context)
        elif user_message == "ayuda":
            await self._send_main_menu(turn_context)
        elif "cancelar" in user_message:
            await self._cancel_current_flow(turn_context)
        else:
            # Aquí podrías integrar la lógica del LLM si el mensaje no coincide con un comando conocido
            await turn_context.send_activity(
                "No entiendo tu consulta. Por favor, selecciona una opción del menú principal o escribe 'ayuda'."
            )
            await self._send_main_menu(turn_context) # Siempre mostrar el menú principal al final de un mensaje no reconocido

        # Guarda los cambios de estado al final de cada turno
        await self.conversation_state.save_changes(turn_context)
        await self.user_state.save_changes(turn_context)

    async def _send_main_menu(self, turn_context: TurnContext):
        card = CardFactory.hero_card(
            HeroCard(
                title="Menú Principal",
                text="¿En qué puedo ayudarte?",
                buttons=[
                    CardAction(
                        type=ActionTypes.ImBack,
                        title="Consultar Licencia",
                        value="Consultar Licencia",
                    ),
                    CardAction(
                        type=ActionTypes.ImBack,
                        title="Sacar Turno",
                        value="Sacar Turno",
                    ),
                    CardAction(
                        type=ActionTypes.ImBack,
                        title="Estado de Tramite",
                        value="Estado de Tramite",
                    ),
                    CardAction(
                        type=ActionTypes.ImBack,
                        title="Contacto",
                        value="Contacto",
                    ),
                    CardAction(
                        type=ActionTypes.ImBack,
                        title="Ver Objetivos",
                        value="Ver Objetivos",
                    ),
                    CardAction(
                        type=ActionTypes.ImBack,
                        title="Enviar Consulta",
                        value="Enviar Consulta",
                    ),
                ],
            )
        )
        await turn_context.send_activity(MessageFactory.attachment(card))

    async def _send_objective_cards(self, turn_context: TurnContext):
        # Asegúrate de que estas rutas sean correctas para los archivos en static/
        objective_cards = [
            CardFactory.hero_card(
                HeroCard(
                    title="Objetivo 1: Reducción de Siniestros",
                    text="Promovemos la seguridad vial y la reducción de siniestros en el territorio nacional.",
                    images=[CardImage(url=f"{turn_context.activity.service_url}static/objetivo.png")],
                )
            ),
            CardFactory.hero_card(
                HeroCard(
                    title="Objetivo 2: Educación Vial",
                    text="Fomentamos la educación y concientización sobre la importancia de la seguridad vial.",
                    images=[CardImage(url=f"{turn_context.activity.service_url}static/objetivo1.png")],
                )
            ),
            CardFactory.hero_card(
                HeroCard(
                    title="Objetivo 3: Control y Fiscalización",
                    text="Fortalecemos los controles y la fiscalización para asegurar el cumplimiento de las normativas de tránsito.",
                    images=[CardImage(url=f"{turn_context.activity.service_url}static/objetivo2.png")],
                )
            ),
        ]
        await turn_context.send_activity(MessageFactory.carousel(objective_cards))

    async def _initiate_email_flow(self, turn_context: TurnContext):
        conversation_data = await self.conversation_state.get(turn_context, {})
        conversation_data["email_flow_active"] = True
        conversation_data["email_step"] = "ask_subject"
        await turn_context.send_activity("Comenzando el proceso para enviar una consulta por correo. Puedes decir 'cancelar' en cualquier momento.")
        await turn_context.send_activity("Por favor, ingresa el asunto de tu consulta:")

    async def _handle_email_flow(self, turn_context: TurnContext):
        conversation_data = await self.conversation_state.get(turn_context, {})
        user_message = turn_context.activity.text.strip()

        current_step = conversation_data.get("email_step")

        if current_step == "ask_subject":
            conversation_data["email_subject"] = user_message
            conversation_data["email_step"] = "ask_body"
            await turn_context.send_activity("Ahora, por favor, ingresa el cuerpo de tu consulta:")
        elif current_step == "ask_body":
            conversation_data["email_body"] = user_message
            conversation_data["email_step"] = "ask_confirmation"
            await turn_context.send_activity(f"Asunto: {conversation_data['email_subject']}")
            await turn_context.send_activity(f"Cuerpo: {conversation_data['email_body']}")
            await turn_context.send_activity("¿Es correcto? (Sí/No)")
        elif current_step == "ask_confirmation":
            if user_message.lower() == "sí" or user_message.lower() == "si":
                try:
                    await send_email_async(
                        subject=conversation_data["email_subject"],
                        body=conversation_data["email_body"],
                        to_email="tu_email_destino@example.com" # CAMBIA ESTO AL EMAIL DE DESTINO REAL
                    )
                    await turn_context.send_activity("Tu consulta ha sido enviada con éxito. En breve recibirás una respuesta.")
                except Exception as e:
                    await turn_context.send_activity(f"Lo siento, hubo un error al enviar tu consulta: {e}")
                finally:
                    await self._reset_email_flow(turn_context)
            else:
                await turn_context.send_activity("Envío de correo cancelado. ¿Hay algo más en lo que pueda ayudarte?")
                await self._reset_email_flow(turn_context)
        else:
            await turn_context.send_activity("Algo salió mal en el flujo de correo. Por favor, intenta de nuevo o escribe 'cancelar'.")

    async def _reset_email_flow(self, turn_context: TurnContext):
        conversation_data = await self.conversation_state.get(turn_context, {})
        conversation_data["email_flow_active"] = False
        conversation_data["email_step"] = None
        conversation_data["email_subject"] = None
        conversation_data["email_body"] = None
        await self.conversation_state.save_changes(turn_context)
        await self._send_main_menu(turn_context) # Volver al menú principal

    async def _cancel_current_flow(self, turn_context: TurnContext):
        conversation_data = await self.conversation_state.get(turn_context, {})
        if conversation_data.get("email_flow_active"):
            await self._reset_email_flow(turn_context)
            await turn_context.send_activity("Proceso de envío de correo cancelado.")
        else:
            await turn_context.send_activity("No hay ningún proceso activo para cancelar.")
        await self._send_main_menu(turn_context)


    async def on_turn(self, turn_context: TurnContext):
        # Mover la lógica del flujo de correo aquí
        conversation_data = await self.conversation_state.get(turn_context, {})
        if conversation_data.get("email_flow_active"):
            await self._handle_email_flow(turn_context)
        else:
            # Llama al método base on_turn para manejar las actividades normales
            await super().on_turn(turn_context)