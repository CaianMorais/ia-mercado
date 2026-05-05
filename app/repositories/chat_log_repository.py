from app.models.chat_log import ChatLog
from sqlalchemy.orm import Session
from datetime import datetime

class ChatLogRepository:
    @staticmethod
    def add_chat_log(db: Session, user: str, pergunta: str, resposta: str):
        chat_log = ChatLog(
            user=user,
            pergunta=pergunta,
            resposta=resposta,
        )
        db.add(chat_log)
        db.commit()
        db.refresh(chat_log)
        return chat_log