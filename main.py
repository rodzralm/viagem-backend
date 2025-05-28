from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import openai
import os

app = FastAPI()

# Carregando a API Key do OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    data = await request.form()
    mensagem_recebida = data.get('Body')
    numero_remetente = data.get('From')

    # Teste simples de consulta ao ChatGPT
    resposta_openai = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": mensagem_recebida}]
    )

    resposta = resposta_openai.choices[0].message.content.strip()

    print(f"Mensagem recebida de whatsapp:{numero_remetente}: {mensagem_recebida}")
    print(f"Resposta OpenAI: {resposta}")

    return JSONResponse(
        content={"message": resposta},
        status_code=200
    )
