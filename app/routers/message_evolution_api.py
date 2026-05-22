from fastapi import requests
from fastapi import requests
from app.core.cache import get_state_by_ddd
from fastapi import Request
from fastapi import APIRouter, Depends, Form
from app.core.config import get_db, twilio_config
from sqlalchemy.orm import Session
from twilio.rest import Client
from app.services.shopping_service import ShoppingService
from app.services.chat_log_service import ChatLogService
import os
import httpx

router = APIRouter()

# Configurações obtidas das Variáveis de Ambiente
EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY")
INSTANCE_NAME = os.getenv("EVOLUTION_INSTANCE_NAME")

@router.post("/evolution/webhook/messages-upsert")
async def receive_message(
    request: Request,
):

    try:
        payload = await request.json()
        event = payload.get("event")
        
        if event == "messages.upsert":
            print("--- NOVO WEBHOOK DA EVOLUTION API ---")
            print("Payload Completo:", payload)        
            print(f"Tipo do Evento: {event}")
                
            data = payload.get("data", {})
            key = data.get("key", {})
            
            if key.get("fromMe") is True:
                print("Mensagem enviada por mim mesmo. Ignorando...")
                return {"status": "ignored", "reason": "Message from me"}
            
            # extração do numero que enviou a mensagem
            remote_jid = key.get("remoteJid", "")
            wa_id = remote_jid.split("@")[0] if "@" in remote_jid else remote_jid
            
            # extração do nome do perfil do usuário no WhatsApp
            profile_name = data.get("pushName", "Usuário")
            
            # extração do texto da mensagem (tratando mensagens simples ou respostas com citação)
            message_info = data.get("message", {})
            body = (
                message_info.get("conversation") or 
                message_info.get("extendedTextMessage", {}).get("text", "")
            )
            
            print(f"Remetente (WaId): {wa_id}")
            print(f"Nome (ProfileName): {profile_name}")
            print(f"Texto da Mensagem (Body): {body}")          

        return {"status": "success"}

    except Exception as e:
        print(f"Erro ao processar o webhook: {str(e)}")
        return {"status": "error", "message": str(e)}
    
async def message_with_evolution(
    wa_id:str,
    message:str,
):
    """
    Rota auxiliar interna para efetuar o envio de mensagens de volta 
    para o usuário utilizando a Evolution API.
    """
    url = f"{EVOLUTION_API_URL}/message/sendText/{INSTANCE_NAME}"
    headers = {
        "apikey": EVOLUTION_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "number": wa_id,
        "delay": 4000,
        "text": message
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Erro ao enviar mensagem via Evolution API: {str(e)}")
            return None

@router.post("/evolution/messages-upsert")
async def handle_whatsapp(
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        # extrai o JSON
        payload = await request.json()
        
        # garante que o evento é de mensagem recebida
        event = payload.get("event")
        if event != "messages.upsert":
            return {"status": "ignored", "reason": f"Event '{event}' ignored"}

        data = payload.get("data", {})
        key = data.get("key", {})
        
        # evita loop infinito ignorando mensagens enviadas pelo próprio bot
        if key.get("fromMe") is True:
            return {"status": "ignored", "reason": "Message sent by the bot itself"}

        # extrai o numero que enviou a mensagem
        remote_jid = key.get("remoteJid", "")
        wa_id = remote_jid.split("@")[0] if "@" in remote_jid else remote_jid

        # extrai o nome do perfil do WhatsApp
        profile_name = data.get("pushName", "Usuário")

        # extrai o texto da mensagem
        message_info = data.get("message", {})
        body = (
            message_info.get("conversation") or 
            message_info.get("extendedTextMessage", {}).get("text", "")
        )

        # se o corpo da mensagem vier vazio, ignora
        if not body:
            return {"status": "ignored", "reason": "No text body found"}

        # busca localidade pelo DDD
        ddd = wa_id[2:4]
        estado = get_state_by_ddd(ddd)

        # executa as regras de negócio
        service = ShoppingService(db)
        resultado, lista_de_itens, mensagem_direta = service.execute_command(user_message=body, user_name=profile_name, state=estado)

        chat_log_service = ChatLogService(db)

        if not resultado and not lista_de_itens and mensagem_direta:
            await message_with_evolution(wa_id, mensagem_direta)
            chat_log_service.add_chat_log(profile_name, body, mensagem_direta)

        if resultado:
            resumo = service.ai_service.resume(resultado)
            if not resumo: 
                resposta = f"{profile_name}, não consegui processar sua mensagem, mas a operação foi concluída" 
                await message_with_evolution(wa_id, resposta)
                chat_log_service.add_chat_log(profile_name, body, resposta)
            else:
                await message_with_evolution(wa_id, str(resumo.resumo))
                chat_log_service.add_chat_log(profile_name, body, resumo.resumo)

        if lista_de_itens: # Tratamento seguro para listas
            if len(lista_de_itens) == 0: #
                resposta = f"{profile_name}, sua lista de compras está vazia."
                await message_with_evolution(wa_id, resposta)
                chat_log_service.add_chat_log(profile_name, body, resposta)
            else:
                lista_formatada = "\n".join(lista_de_itens)
                await message_with_evolution(wa_id, lista_formatada)
                chat_log_service.add_chat_log(profile_name, body, lista_formatada)
                        
        return {"status": "success", "message": "Mensagem processada e respondida"}

    except Exception as e:
        print(f"Erro interno no processamento do webhook: {str(e)}")
        return {"status": "error", "message": str(e)}
