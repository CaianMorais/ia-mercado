from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class AcaoEnum(str, Enum):
    ADICIONAR = "adicionar"
    REMOVER = "remover"
    LISTAR = "listar"
    FINALIZAR = "finalizar"
    MANTER = "manter"

class ItemComando(BaseModel):
    acao: AcaoEnum = Field(description="A ação específica para este(s) item(ns)")
    itens: List[str] = Field(default=[], description="Lista de nomes de produtos")
    valor: Optional[float] = Field(None, description="Valor gasto, se aplicável")

class RespostaIA(BaseModel):
    comandos: List[ItemComando] = Field(description="Lista de ações a serem executadas")
    mensagem_direta: str = Field(None, description="Uma resposta amigável para o utilizador")