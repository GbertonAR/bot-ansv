# update_secret.py
import sys
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from bot.services.db_service import set_parametro
    logger.info("Módulo db_service importado correctamente.")
except ImportError:
    logger.error("No se pudo importar db_service.py. Asegúrate de que el script esté en la raíz del proyecto o que la ruta sea correcta.")
    sys.exit(1)

# === REEMPLAZA ESTO CON TU SECRETO REAL DE DIRECT LINE COPIADO DE AZURE ===
NEW_DIRECT_LINE_SECRET = "TU_NUEVO_DIRECT_LINE_SECRET_COPIADO_DE_AZURE" # <--- ¡PEGA AQUÍ TU SECRETO DE AZURE!
# === FIN DE LA SECCIÓN A REEMPLAZAR ===

if NEW_DIRECT_LINE_SECRET == "TU_NUEVO_DIRECT_LINE_SECRET_COPIADO_DE_AZURE" or not NEW_DIRECT_LINE_SECRET:
    logger.error("Por favor, edita 'update_secret.py' y pega tu DIRECT_LINE_SECRET real de Azure.")
else:
    try:
        set_parametro("DIRECT_LINE_SECRET", NEW_DIRECT_LINE_SECRET)
        logger.info("✅ DIRECT_LINE_SECRET actualizado en la base de datos.")
    except Exception as e:
        logger.error(f"❌ Error al actualizar DIRECT_LINE_SECRET en la DB: {e}")
        import traceback
        traceback.print_exc()