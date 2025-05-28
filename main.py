from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv
from twilio.rest import Client
from openai import OpenAI

load_dotenv()

app = FastAPI()

TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
TWILIO_NUMERO_WHATSAPP = os.getenv("TWILIO_NUMERO_WHATSAPP")

client = Client(TWILIO_SID, TWILIO_TOKEN)
openai_client = OpenAI(api_key=OPENAI_KEY)

@app.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    data = await request.form()
    mensagem_recebida = data.get('Body')
    numero_remetente = data.get('From')

    print(f"Mensagem recebida de {numero_remetente}: {mensagem_recebida}")

    resposta_openai = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Você é um assistente simpático respondendo mensagens via WhatsApp."},
            {"role": "user", "content": mensagem_recebida}
        ]
    )

    resposta = resposta_openai.choices[0].message.content.strip()

    # Enviar resposta via Twilio WhatsApp
    client.messages.create(
        from_='whatsapp:' + TWILIO_NUMERO_WHATSAPP,
        to=numero_remetente,
        body=resposta
    )

    return JSONResponse(content={"message": resposta}, status_code=200)


