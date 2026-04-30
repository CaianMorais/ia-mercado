from fastapi import Request
from fastapi import APIRouter, Depends, Form
from app.core.config import get_db, twilio_config
from sqlalchemy.orm import Session
from app.services.shopping_service import ShoppingService
from twilio.rest import Client


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
    service = ShoppingService(db)
    resultado, itens_comprados, itens_mantidos, lista_de_itens = service.execute_command(user_message=Body, user_name=ProfileName)

    account_sid, auth_token = twilio_config()
    client = Client(account_sid, auth_token)
    
    if resultado:
        resumo = service.ai_service.resume(resultado)
        print(resumo.resumo)

        client.messages.create(
            from_='whatsapp:+14155238886',
            body=str(resumo.resumo),
            to='whatsapp:+'+WaId
        )

    if lista_de_itens:
        lista_formatada = "\n".join(lista_de_itens)
        client.messages.create(
            from_='whatsapp:+14155238886',
            body=lista_formatada,
            to='whatsapp:+'+WaId
        )
    else:
        client.messages.create(
            from_='whatsapp:+14155238886',
            body=f"{ProfileName}, sua lista de compras está vazia.",
            to='whatsapp:+'+WaId
        )
    
    return {"status": "success", "message": "Mensagem enviada"}
