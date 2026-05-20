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

@router.post("/evolution/webhook/groups-upsert")
async def receive_message(
    request: Request,
):

    try:
        # 1. A Evolution API envia dados em formato JSON, não Form
        payload = await request.json()
        event = payload.get("event")
        print("Payload Completo:", payload)
        
        # if event == "groups.upsert":
        #     # Print completo para você inspecionar a estrutura inteira no terminal local
        #     print("--- NOVO WEBHOOK DA EVOLUTION API ---")
        #     print("Payload Completo:", payload)
        
        #     # 2. Captura o tipo de evento enviado
        
        #     print(f"Tipo do Evento: {event}")
        
        #     # Queremos processar apenas quando uma nova mensagem é inserida/recebida
        
        #     data = payload.get("data", {})
        #     key = data.get("key", {})
            
        #     # Evita que o robô responda às próprias mensagens que ele enviar
        #     if key.get("fromMe") is True:
        #         print("Mensagem enviada por mim mesmo. Ignorando...")
        #         return {"status": "ignored", "reason": "Message from me"}
            
        #     # Extrai o número do WhatsApp do remetente (ex: 5511999999999)
        #     remote_jid = key.get("remoteJid", "")
        #     wa_id = remote_jid.split("@")[0] if "@" in remote_jid else remote_jid
            
        #     # Extrai o nome do perfil do usuário no WhatsApp
        #     profile_name = data.get("pushName", "Usuário")
            
        #     # Extrai o texto da mensagem (tratando mensagens simples ou respostas com citação)
        #     message_info = data.get("message", {})
        #     body = (
        #         message_info.get("conversation") or 
        #         message_info.get("extendedTextMessage", {}).get("text", "")
        #     )
            
        #     print(f"Remetente (WaId): {wa_id}")
        #     print(f"Nome (ProfileName): {profile_name}")
        #     # Equivalente ao "Body" que vinha do Twilio
        #     print(f"Texto da Mensagem (Body): {body}") 
            
        #     # Aqui depois você chamará a sua lógica do ShoppingService...
            
        # return {"status": "success"}

    except Exception as e:
        print(f"Erro ao processar o webhook: {str(e)}")
        return {"status": "error", "message": str(e)}
    