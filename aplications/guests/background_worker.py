import os
import json
import time
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from datetime import datetime
from aplications.guests.models import ModelGoogleGuest, RespondedMessage
from aplications.guests.utils import consulta_chatgpt
from dotenv import load_dotenv

load_dotenv()

SCOPES = [
    'https://www.googleapis.com/auth/chat.spaces',
    'https://www.googleapis.com/auth/chat.messages',
    'https://www.googleapis.com/auth/chat.messages.readonly',
]
CREDENTIALS_FILE = os.path.join("credentials", "user_credentials.json")
BOT_USER_ID = "users/112568225339349392647"


def load_credentials():
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, 'r') as file:
            creds_data = json.load(file)
        try:
            credentials = Credentials.from_authorized_user_info(creds_data, SCOPES)
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                print("Token refrescado exitosamente")
                with open(CREDENTIALS_FILE, 'w') as file:
                    json.dump({
                        'token': credentials.token,
                        'refresh_token': credentials.refresh_token,
                        'token_uri': credentials.token_uri,
                        'client_id': credentials.client_id,
                        'client_secret': credentials.client_secret,
                        'scopes': credentials.scopes,
                    }, file)
            return credentials
        except Exception as e:
            print(f"Error al cargar o refrescar credenciales: {e}")
            return None
    return None


def background_worker():
    credentials = load_credentials()
    if not credentials:
        print("No se pudieron cargar las credenciales. Worker detenido.")
        return

    try:
        service = build("chat", "v1", credentials=credentials)
        print("Servicio de Google Chat configurado.")
    except Exception as e:
        print(f"Error al configurar Google Chat: {e}")
        return

    while True:
        try:
            guests = ModelGoogleGuest.objects.all()
            for guest in guests:
                space_name = f"spaces/{guest.space.strip()}"
                response = service.spaces().messages().list(
                    parent=space_name,
                    pageSize=1000  # Traer varios mensajes recientes
                ).execute()

                messages = response.get('messages', [])

                # Filtrar mensajes que no sean del bot
                user_messages = [
                    msg for msg in messages
                    if msg['sender']['name'] != BOT_USER_ID and 'text' in msg
                ]

                # Ordenar los mensajes por fecha de creación (más recientes primero)
                user_messages = sorted(
                    user_messages,
                    key=lambda x: x['createTime'],
                    reverse=True
                )

                if user_messages:
                    # Tomar el último mensaje del usuario
                    last_message = user_messages[0]
                    message_id = last_message['name']
                    sender_id = last_message['sender']['name']
                    message_text = last_message['text']
                    created_time = last_message['createTime']

                    print(f"[DEBUG] Último mensaje del usuario detectado en espacio {space_name}:")
                    print(f"  - ID Mensaje: {message_id}")
                    print(f"  - Remitente: {sender_id}")
                    print(f"  - Texto: {message_text}")
                    print(f"  - Fecha de creación: {created_time}")

                    # Verificar si ya se respondió el mensaje
                    if not RespondedMessage.objects.filter(message_id=message_id).exists():
                        print(f"[DEBUG] Generando respuesta para el mensaje: {message_text}")

                        # Generar respuesta usando ChatGPT
                        response_text = consulta_chatgpt(message_text)

                        # Enviar respuesta al usuario
                        service.spaces().messages().create(
                            parent=space_name,
                            body={"text": response_text}
                        ).execute()
                        print(f"[DEBUG] Respuesta enviada: {response_text}")

                        # Guardar en la base de datos como respondido
                        RespondedMessage.objects.create(
                            message_id=message_id,
                            message_user=message_text,
                            status=True
                        )
                    else:
                        print(f"[DEBUG] El mensaje ya fue respondido: {message_id}")

            print("Revisando mensajes nuevamente...")
            time.sleep(10)

        except Exception as e:
            print(f"Error en el worker: {e}")
            time.sleep(10)

