import os
from fastapi import FastAPI, Request, Form
from twilio.rest import Client
import openai
from airtable import Airtable
from dotenv import load_dotenv

load_dotenv()

# Carregando credenciais diretamente do Render
openai.api_key = os.getenv('OPENAI_API_KEY')

TWILIO_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
twilio_whatsapp_number = os.getenv('TWILIO_WHATSAPP_NUMBER')

client = Client(TWILIO_SID, TWILIO_TOKEN)

# Carregando as bases do Airtable
airtable_atividades_opcionais = Airtable(
    os.getenv('AIRTABLE_BASE_ID'),
    os.getenv('AIRTABLE_ATIVIDADES_OPCIONAIS_TABLE'),
    os.getenv('AIRTABLE_API_KEY')
)

# Iniciando FastAPI
app = FastAPI()

@app.get("/")
async def root():
    return {"Rodz Viagem AI": "API funcionando perfeitamente!"}

@app.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    form = await request.form()
    mensagem_usuario = form.get('Body')
    numero_usuario = form.get('From')

    # Aqui vamos testar a comunicação respondendo via OpenAI
    resposta_openai = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Você é um assistente virtual para ajudar em uma viagem."},
            {"role": "user", "content": mensagem_usuario}
        ]
    )

    resposta_texto = resposta_openai.choices[0].message.content

    # Respondendo via Twilio WhatsApp
    message = client.messages.create(
        from_=f'whatsapp:{twilio_whatsapp_number}',
        body=resposta_texto,
        to=numero_usuario
    )

    return {"status": "Mensagem enviada com sucesso", "sid": message.sid}
