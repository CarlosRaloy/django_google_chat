#!/bin/bash
DJANGODIR=$(dirname $(cd `dirname $0` && pwd))
echo ".: Directory by project :."
echo $DJANGODIR
DJANGO_SETTINGS_MODULE=bot_google_chat.settings
cd $DJANGODIR
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
exec uvicorn bot_google_chat.asgi:application --host 0.0.0.0 --port 8000 --workers 5

#exec python manage.py runserver 10.150.8.30:8000
