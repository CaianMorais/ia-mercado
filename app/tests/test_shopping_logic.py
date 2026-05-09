from sqlalchemy import create_engine
from app.services import chat_log_service
from app.services.chat_log_service import ChatLogService
import pytest
from _pytest.monkeypatch import MonkeyPatch
from app.schemas.bot_schema import RespostaIA, ItemComando, AcaoEnum
from app.core.config import SessionLocal, SQLALCHEMY_DATABASE_URL
from app.services.shopping_service import ShoppingService
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# cria uma instancia do banco de dados exclusiva para testes
# para garantir que os testes sejam isolados e não afetem o banco de dados de produção
# e garante que cada teste tenha sua própria sessão de banco de dados
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    
    session = TestingSessionLocal(bind=connection)

    nested = connection.begin_nested()
    
    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def service(db_session):
    service = ShoppingService(db_session)
    chat_log_service = ChatLogService(db_session)
    yield service, chat_log_service


# explicando decisão do monkeypatch nos testes:
# usando mockagem para "sequestrar" a service para que ela não seja dependente da IA para teste
# assim nao consome tokens da IA para testar o back-end da aplicação
# sendo assim, é possível desenvolver o back-end e testa-lo antes de fazer a IA executar a mesma funcionalidade.

def test_adicionar_itens(service, monkeypatch: MonkeyPatch):
    shopping_service, chat_log_service = service

    comando = RespostaIA(
        comandos=[
            ItemComando(
                acao=AcaoEnum.ADICIONAR, 
                itens=["Arroz", "Feijão"]
            )
        ]
    )

    monkeypatch.setattr(shopping_service.ai_service, "process_message", lambda msg, hist: comando)

    resultado, *_ = shopping_service.execute_command("mensagem de teste", "UserTeste")
    chat_log_service.add_chat_log("UserTeste", "mensagem de teste", "resposta de teste")
    assert "produto Arroz adicionado na lista de compras" in resultado
    assert "produto Feijão adicionado na lista de compras" in resultado

def test_remover_todos_itens(service, monkeypatch: MonkeyPatch):
    shopping_service, chat_log_service = service

    shopping_service.repository.add_item_to_list(shopping_service.db, "UserTeste", "Café")
    shopping_service.repository.add_item_to_list(shopping_service.db, "UserTeste", "Leite")

    comando = RespostaIA(
        comandos=[
            ItemComando(
                acao=AcaoEnum.REMOVER,
                itens=["todos os itens"]
            )
        ]
    )
    
    monkeypatch.setattr(shopping_service.ai_service, "process_message", lambda msg, hist: comando)
    resultado, *_ = shopping_service.execute_command("mensagem de teste", "UserTeste")
    assert "todos os itens foram removidos da lista de compras" in resultado
    
    lista = shopping_service.repository.get_all_items_from_list(shopping_service.db)
    assert len(lista) == 0

def test_finalizar_compra(service, monkeypatch: MonkeyPatch):
    shopping_service, chat_log_service = service
    shopping_service.repository.add_item_to_list(shopping_service.db, "UserTeste", "Café")
    shopping_service.repository.add_item_to_list(shopping_service.db, "UserTeste", "Leite")
    
    comando = RespostaIA(
        comandos=[ItemComando(
            acao=AcaoEnum.FINALIZAR, 
            itens=[], 
            valor=50.0, 
            supermercado="Assai"
        )]
    )

    monkeypatch.setattr(shopping_service.ai_service, "process_message", lambda msg, hist: comando)
    resultado, *_ = shopping_service.execute_command("mensagem de teste", "UserTeste")
    assert "compra finalizada, valor total: R$ 50.00 no supermercado Assai" in resultado
    
    lista = shopping_service.repository.get_all_items_from_list(shopping_service.db)
    assert len(lista) == 0

    