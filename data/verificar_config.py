import os
import sqlite3
from openai import AzureOpenAI


DB_PATH = os.environ.get("BOT_DB_PATH", "soporte_db.db")
print(f"📁 Usando base de datos en: {DB_PATH}")

def cargar_parametros():
    if not os.path.exists(DB_PATH):
        print(f"❌ Base de datos no encontrada: {DB_PATH}")
        return {}

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("SELECT nombre_parametro, valor_parametro FROM parametros_seteos")
        data = dict(cursor.fetchall())
        print(f"✅ Se cargaron {len(data)} parámetros desde la base de datos.")
        return data

def test_openai_sdk(api_key, endpoint, deployment_name, api_version="2024-12-01-preview"):
    try:
        client = AzureOpenAI(
            api_key=api_key,
            azure_endpoint=endpoint,
            api_version=api_version,
        )

        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": "ping"},
                {"role": "user", "content": "ping"},
            ],
            max_tokens=1,
        )
        print("✅ Conexión a Azure OpenAI exitosa (usando SDK).")
        return True
    except OpenAIError as e:
        print(f"❌ Azure OpenAI error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado con Azure OpenAI: {e}")
        return False

def test_directline(secret):
    import requests
    url = "https://directline.botframework.com/v3/directline/tokens/generate"
    headers = {"Authorization": f"Bearer {secret}"}
    resp = requests.post(url, headers=headers)
    if resp.status_code == 200:
        print("✅ Direct Line Token generado correctamente.")
        return True
    print(f"❌ Error generando token de Direct Line ({resp.status_code}): {resp.text}")
    return False

def main():
    params = cargar_parametros()
    if not params:
        print("🚫 No se encontraron parámetros. Abortando.")
        return

    print("\n🔐 Validando configuración de Azure OpenAI:")
    test_openai_sdk(
        api_key=params.get("AZURE_OPENAI_API_KEY"),
        endpoint=params.get("AZURE_OPENAI_ENDPOINT"),
        deployment_name=params.get("AZURE_OPENAI_DEPLOYMENT_NAME"),
        api_version=params.get("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
    )

    if params.get("AZURE_OPENAI_DEPLOYMENT_NAME"):
        print("✅ Nombre del deployment OpenAI presente.")
    else:
        print("❌ Falta el nombre del deployment de OpenAI.")

    print("\n🧩 Validando credenciales del bot:")
    print("✅ MicrosoftAppId presente." if params.get("MicrosoftAppId") else "❌ MicrosoftAppId no encontrado.")
    if params.get("MicrosoftAppPassword") or params.get("MICROSOFT_APP_PASSWORD"):
        print("✅ MicrosoftAppPassword presente.")
    else:
        print("❌ MicrosoftAppPassword no encontrado.")

    print("\n🔗 Validando Direct Line:")
    test_directline(params.get("DIRECT_LINE_SECRET", ""))

    print("\n🌐 Validando endpoint del bot:")
    bot_url = params.get("BOT_ENDPOINT_URL")
    print(f"✅ BOT_ENDPOINT_URL definido: {bot_url}" if bot_url else "❌ BOT_ENDPOINT_URL no encontrado.")

if __name__ == "__main__":
    main()
