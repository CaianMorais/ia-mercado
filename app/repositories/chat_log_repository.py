from app.models.chat_log import ChatLog
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.users import Users

class ChatLogRepository:
    @staticmethod
    def add_chat_log(db: Session, user: str, pergunta: str, resposta: str):
        db_user = db.query(Users).filter(Users.user_name == user).first()
        if not db_user:
            raise ValueError(f"Usuário '{user}' não encontrado no banco de dados.")
            
        chat_log = ChatLog(
            usuario=db_user,
            user_name=db_user.user_name,
            pergunta=pergunta,
            resposta=resposta,
        )
        db.add(chat_log)
        db.commit()
        db.refresh(chat_log)
        return chat_log

    @staticmethod
    def get_last_user_messages(db: Session, user: str, limit: int = 3):
        return db.query(ChatLog)\
            .filter(ChatLog.user_name == user)\
            .order_by(ChatLog.id.desc())\
            .limit(limit)\
            .all()
        