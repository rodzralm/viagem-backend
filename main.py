from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv()

app = FastAPI()

# Busca as variáveis diretamente do ambiente (funciona tanto localmente quanto no Render)
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
AIRTABLE_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")

# Configura cliente do Twilio
client = Client(TWILIO_SID, TWILIO_TOKEN)

@app.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    data = await request.form()
    mensagem_recebida = data.get('Body')
    numero_remetente = data.get('From')

    print(f"Mensagem recebida de {numero_remetente}: {mensagem_recebida}")

    resposta = f"Olá! Recebi sua mensagem: {mensagem_recebida}"

    return JSONResponse(
        content={"message": resposta},
        status_code=200
    )
