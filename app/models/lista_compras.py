from app.core.config import Base
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship

class ListaCompras(Base):
    __tablename__ = 'lista_compras'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    user_name = Column(String(50))
    nome_item = Column(String(100), index=True)
    quantidade = Column(Integer)
    data_criacao = Column(DateTime, index=True)

    # Relacionamento
    usuario = relationship("Users", back_populates="lista_compras")