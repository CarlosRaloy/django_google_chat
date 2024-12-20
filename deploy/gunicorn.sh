#!/bin/bash

NAME="bot_google_chat"
DJANGODIR=$(dirname $(cd `dirname $0` && pwd))
LOGDIR=${DJANGODIR}/logs/gunicorn.log
USER=raloy
GROUP=raloy
NUM_WORKERS=5
DJANGO_WSGI_MODULE=bot_google_chat.wsgi
SERVER_IP=0.0.0.0
PORT=8000

echo $DJANGODIR

cd $DJANGODIR

exec ${DJANGODIR}/venv/bin/gunicorn ${DJANGO_WSGI_MODULE}:application \
  --name $NAME \
  --workers $NUM_WORKERS \
  --user=$USER --group=$GROUP \
  --bind=$SERVER_IP:$PORT \
  --log-level=debug \
  --log-file=$LOGDIR