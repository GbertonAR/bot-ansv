# services/mail_service.py

import os
import asyncio
import smtplib
from email.mime.text import MIMEText

# === Configuración de Cuentas de Correo ===
# Cargar esto desde variables de entorno es más seguro en producción.
# Para desarrollo, puedes ponerlo aquí o en un archivo de configuración que no se suba al control de versiones.

# Si usas config_canje.py para esto, asegúrate de que esté en una ubicación accesible
# (ej. en la raíz de tu proyecto, o ajustar el path si lo pones en otro lugar).
try:
    from config_canje import MAIL_ACCOUNTS
except ImportError:
    print("ADVERTENCIA: No se pudo importar 'config_canje'. La funcionalidad de envío de correo no funcionará.")
    MAIL_ACCOUNTS = {"mesa_entradas": {}} # Fallback para evitar errores de NameError

async def send_email_async(
    subject: str,
    body: str,
    to_email: str,
    from_account_name: str = "mesa_entradas"
):
    """
    Envía un correo electrónico de forma asíncrona.
    :param subject: Asunto del correo.
    :param body: Cuerpo del correo.
    :param to_email: Dirección de correo del destinatario.
    :param from_account_name: Nombre de la cuenta remitente configurada en MAIL_ACCOUNTS.
    """
    account = MAIL_ACCOUNTS.get(from_account_name)
    if not account:
        raise ValueError(f"Cuenta de correo '{from_account_name}' no configurada.")

    sender_email = account.get("email")
    sender_password = account.get("password")

    if not sender_email or not sender_password:
        raise ValueError(f"Credenciales de correo incompletas para la cuenta '{from_account_name}'.")

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = to_email

    try:
        # Usamos asyncio.to_thread para ejecutar smtplib (que es bloqueante) en un hilo separado
        # sin bloquear el bucle de eventos principal de aiohttp.
        await asyncio.to_thread(
            _send_email_sync, sender_email, sender_password, to_email, msg
        )
        print(f"Correo enviado con éxito a {to_email}")
    except Exception as e:
        print(f"Error al enviar correo: {e}")
        raise # Re-lanza la excepción para que el llamador pueda manejarla

def _send_email_sync(sender_email, sender_password, to_email, msg):
    """Función de ayuda síncrona para smtplib."""
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(sender_email, sender_password)
        smtp.send_message(msg)