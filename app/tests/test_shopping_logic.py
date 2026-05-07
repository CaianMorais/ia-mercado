import pytest
from _pytest.monkeypatch import MonkeyPatch
from app.schemas.bot_schema import RespostaIA, ItemComando, AcaoEnum
from app.core.config import SessionLocal
from app.services.shopping_service import ShoppingService

@pytest.fixture
def service():
    db = SessionLocal()
    service = ShoppingService(db)
    yield service
    db.close()

def test_adicionar_itens(service, monkeypatch: MonkeyPatch):
    comando = RespostaIA(
        comandos=[
            ItemComando(
                acao=AcaoEnum.ADICIONAR, 
                itens=["Arroz", "Feijão"]
            )
        ]
    )

    monkeypatch.setattr(service.ai_service, "process_message", lambda msg, hist: comando)
    resultado, *_ = service.execute_command("mensagem de teste", "UserTeste") 
    assert "produto Arroz adicionado na lista de compras" in resultado
    assert "produto Feijão adicionado na lista de compras" in resultado

def test_remover_todos_itens(service, monkeypatch: MonkeyPatch):
    service.repository.add_item_to_list(service.db, "UserTeste", "Café")

    comando = RespostaIA(
        comandos=[
            ItemComando(
                acao=AcaoEnum.REMOVER,
                itens=["todos os itens"]
            )
        ]
    )
    
    monkeypatch.setattr(service.ai_service, "process_message", lambda msg, hist: comando)
    resultado, *_ = service.execute_command("mensagem de teste", "UserTeste")
    assert "todos os itens foram removidos da lista de compras" in resultado
    
    lista = service.repository.get_all_items_from_list(service.db)
    assert len(lista) == 0

def test_finalizar_compra(service, monkeypatch: MonkeyPatch):
    service.repository.add_item_to_list(service.db, "UserTeste", "Café")
    service.repository.add_item_to_list(service.db, "UserTeste", "Leite")
    
    comando = RespostaIA(
        comandos=[ItemComando(
            acao=AcaoEnum.FINALIZAR, 
            itens=[], 
            valor=50.0, 
            supermercado="Assai"
        )]
    )

    monkeypatch.setattr(service.ai_service, "process_message", lambda msg, hist: comando)
    resultado, *_ = service.execute_command("mensagem de teste", "UserTeste")
    assert "compra finalizada, valor total: R$ 50.00 no supermercado Assai" in resultado
    
    lista = service.repository.get_all_items_from_list(service.db)
    assert len(lista) == 0

    