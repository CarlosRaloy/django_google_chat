from django.shortcuts import render, redirect, get_object_or_404
from .models import ModelGoogleGuest
import googleapiclient.discovery
from google.oauth2.service_account import Credentials
import os

def feed_view(request):
    guests = ModelGoogleGuest.objects.all()
    return render(request, 'feed.html', {'users': guests})

def add_user(request):
    if request.method == "POST":
        name = request.POST.get("name")
        space = request.POST.get("space")
        if name and space:
            ModelGoogleGuest.objects.create(name=name, space=space)
        return redirect('guests:feed')

def edit_user(request, user_id):
    if request.method == "POST":
        user = get_object_or_404(ModelGoogleGuest, id=user_id)
        user.name = request.POST.get("name")
        user.space = request.POST.get("space")
        if user.name and user.space:
            user.save()
        return redirect('guests:feed')

def delete_user(request, user_id):
    if request.method == "POST":
        user = get_object_or_404(ModelGoogleGuest, id=user_id)
        user.delete()
        return redirect('guests:feed')

def send_message(request):
    if request.method == "POST":
        message = request.POST.get("message")
        if not message:
            return redirect('guests:feed')

        users = ModelGoogleGuest.objects.all()  # Obtener todos los usuarios registrados

        # Ruta al archivo JSON de la cuenta de servicio
        SERVICE_ACCOUNT_FILE = os.path.join('credentials', 'genuine-synapse-443816-d6-4be5dc4cf0a4.json')

        # Configuración de las credenciales de la cuenta de servicio
        credentials = Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=["https://www.googleapis.com/auth/chat.bot"]
        )

        # Configuración del servicio de Google Chat
        service = googleapiclient.discovery.build('chat', 'v1', credentials=credentials)

        # Enviar mensaje a cada usuario
        for user in users:
            space_id = user.space
            try:
                service.spaces().messages().create(
                    parent=f'spaces/{space_id}',
                    body={"text": message}
                ).execute()
            except Exception as e:
                print(f"Error al enviar mensaje a {user.name}: {e}")

        return redirect('guests:feed')

    return redirect('guests:feed')
