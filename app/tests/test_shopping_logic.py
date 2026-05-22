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
from app.services.user_service import UserService
from app.models.users import Users

# crie um banco de dados exclusiva para testes e configure-o no .env
# para garantir que os testes sejam isolados e não afetem o banco de dados de produção
# cada teste abrirá uma nova sessão no banco de dados
############### START CONFIGURAÇÃO DO BANCO DE DADOS DE TESTE ###############
load_dotenv()
TEST_DB_USER = os.getenv("TEST_DB_USER")
TEST_DB_PASSWORD = os.getenv("TEST_DB_PASSWORD")
TEST_DB_HOST = os.getenv("TEST_DB_HOST")
TEST_DB_NAME = os.getenv("TEST_DB_NAME")

SQLALCHEMY_TEST_DATABASE_URL = f"mysql+mysqldb://{TEST_DB_USER}:{TEST_DB_PASSWORD}@{TEST_DB_HOST}/{TEST_DB_NAME}"
if not SQLALCHEMY_TEST_DATABASE_URL:
    raise RuntimeError("Não foi possível conectar a base de testes. Verifique se a configuração está correta.")

engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL)
# Limpa e recria todas as tabelas na base de testes para atualizar a estrutura de acordo com as novas models
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    
    session = TestingSessionLocal(bind=connection)

    # Desativa checagem de chave estrangeira temporariamente para limpar as tabelas com segurança
    session.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
    session.execute(text("DELETE FROM lista_compras"))
    session.execute(text("DELETE FROM chat_log"))
    session.execute(text("DELETE FROM historico_compras"))
    session.execute(text("DELETE FROM users"))
    session.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
    session.commit()

    # Cria usuário mock para satisfazer as constraints de chave estrangeira nos testes
    from app.models.users import Users
    user = Users(
        user_name="UserTeste",
        cpf="000.000.000-00",
        phonenumber="123456789",
        zip_code="00000-000",
        city="Test City",
        state="TS",
        active=True
    )
    session.add(user)
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
############### END CONFIGURAÇÃO DO BANCO DE DADOS DE TESTE ###############


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

def test_langgraph_flow_multiple_commands(service, monkeypatch: MonkeyPatch):
    shopping_service, chat_log_service = service
    
    # mock do process_message para retornar múltiplos comandos (Adicionar + Pesquisar Preços)
    comandos = RespostaIA(
        comandos=[
            ItemComando(
                acao=AcaoEnum.ADICIONAR, 
                itens=["maçã"]
            ),
            ItemComando(
                acao=AcaoEnum.PESQUISAR_PRECOS,
                itens=["maçã"],
                supermercado="Pão de Açúcar"
            )
        ]
    )
    monkeypatch.setattr(shopping_service.ai_service, "process_message", lambda msg, hist: comandos)
    
    # mock do search para nao fazer requisicao de rede real
    from app.schemas.bot_schema import PesquisaPrecos
    pesquisa_mock = PesquisaPrecos(
        itens_pesquisados=["maçã: R$ 5.99"],
        soma_total=5.99,
        nome_supermercado="Pão de Açúcar"
    )
    monkeypatch.setattr(shopping_service.ai_service, "search", lambda items, supermarket, state: pesquisa_mock)
    
    # executa o comando via LangGraph
    resultados, lista_de_itens, _ = shopping_service.execute_command("Adicione maçã e pesquise preço no Pão de Açúcar", "UserTeste")
    
    # verifica se ambas as ações foram executadas pelo grafo
    assert "produto maçã adicionado na lista de compras" in resultados
    assert len(lista_de_itens) == 1
    assert "Pesquisa de Preços no Pão de Açúcar" in lista_de_itens[0]
    assert "maçã: R$ 5.99" in lista_de_itens[0]

def test_analisar_historico_compras(service, monkeypatch: MonkeyPatch):
    shopping_service, chat_log_service = service

    # Adiciona compras ao histórico para teste
    shopping_service.repository.add_shopping_to_history(
        shopping_service.db, 
        "UserTeste", 
        valor=20.0, 
        supermercado="Mercado A", 
        itens=["arroz", "feijão"]
    )
    shopping_service.repository.add_shopping_to_history(
        shopping_service.db, 
        "UserTeste", 
        valor=55.0, 
        supermercado="Mercado B", 
        itens=["café", "leite"]
    )

    comando = RespostaIA(
        comandos=[
            ItemComando(
                acao=AcaoEnum.ANALISAR,
                periodo="30 dias"
            )
        ]
    )

    monkeypatch.setattr(shopping_service.ai_service, "process_message", lambda msg, hist: comando)
    resultados, lista_de_itens, _ = shopping_service.execute_command("mensagem de teste", "UserTeste")

    # resultados deve estar vazio para não disparar a IA que faz resumo
    assert len(resultados) == 0

    # O relatório formatado deve estar em lista_de_itens
    assert len(lista_de_itens) == 1
    report = lista_de_itens[0]
    
    assert "Compras realizadas no período: 30 dias" in report
    assert "Compra do dia:" in report
    assert "Itens da compra:" in report
    assert "- arroz" in report
    assert "- feijão" in report
    assert "Valor da compra: R$ 20.00" in report
    assert "- café" in report
    assert "- leite" in report
    assert "Valor da compra: R$ 55.00" in report
    assert "Total gasto no período: R$ 75.00" in report

def test_user_service_registration_checks(db_session):


    user_service = UserService(db_session)

    # testa numero nao cadastrado
    assert user_service.get_active_user_by_phonenumber("999999999") is None

    # adiciona um usuario valido
    active_user = Users(
        user_name="ActiveUser",
        cpf="111.111.111-11",
        phonenumber="5511999998888",
        zip_code="12345-678",
        city="Sao Paulo",
        state="SP", 
        active=True
    )
    db_session.add(active_user)
    db_session.commit()

    # usuário ativo deve ser retornado com sucesso
    found = user_service.get_active_user_by_phonenumber("5511999998888")
    assert found is not None
    assert found.user_name == "ActiveUser"

    # adiciona um usuario inativo
    inactive_user = Users(
        user_name="InactiveUser",
        cpf="222.222.222-22",
        phonenumber="5511999997777",
        zip_code="12345-678",
        city="Sao Paulo",
        state="SP",
        active=False
    )
    db_session.add(inactive_user)
    db_session.commit()

    # usuário inativo não deve ser retornado (retorna None)
    assert user_service.get_active_user_by_phonenumber("5511999997777") is None


def test_mensagem_direta_only_when_no_commands(service, monkeypatch: MonkeyPatch):
    shopping_service, _ = service

    # tem comando, a mensagem_direta nao deve ser disparada (pois a IA vai resumir ou é uma resposta estruturada)
    resposta_com_comando = RespostaIA(
        comandos=[
            ItemComando(
                acao=AcaoEnum.ADICIONAR, 
                itens=["banana"]
            )
        ],
        mensagem_direta="Claro! Adicionando banana para você."
    )
    monkeypatch.setattr(shopping_service.ai_service, "process_message", lambda msg, hist: resposta_com_comando)
    
    _, _, mensagem_direta_retornada = shopping_service.execute_command("Adiciona banana", "UserTeste")
    assert mensagem_direta_retornada is None

    # nao tem comando, a mensagem_dreta será disparada para o whatsapp.
    resposta_sem_comando = RespostaIA(
        comandos=[],
        mensagem_direta="Olá! Como posso te ajudar hoje?"
    )
    monkeypatch.setattr(shopping_service.ai_service, "process_message", lambda msg, hist: resposta_sem_comando)
    
    _, _, mensagem_direta_retornada = shopping_service.execute_command("Olá", "UserTeste")
    assert mensagem_direta_retornada == "Olá! Como posso te ajudar hoje?"

