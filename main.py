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

# Função centralizada para enviar WhatsApp

def enviar_whatsapp(numero_destino, mensagem):
    mensagem_limitada = mensagem[:1500]
    client.messages.create(
        from_='whatsapp:' + TWILIO_NUMERO_WHATSAPP,
        to=numero_destino,
        body=mensagem_limitada
    )

# Memória temporária para contexto
ultima_solicitacao = {}

@app.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    data = await request.form()
    mensagem_recebida = data.get('Body')
    numero_remetente = data.get('From')

    print(f"Mensagem recebida de {numero_remetente}: {mensagem_recebida}")

    # Ler tabelas Airtable com tratamento de erro
    contexto_airtable = {}
    erro_airtable = False

    try:
        for nome_tabela, cliente_tabela in tabelas_airtable.items():
            records = cliente_tabela.get_all()
            contexto_airtable[nome_tabela] = [record['fields'] for record in records]
    except Exception as e:
        erro_airtable = True
        contexto_airtable = f"Erro ao acessar Airtable: {e}"

    if erro_airtable:
        resposta = f"GOSTOSO, tivemos um erro ao acessar o Airtable: {contexto_airtable}. Por favor verifique isso antes de continuar!"
        enviar_whatsapp(numero_remetente, resposta)
        return JSONResponse(content={"message": resposta}, status_code=500)

    if mensagem_recebida.strip().lower() in ["ok", "sim"]:
        if numero_remetente in ultima_solicitacao:
            solicitacao = ultima_solicitacao[numero_remetente]
            try:
                tabelas_airtable[solicitacao["tabela"]].insert(solicitacao["dados"])
                resposta_final = "Prontinho, gostoso! Atualizei as informações no Airtable como combinado."
            except Exception as e:
                resposta_final = f"Erro ao atualizar no Airtable: {e}"

            del ultima_solicitacao[numero_remetente]
        else:
            resposta_final = "Gostoso, não encontrei nenhuma atualização pendente. Me manda novamente?"

        enviar_whatsapp(numero_remetente, resposta_final)
        return JSONResponse(content={"message": resposta_final}, status_code=200)

    classificacao_openai = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": f"{prompt_viagem}\nClassifique claramente esta mensagem como 'consulta', 'atualizacao' ou 'outro':"},
            {"role": "user", "content": mensagem_recebida}
        ]
    )

    tipo_mensagem = classificacao_openai.choices[0].message.content.strip().lower()

    if tipo_mensagem == "atualizacao":
        validacao = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"{prompt_viagem}\nIdentifique claramente a tabela, os campos, valores completos, e valide tudo com Rodz antes de salvar."},
                {"role": "user", "content": mensagem_recebida}
            ]
        )
        resposta_validacao = validacao.choices[0].message.content.strip()

        # Salva contexto da solicitação pendente
        ultima_solicitacao[numero_remetente] = {
            "tabela": "presentes",  # aqui você deve implementar lógica dinâmica
            "dados": {"Observações": mensagem_recebida}  # idem acima
        }

        enviar_whatsapp(numero_remetente, resposta_validacao)

    else:
        resposta_openai = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"{prompt_viagem}\nDados atuais Airtable:\n{contexto_airtable}"},
                {"role": "user", "content": mensagem_recebida}
            ]
        )
        resposta = resposta_openai.choices[0].message.content.strip()
        enviar_whatsapp(numero_remetente, resposta)

    return JSONResponse(content={"message": "Processado com sucesso"}, status_code=200)
