import openai
import os
from dotenv import load_dotenv

# Cargar las variables de entorno
load_dotenv()

# Configurar la API de OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

def consulta_chatgpt(prompt):
    """
    Envía una consulta a la API de OpenAI ChatGPT y devuelve la respuesta.
    """
    try:
        # Usar la estructura correcta de `chat.completions.create`
        respuesta = openai.chat.completions.create(
            model="gpt-3.5-turbo",  # Modelo correcto
            messages=[
                {"role": "user", "content": prompt}  # Formato requerido
            ]
        )
        # Extraer el contenido de la respuesta
        return respuesta.choices[0].message.content
    except Exception as e:
        print(f"Error al consultar ChatGPT: {e}")
        return "Lo siento, no pude procesar la solicitud."