from app.core.cache import get_state_by_ddd
from fastapi import Request
from fastapi import APIRouter, Depends, Form
from app.core.config import get_db, twilio_config
from sqlalchemy.orm import Session
from twilio.rest import Client
from app.services.shopping_service import ShoppingService
from app.services.chat_log_service import ChatLogService
from app.services.user_service import UserService

router = APIRouter()

@router.post("/twilio/webhook")
async def receive_message(
    request: Request,
    Body: str=Form(),
    ProfileName: str=Form(),
):
    print("Body", Body)
    print("ProfileName", ProfileName)
    print("Form Data:", await request.form())
    

@router.post("/twilio/message")
def handle_whatsapp(
    Body: str=Form(),
    ProfileName: str=Form(),
    WaId: str=Form(),
    db: Session = Depends(get_db)
):
    account_sid, auth_token, tel_number = twilio_config()
    client = Client(account_sid, auth_token)

    # Verifica se o usuário está registrado e ativo
    user_service = UserService(db)
    print(WaId)
    user = user_service.get_active_user_by_phonenumber(WaId)
    print(user)
    
    if not user:
        resposta = f"Olá {ProfileName}! Seu número (+{WaId}) não está cadastrado ou está inativo no sistema. Entre em contato com o suporte."
        client.messages.create(
            from_='whatsapp:+'+tel_number,
            body=resposta,
            to='whatsapp:+'+WaId
        )
        return {"status": "error", "message": "Usuário não registrado ou inativo"}

    # busca localidade pelo DDD
    ddd = WaId[2:4]
    estado = get_state_by_ddd(ddd)

    service = ShoppingService(db)
    resultado, lista_de_itens, mensagem_direta = service.execute_command(user_message=Body, user_name=ProfileName, state=estado)

    chat_log_service = ChatLogService(db)

    if not resultado and not lista_de_itens and mensagem_direta:
        client.messages.create(
            from_='whatsapp:+'+tel_number,
            body=mensagem_direta,
            to='whatsapp:+'+WaId
        )
        chat_log_service.add_chat_log(ProfileName, Body, mensagem_direta)

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
