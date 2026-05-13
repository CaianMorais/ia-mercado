from app.core.config import Base
from sqlalchemy import create_engine
from app.services import chat_log_service
from app.services.chat_log_service import ChatLogService
import pytest
from _pytest.monkeypatch import MonkeyPatch
from app.schemas.bot_schema import RespostaIA, ItemComando, AcaoEnum
from app.services.shopping_service import ShoppingService
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# crie um do banco de dados exclusiva para testes e configure-o no .env
# para garantir que os testes sejam isolados e não afetem o banco de dados de produção
# cada teste terá sua própria sessão de banco de dados
load_dotenv()
TEST_DB_USER = os.getenv("TEST_DB_USER")
TEST_DB_PASSWORD = os.getenv("TEST_DB_PASSWORD")
TEST_DB_HOST = os.getenv("TEST_DB_HOST")
TEST_DB_NAME = os.getenv("TEST_DB_NAME")

SQLALCHEMY_TEST_DATABASE_URL = f"mysql+mysqldb://{TEST_DB_USER}:{TEST_DB_PASSWORD}@{TEST_DB_HOST}/{TEST_DB_NAME}"
if not SQLALCHEMY_TEST_DATABASE_URL:
    raise RuntimeError("Não foi possível conectar a base de testes. Verifique se a configuração está correta.")

engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL)
Base.metadata.create_all(bind=engine)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    
    session = TestingSessionLocal(bind=connection)

    session.execute(text("DELETE FROM lista_compras"))
    session.execute(text("DELETE FROM chat_log"))
    session.execute(text("DELETE FROM historico_compras"))
    session.commit()

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
                itens=["arroz", "feijão"]
            )
        ]
    )

    monkeypatch.setattr(shopping_service.ai_service, "process_message", lambda msg, hist: comando)

    resultado, *_ = shopping_service.execute_command("mensagem de teste", "UserTeste")
    chat_log_service.add_chat_log("UserTeste", "mensagem de teste", "resposta de teste")
    assert "produto arroz adicionado na lista de compras" in resultado
    assert "produto feijão adicionado na lista de compras" in resultado

def test_remover_todos_itens(service, monkeypatch: MonkeyPatch):
    shopping_service, chat_log_service = service

    shopping_service.repository.add_item_to_list(shopping_service.db, "UserTeste", "café")
    shopping_service.repository.add_item_to_list(shopping_service.db, "UserTeste", "leite")

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
    shopping_service.repository.add_item_to_list(shopping_service.db, "UserTeste", "café")
    shopping_service.repository.add_item_to_list(shopping_service.db, "UserTeste", "leite")
    
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

# teste específico para saber se a IA está levando em conta o histórico de mensagens
# para resolver pronomes
def test_contexto_pronome(service):
    shopping_service, chat_log_service = service

    # prepara o teste adicionando itens na lista
    shopping_service.repository.add_item_to_list(shopping_service.db, "UserTeste", "arroz")
    shopping_service.repository.add_item_to_list(shopping_service.db, "UserTeste", "feijão")
    shopping_service.repository.add_item_to_list(shopping_service.db, "UserTeste", "carne")

    # simula o histórico de mensagens no banco de dados
    # contexto: usuário pediu a lista e depois adicionou carne
    chat_log_service.add_chat_log("UserTeste", "mostre a lista de compras", "Arroz, Feijão")
    chat_log_service.add_chat_log("UserTeste", "adicione carne a lista", "Adicionamos carne na lista de compras.")

    # executa o teste igual a aplicação real
    # é necessário testar se a IA entendeu o contexto e resolveu o pronome
    resultado, lista_final = shopping_service.execute_command("remova-o", "UserTeste")

    # o resultado deve indicar a remoção da carne, e não de tudo
    assert "produto carne removido da lista de compras" in resultado
    assert "todos os itens foram removidos" not in str(resultado)
    
    # a lista final deve conter os itens originais (arroz, feijão) e NÃO conter a carne
    itens_no_banco = [item.nome_item for item in shopping_service.repository.get_all_items_from_list(shopping_service.db)]
    assert "arroz" in itens_no_banco
    assert "feijão" in itens_no_banco
    assert "carne" not in itens_no_banco
    assert len(itens_no_banco) == 2