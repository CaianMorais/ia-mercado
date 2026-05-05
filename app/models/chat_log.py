from app.core.config import Base
from sqlalchemy import Column, String, DateTime, Float, Integer

class ChatLog(Base):
    __tablename__ = 'chat_log'

    id = Column(Integer, primary_key=True, index=True)
    user = Column(String(50))
    pergunta = Column(String(500))
    resposta = Column(String(500))
