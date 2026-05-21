from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class AcaoEnum(str, Enum):
    ADICIONAR = "adicionar"
    REMOVER = "remover"
    LISTAR = "listar"
    MANTER = "manter"
    FINALIZAR = "finalizar"
    PESQUISAR_PRECOS = "pesquisar_precos"
    ANALISAR = "analisar"

class ItemComando(BaseModel):
    acao: AcaoEnum = Field(description="A ação específica para este(s) item(ns)")
    itens: List[str] = Field(default=[], description="Lista de nomes de produtos")
    valor: Optional[float] = Field(None, description="Valor gasto, se aplicável")
    supermercado: Optional[str] = Field(None, description="Supermercado, se aplicável")
    periodo: Optional[str] = Field(None, description="30 dias ou mes atual, para análise")

class RespostaIA(BaseModel):
    comandos: List[ItemComando] = Field(description="Lista de ações a serem executadas")
    mensagem_direta: str = Field(None, description="Uma resposta amigável para o utilizador")

class ResumoIA(BaseModel):
    resumo: str = Field(description="Resumo dos resultados")

class PesquisaPrecos(BaseModel):
    itens_pesquisados: List[str] = Field(description="Lista de itens pesquisados")
    soma_total: float = Field(description="Preço total dos itens")
    nome_supermercado: str = Field(description="Nome do supermercado")