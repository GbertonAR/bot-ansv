# bot_adapter.py
import logging
from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings
from functools import wraps
from botbuilder.schema import Activity, ActivityTypes
from botbuilder.core.turn_context import TurnContext

logger = logging.getLogger(__name__)

def create_adapter(app_id: str, app_password: str):
    """Crea y configura el BotFrameworkAdapter."""
    settings = BotFrameworkAdapterSettings(app_id, app_password)
    adapter = BotFrameworkAdapter(settings)

    # Decorador para envolver send_activity y capturar logs
    # Este decorador se aplica a adapter.send_activities
    def wrapped_send_activities(func):
        @wraps(func)
        async def wrapper(self, turn_context: TurnContext, activities: list, **kwargs):
            for activity_obj in activities:
                if isinstance(activity_obj, Activity):
                    # Accede al ID de la conversación desde la actividad entrante original en el TurnContext
                    # 'turn_context' se pasa directamente aquí
                    conv_id = "N/A"
                    if turn_context.activity and turn_context.activity.conversation and turn_context.activity.conversation.id:
                        conv_id = turn_context.activity.conversation.id
                    
                    text = activity_obj.text if activity_obj.text else 'N/A'
                    activity_type = activity_obj.type if activity_obj.type else 'N/A'
                    
                    logger.info(f"📤 [Wrapped] Capturando actividad saliente para conv '{conv_id}': Tipo={activity_type}, Texto='{text}'")
                else:
                    logger.info(f"📤 [Wrapped] Capturando actividad saliente: Objeto no es tipo Activity. Tipo: {type(activity_obj)}")

            # Llamar a la función original de adapter.send_activities
            return await func(self, turn_context, activities, **kwargs)
        return wrapper

    # Aplicar el decorador a adapter.send_activities
    # NOTA: El decorador que tenías en app.py estaba aplicado a ActivityHandler.send_activity.
    # El Adapter.send_activities es donde el SDK realmente maneja el envío.
    # Necesitaríamos revisar si el error de 'NoneType' persistía en el ActivityHandler si se quitara de app.py y se probara aquí.
    # Por ahora, dejo la corrección aquí para el log.
    adapter.send_activities = wrapped_send_activities(adapter.send_activities)

    # Manejador de errores
    async def on_error(context: TurnContext, error: Exception):
        logger.error(f"Error inesperado: {error}", exc_info=True)
        await context.send_activity("¡Oops! Parece que algo salió mal. Por favor, inténtalo de nuevo más tarde.")
        # Envía un trace activity, que será capturado por el Bot Framework Emulator
        # Si estás usando Application Insights, esto aparecerá en tus logs.
        await context.send_trace_activity(
            name="OnTurnError",
            value=error,
            value_type="https://www.botframework.com/schemas/error",
        )

    adapter.on_turn_error = on_error
    return adapter