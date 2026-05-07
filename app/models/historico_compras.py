from app.core.config import Base
from sqlalchemy import Column, String, DateTime, Float, Integer, JSON

class HistoricoCompras(Base):
    __tablename__ = 'historico_compras'

    id = Column(Integer, primary_key=True, index=True)
    user = Column(String(50))
    data_compra = Column(DateTime, index=True)
    gasto_valor = Column(Float)
    supermercado = Column(String(100), index=True, nullable=True)
    lista_itens_comprados = Column(JSON, nullable=True)