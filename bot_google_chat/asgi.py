import os
import threading
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bot_google_chat.settings')
application = get_asgi_application()

# Importar y lanzar el worker
from aplications.guests.background_worker import background_worker

print("Iniciando el worker en segundo plano...")
worker_thread = threading.Thread(target=background_worker, daemon=True)
worker_thread.start()

