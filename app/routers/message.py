from fastapi import Request
from fastapi import APIRouter, Depends, Form
from app.core.config import get_db, twilio_config
from sqlalchemy.orm import Session
from twilio.rest import Client
from app.services.shopping_service import ShoppingService
from app.services.chat_log_service import ChatLogService


router = APIRouter()

@router.post("/webhook")
async def receive_message(
    request: Request,
    Body: str=Form(),
    ProfileName: str=Form()
):
    print("Body", Body)
    print("ProfileName", ProfileName)
    

@router.post("/whatsapp_message")
def handle_whatsapp(
    Body: str=Form(),
    ProfileName: str=Form(),
    WaId: str=Form(),
    db: Session = Depends(get_db)
):
    account_sid, auth_token, tel_number = twilio_config()
    client = Client(account_sid, auth_token)

    service = ShoppingService(db)
    resultado, lista_de_itens = service.execute_command(user_message=Body, user_name=ProfileName)

    chat_log_service = ChatLogService(db)

    if resultado:
        # IA resume o resultado da operação
        resumo = service.ai_service.resume(resultado)
        if not resumo:
            resposta = f"{ProfileName}, não consegui processar sua mensagem, mas a operação foi concluída"
            client.messages.create(
                from_='whatsapp:+'+tel_number,
                body=resposta,
                to='whatsapp:+'+WaId
            )
            chat_log_service.add_chat_log(ProfileName, Body, resposta)

        client.messages.create(
            from_='whatsapp:+'+tel_number,
            body=str(resumo.resumo),
            to='whatsapp:+'+WaId
        )

        chat_log_service.add_chat_log(ProfileName, Body, resumo.resumo)

    if lista_de_itens:
        if len(lista_de_itens) == 0:
            resposta = f"{ProfileName}, sua lista de compras está vazia."
            client.messages.create(
                from_='whatsapp:+'+tel_number,
                body=resposta,
                to='whatsapp:+'+WaId
            )
            chat_log_service.add_chat_log(ProfileName, Body, resposta)
        else:
            lista_formatada = "\n".join(lista_de_itens)
            client.messages.create(
                from_='whatsapp:+'+tel_number,
                body=lista_formatada,
                to='whatsapp:+'+WaId
            )
            chat_log_service.add_chat_log(ProfileName, Body, lista_formatada)
                    
    
    return {"status": "success", "message": "Mensagem enviada"}
