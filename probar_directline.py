import requests

direct_line_secret = ""  # pegá aquí la clave copiada

url = "https://directline.botframework.com/v3/directline/tokens/generate"
headers = {
    "Authorization": f"Bearer {direct_line_secret}"
}

response = requests.post(url, headers=headers)

print(response.status_code)
print(response.json())
