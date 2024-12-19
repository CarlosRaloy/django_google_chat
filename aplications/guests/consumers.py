import json
from channels.generic.websocket import AsyncWebsocketConsumer

class MessageConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.send(text_data=json.dumps({"message": "Conexión establecida"}))

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json.get('message', '')
        await self.send(text_data=json.dumps({"message": f"Respuesta: {message}"}))

    async def disconnect(self, close_code):
        pass
