import uvicorn
from fastapi import FastAPI
from app.routers import message

app = FastAPI()

app.include_router(message.router)

# AO RODAR O PROJETO, É NECESSÁRIO COLOCAR NO CMD "./ngrok http 8000" PARA QUE O TWILIO CONSIGA ENVIAR AS MENSAGENS PARA O BOT
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)