# test_directline_connection.py
import asyncio
import httpx
import json
import os
from dotenv import load_dotenv

# Cargar variables de entorno para obtener el puerto del bot si es dinámico
load_dotenv()
BOT_PORT = int(os.getenv("PORT", 8850)) # Usa el mismo puerto que en config.py y main.py

async def test_directline_connection():
    """
    Intenta crear una conversación de Direct Line con el bot local.
    Verifica si el endpoint '/directline/conversations' está funcionando.
    """
    bot_host = f'http://127.0.0.1:{BOT_PORT}'
    conversation_creation_url = f'{bot_host}/directline/conversations'

    print(f"--- Iniciando prueba de conexión Direct Line ---")
    print(f"Intentando conectar con el bot en: {bot_host}")
    print(f"Endpoint de creación de conversación: {conversation_creation_url}")

    async with httpx.AsyncClient() as client:
        try:
            # 1. Intentar POST a /directline/conversations
            print(f"Enviando POST a {conversation_creation_url}...")
            response = await client.post(conversation_creation_url, timeout=10) # Añadir timeout

            print(f"Respuesta del servidor - Código de estado: {response.status_code}")
            
            if response.status_code == 200:
                print("¡Éxito! Conexión Direct Line establecida.")
                try:
                    data = response.json()
                    print(f"Datos recibidos:")
                    print(f"  conversationId: {data.get('conversationId')}")
                    print(f"  token: {data.get('token')}")
                    print(f"  expires_in: {data.get('expires_in')} segundos")
                    print(f"  streamUrl: {data.get('streamUrl')}")
                    print("\nEsto indica que tu bot está sirviendo correctamente el endpoint de Direct Line.")
                    #print("Si el Web Chat sigue fallando, revisa la configuración de 'domain' en index.html.")
                except json.JSONDecodeError:
                    print("Error: La respuesta no es un JSON válido.")
                    print(f"Contenido de la respuesta: {response.text[:500]}...") # Imprimir parte del contenido
            elif response.status_code == 404:
                print("Error: 404 Not Found.")
                print(f"Verifica que tu servidor bot está corriendo y que la ruta '{conversation_creation_url}'")
                print(f"está definida correctamente en main.py (debe ser app.router.add_post('/directline/conversations', ...)).")
                print(f"Si usas un prefijo diferente en main.py, ajústalo aquí.")
            else:
                print(f"Error inesperado: Código de estado {response.status_code}")
                print(f"Contenido de la respuesta: {response.text}")

        except httpx.ConnectError as e:
            print(f"Error de conexión: No se pudo conectar al bot en {bot_host}.")
            print("Asegúrate de que tu bot (main.py) esté corriendo antes de ejecutar este script.")
            print(f"Detalle: {e}")
        except httpx.TimeoutException:
            print(f"Error de tiempo de espera: El bot en {bot_host} no respondió a tiempo.")
            print("Verifica si el bot está procesando algo muy lento o si el firewall está bloqueando la conexión.")
        except Exception as e:
            print(f"Ocurrió un error inesperado: {e}")

if __name__ == "__main__":
    asyncio.run(test_directline_connection())
    print("\n--- Prueba de conexión Direct Line Finalizada ---")