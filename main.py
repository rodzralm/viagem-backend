from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv
from twilio.rest import Client
from openai import OpenAI
from airtable import Airtable

load_dotenv()

app = FastAPI()

# Twilio e OpenAI
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
TWILIO_NUMERO_WHATSAPP = os.getenv("TWILIO_NUMERO_WHATSAPP")

client = Client(TWILIO_SID, TWILIO_TOKEN)
openai_client = OpenAI(api_key=OPENAI_KEY)

# Airtable
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")

tabelas_airtable = {
    "gastos": Airtable(AIRTABLE_BASE_ID, os.getenv("AIRTABLE_TABELA_GASTOS"), AIRTABLE_API_KEY),
    "agenda": Airtable(AIRTABLE_BASE_ID, os.getenv("AIRTABLE_TABELA_AGENDA"), AIRTABLE_API_KEY),
    "opcionais": Airtable(AIRTABLE_BASE_ID, os.getenv("AIRTABLE_TABELA_ATIVIDADES_OPCIONAIS"), AIRTABLE_API_KEY),
    "parques": Airtable(AIRTABLE_BASE_ID, os.getenv("AIRTABLE_TABELA_PARQUES"), AIRTABLE_API_KEY),
    "presentes": Airtable(AIRTABLE_BASE_ID, os.getenv("AIRTABLE_TABELA_PRESENTES"), AIRTABLE_API_KEY),
    "compras": Airtable(AIRTABLE_BASE_ID, os.getenv("AIRTABLE_TABELA_COMPRAS"), AIRTABLE_API_KEY),
    "mala": Airtable(AIRTABLE_BASE_ID, os.getenv("AIRTABLE_TABELA_MALAS"), AIRTABLE_API_KEY),
    "fotos": Airtable(AIRTABLE_BASE_ID, os.getenv("AIRTABLE_TABELA_POSTS"), AIRTABLE_API_KEY)
}

# Carrega o prompt detalhado
with open('prompt_viagem.txt', 'r', encoding='utf-8') as file:
    prompt_viagem = file.read()

@app.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    data = await request.form()
    mensagem_recebida = data.get('Body')
    numero_remetente = data.get('From')

    print(f"Mensagem recebida de {numero_remetente}: {mensagem_recebida}")

    # Ler tabelas Airtable
    contexto_airtable = {}
    try:
        for nome_tabela, cliente_tabela in tabelas_airtable.items():
            records = cliente_tabela.get_all()
            contexto_airtable[nome_tabela] = [record['fields'] for record in records]
    except Exception as e:
        contexto_airtable = f"Erro ao acessar Airtable: {e}"

    # Gerar resposta da OpenAI
    resposta_openai = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": f"{prompt_viagem}\nDados atuais Airtable:\n{contexto_airtable}"},
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
