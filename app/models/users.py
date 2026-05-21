from datetime import datetime
from app.core.config import Base
from sqlalchemy import Column, String, DateTime, Boolean, Integer
from sqlalchemy.orm import relationship

class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String(50), nullable=False)
    cpf = Column(String(14), nullable=False)
    email = Column(String(50), nullable=True)
    phonenumber = Column(String(50), nullable=False)
    zip_code = Column(String(50), nullable=False)
    city = Column(String(50), nullable=False)
    state = Column(String(50), nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relacionamentos
    lista_compras = relationship("ListaCompras", back_populates="usuario", cascade="all, delete-orphan")
    historico_compras = relationship("HistoricoCompras", back_populates="usuario", cascade="all, delete-orphan")
    chat_logs = relationship("ChatLog", back_populates="usuario", cascade="all, delete-orphan")
    