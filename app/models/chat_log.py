from app.core.config import Base
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

class ChatLog(Base):
    __tablename__ = 'chat_log'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    user_name = Column(String(50))
    pergunta = Column(String(500))
    resposta = Column(String(2000))

    # Relacionamento
    usuario = relationship("Users", back_populates="chat_logs")
