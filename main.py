from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

@app.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    data = await request.form()
    mensagem_recebida = data.get('Body')
    numero_remetente = data.get('From')

    # Aqui você pode tratar a mensagem recebida conforme sua necessidade
    print(f"Mensagem recebida de {numero_remetente}: {mensagem_recebida}")

    resposta = f"Olá! Recebi sua mensagem: {mensagem_recebida}"

    return JSONResponse(
        content={"message": resposta},
        status_code=200
    )
