from sqlalchemy.orm import Session
from app.services.ai_service import AIService
from app.repositories.chat_log_repository import ChatLogRepository

class ChatLogService:
    def __init__(self, db: Session):
        self.db: Session = db
        self.ai_service = AIService()
        self.repository = ChatLogRepository

    def add_chat_log(self, user: str, pergunta: str, resposta: str):
        self.repository.add_chat_log(self.db, user, pergunta, resposta)