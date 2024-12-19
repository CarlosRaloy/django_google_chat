import os
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from datetime import datetime
from .models import ModelGoogleGuest, RespondedMessage
import googleapiclient.discovery
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from .utils import consulta_chatgpt
from dotenv import load_dotenv
load_dotenv()

# Ruta del archivo JSON de credenciales OAuth
CLIENT_SECRETS_FILE = os.path.join('credentials', 'client_secret_429186771757-rk0ptndo07neej85p0a171bssb66p8n0.apps.googleusercontent.com.json')
CREDENTIALS_FILE = os.path.join('credentials', 'user_credentials.json')
BOT_USER_ID = "users/112568225339349392647"

# Definir los permisos necesarios
SCOPES = [
    'https://www.googleapis.com/auth/chat.spaces',
    'https://www.googleapis.com/auth/chat.messages',
    'https://www.googleapis.com/auth/chat.messages.readonly',
]

# Permitir transporte inseguro (desarrollo local)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


def feed_view(request):
    guests = ModelGoogleGuest.objects.all()
    is_authorized = os.path.exists(CREDENTIALS_FILE)
    success_message = request.session.pop('success_message', None)
    error_message = request.session.pop('error_message', None)
    return render(request, 'feed.html', {
        'users': guests,
        'is_authorized': is_authorized,
        'success_message': success_message,
        'error_message': error_message
    })



# Agregar usuario
def add_user(request):
    if request.method == "POST":
        name = request.POST.get("name")
        space = request.POST.get("space")
        if name and space:
            ModelGoogleGuest.objects.create(name=name, space=space)
        return redirect('guests:feed')


# Editar usuario
def edit_user(request, user_id):
    if request.method == "POST":
        user = get_object_or_404(ModelGoogleGuest, id=user_id)
        user.name = request.POST.get("name")
        user.space = request.POST.get("space")
        if user.name and user.space:
            user.save()
        return redirect('guests:feed')


# Eliminar usuario
def delete_user(request, user_id):
    if request.method == "POST":
        user = get_object_or_404(ModelGoogleGuest, id=user_id)
        user.delete()
        return redirect('guests:feed')


# Inicio del flujo OAuth
def start_oauth(request):
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=request.build_absolute_uri(reverse('guests:oauth_callback'))
    )
    authorization_url, state = flow.authorization_url(
        access_type='offline',  # Asegura la solicitud de un refresh_token
        include_granted_scopes='true',
        prompt='consent'  # Obliga a que el usuario vea la pantalla de consentimiento nuevamente
    )
    request.session['state'] = state
    return redirect(authorization_url)


def oauth_callback(request):
    state = request.session.get('state')
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        state=state,
        redirect_uri=request.build_absolute_uri(reverse('guests:oauth_callback'))
    )
    flow.fetch_token(authorization_response=request.build_absolute_uri())
    credentials = flow.credentials

    # Imprimir credenciales para debug
    print(f"Credenciales obtenidas: {credentials.to_json()}")

    # Guardar las credenciales en el archivo user_credentials.json
    with open(CREDENTIALS_FILE, 'w') as cred_file:
        json.dump({
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes,
        }, cred_file)

    return redirect('guests:feed')


def send_message(request):
    if request.method == "POST":
        message = request.POST.get("message")
        users = ModelGoogleGuest.objects.all()

        if not message:
            return redirect('guests:feed')

        # Intentar cargar credenciales desde user_credentials.json
        credentials = None
        if os.path.exists(CREDENTIALS_FILE):
            with open(CREDENTIALS_FILE, 'r') as cred_file:
                credentials_data = json.load(cred_file)
                print("Cargando credenciales:", credentials_data)  # Debug
                try:
                    credentials = Credentials.from_authorized_user_info(info=credentials_data)
                    print("Credenciales cargadas exitosamente")
                except Exception as e:
                    print(f"Error al cargar credenciales: {e}")

        # Verificar si las credenciales son válidas
        if not credentials or not credentials.valid:
            print("Credenciales inválidas o expiradas")
            if not credentials.refresh_token:
                print("Falta el refresh_token. Necesitas reautorizar.")
                return redirect('guests:start_oauth')

        # Configura el servicio de Google Chat
        try:
            service = googleapiclient.discovery.build('chat', 'v1', credentials=credentials)
            print("Servicio de Google Chat configurado exitosamente")
        except Exception as e:
            print(f"Error al configurar el servicio: {e}")
            return redirect('guests:feed')

        # Envía un mensaje a cada usuario registrado
        for user in users:
            space_id = user.space
            try:
                service.spaces().messages().create(
                    parent=f'spaces/{space_id}',
                    body={"text": message}
                ).execute()
                print(f"Mensaje enviado al espacio {space_id}.")
            except Exception as e:
                print(f"Error al enviar mensaje a {user.name} en el espacio {space_id}: {e}")

        return redirect('guests:feed')

    return redirect('guests:feed')




def load_credentials():
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, 'r') as file:
            creds_data = json.load(file)
        try:
            credentials = Credentials.from_authorized_user_info(creds_data, SCOPES)

            # Si las credenciales están expiradas, refrescarlas
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                print("Token refrescado exitosamente")

                # Guardar las credenciales actualizadas
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

def list_messages(request):
    """
    Obtiene los últimos mensajes de Google Chat por espacio y los muestra en el template.
    Excluye los mensajes enviados por el bot (BOT_USER_ID).
    """
    credentials = load_credentials()

    if not credentials:
        return redirect('guests:start_oauth')

    try:
        # Inicializar el servicio de Google Chat
        service = build('chat', 'v1', credentials=credentials)
        guests = ModelGoogleGuest.objects.all()  # Todos los espacios registrados

        # Lista para almacenar los últimos mensajes por espacio
        last_messages = []

        for guest in guests:
            space_name = f"spaces/{guest.space.strip()}"
            all_messages = []
            page_token = None

            # Obtener todos los mensajes del espacio usando paginación
            while True:
                response = service.spaces().messages().list(
                    parent=space_name,
                    pageSize=1000,  # Máximo permitido
                    pageToken=page_token
                ).execute()

                messages = response.get('messages', [])
                all_messages.extend(messages)

                page_token = response.get('nextPageToken')
                if not page_token:
                    break

            # Filtrar el mensaje más reciente que no sea del bot
            if all_messages:
                messages_sorted = sorted(all_messages, key=lambda x: x['createTime'], reverse=True)

                # Buscar el mensaje más reciente que NO sea del bot
                for message in messages_sorted:
                    sender_id = message['sender']['name']
                    message_text = message.get('text', '')
                    created_time = message['createTime']

                    if sender_id != BOT_USER_ID and message_text:
                        last_messages.append({
                            'space': space_name,
                            'sender': sender_id,
                            'text': message_text,
                            'time': created_time
                        })
                        break  # Solo añadimos el mensaje más reciente

        # Renderizar los últimos mensajes en el template
        return render(request, 'list_messages.html', {'messages_list': last_messages})

    except Exception as e:
        print(f"Error al listar mensajes: {e}")
        return redirect('guests:feed')




