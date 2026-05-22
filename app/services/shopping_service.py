from typing import TypedDict, List, Optional
from sqlalchemy.orm import Session
from langgraph.graph import StateGraph, START, END
from app.services.ai_service import AIService
from app.repositories.shopping_repository import ShoppingRepository
from app.repositories.chat_log_repository import ChatLogRepository
from app.schemas.bot_schema import ItemComando

prioridade = {
    "manter": 1,
    "finalizar": 2,
    "adicionar": 3,
    "remover": 4,
    "listar": 5,
    "pesquisar_precos": 6,
    "analisar": 7
}

class AgentState(TypedDict):
    user_message: str
    user_name: str
    state: Optional[str]
    history: List[dict]
    commands: List[ItemComando]
    current_command_index: int
    resultados: List[str]
    lista_de_itens: List[str]
    itens_mantidos: List[str]
    itens_comprados: List[str]
    mensagem_direta: Optional[str]

class ShoppingService:
    def __init__(self, db: Session):
        self.db: Session = db
        self.ai_service = AIService()
        self.repository = ShoppingRepository

    def _analisar_mensagem_node(self, state: AgentState) -> dict:
        user_messages = ChatLogRepository.get_last_user_messages(self.db, state["user_name"])
        history = []
        for msg in user_messages:
            history.append({"role": "user", "parts": [{"text": msg.pergunta}]})
            history.append({"role": "model", "parts": [{"text": msg.resposta}]})

        ia_response = self.ai_service.process_message(state["user_message"], history)
        print("ia_response", ia_response)
        
        # prepara a lista de comandos e ordena por prioridade lógica
        if not ia_response or not hasattr(ia_response, "comandos"):
            comandos = []
        else:
            comandos = list(ia_response.comandos)
            comandos.sort(key=lambda x: prioridade[x.acao.value])
        
        mensagem_direta = None
        if ia_response and hasattr(ia_response, "mensagem_direta"):
            if not comandos:
                mensagem_direta = ia_response.mensagem_direta
        
        return {
            "history": history,
            "commands": comandos,
            "current_command_index": 0,
            "mensagem_direta": mensagem_direta
        }

    def _gerenciar_lista_node(self, state: AgentState) -> dict:
        cmd = state["commands"][state["current_command_index"]]
        resultados = list(state.get("resultados") or [])
        lista_de_itens = list(state.get("lista_de_itens") or [])
        itens_mantidos = list(state.get("itens_mantidos") or [])
        itens_comprados = list(state.get("itens_comprados") or [])
        
        print(f"DEBUG (LangGraph): Acao={cmd.acao.value}, Items={cmd.itens}, Valor={cmd.valor}, Supermercado={cmd.supermercado}, Periodo={cmd.periodo}")
        
        if cmd.acao == "listar":
            itens_lista = self.repository.get_all_items_from_list(self.db)
            for item in itens_lista:
                lista_de_itens.append(f"- {item.nome_item}")

        elif cmd.acao == "adicionar":
            for item in cmd.itens:
                item = item.lower()
                if self.repository.check_if_product_has_been_added_in_last_48_hours(self.db, item):
                    resultados.append(f"produto {item} ja foi adicionado nas ultimas 48h")
                else:
                    self.repository.add_item_to_list(self.db, state["user_name"], item, 1)
                    resultados.append(f"produto {item} adicionado na lista de compras")

        elif cmd.acao == "remover":
            if "todos os itens" in cmd.itens:
                self.repository.remove_all_items_from_list(self.db)                    
                resultados.append(f"todos os itens foram removidos da lista de compras")
            else:
                for item in cmd.itens:
                    item = item.lower()
                    if self.repository.remove_item_from_list(self.db, item):
                        resultados.append(f"produto {item} removido da lista de compras")
                    else:
                        resultados.append(f"produto {item} nao foi encontrado na lista de compras")
                    
        elif cmd.acao == "manter":
            for item in cmd.itens:
                item = item.lower()
                itens_mantidos.append(item)
                resultados.append(f"produto {item} mantido na lista de compras")

        elif cmd.acao == "finalizar":
            itens_lista = self.repository.get_all_items_from_list(self.db)
            for item in itens_lista:
                if item.nome_item not in itens_mantidos:
                    item.nome_item = item.nome_item.lower()
                    itens_comprados.append(item.nome_item)
                    self.repository.remove_item_from_list(self.db, item.nome_item)
            self.repository.add_shopping_to_history(self.db, state["user_name"], cmd.valor, cmd.supermercado, itens_comprados)
            if cmd.supermercado:
                resultados.append(f"compra finalizada, valor total: R$ {cmd.valor:.2f} no supermercado {cmd.supermercado}")
            else:
                resultados.append(f"compra finalizada, valor total: R$ {cmd.valor:.2f}")
        
        elif cmd.acao == "analisar":
            historico_compras = self.repository.get_all_items_from_history(self.db, state["user_name"], cmd.periodo)
            if historico_compras:
                periodo_str = cmd.periodo if cmd.periodo else "mês atual"
                linhas_analise = [f"Compras realizadas no período: {periodo_str}\n"]
                total_gasto = 0
                for compra in historico_compras:
                    linhas_analise.append(f"Compra do dia: {compra.data_compra.strftime('%d/%m/%Y')}")
                    linhas_analise.append("Itens da compra:")
                    if isinstance(compra.lista_itens_comprados, list):
                        for item in compra.lista_itens_comprados:
                            linhas_analise.append(f"- {item}")
                    elif isinstance(compra.lista_itens_comprados, str):
                        linhas_analise.append(f"- {compra.lista_itens_comprados}")
                    else:
                        linhas_analise.append("- Sem itens registrados")
                    linhas_analise.append(f"Valor da compra: R$ {compra.gasto_valor:.2f}\n")
                    total_gasto += compra.gasto_valor
                linhas_analise.append(f"Total gasto no período: R$ {total_gasto:.2f}")
                lista_de_itens.append("\n".join(linhas_analise))
            else:
                lista_de_itens.append(f"Nenhuma compra encontrada no período: {cmd.periodo if cmd.periodo else 'mês atual'}")
            

        return {
            "resultados": resultados,
            "lista_de_itens": lista_de_itens,
            "itens_mantidos": itens_mantidos,
            "itens_comprados": itens_comprados,
            "current_command_index": state["current_command_index"] + 1
        }

    def _pesquisar_precos_node(self, state: AgentState) -> dict:
        cmd = state["commands"][state["current_command_index"]]
        lista_de_itens = list(state.get("lista_de_itens") or [])
        itens_para_pesquisar = []
        itens_pesquisados = []
        
        print(f"DEBUG (LangGraph): Acao={cmd.acao.value}, Items={cmd.itens}, Supermercado={cmd.supermercado}")

        if "todos os itens" in cmd.itens:
            itens_lista = self.repository.get_all_items_from_list(self.db)
            for item in itens_lista:
                itens_para_pesquisar.append(item.nome_item)
            pesquisa = self.ai_service.search(itens_para_pesquisar, cmd.supermercado, state["state"])
        else:
            pesquisa = self.ai_service.search(cmd.itens, cmd.supermercado, state["state"])
        
        if pesquisa and hasattr(pesquisa, "itens_pesquisados"):
            for item in pesquisa.itens_pesquisados:
                itens_pesquisados.append(f"{item}\n")
            itens_pesquisados.append(f"Valor total: R$ {pesquisa.soma_total:.2f}")
            lista_de_itens.append(f"**Pesquisa de Preços no {pesquisa.nome_supermercado}**\n" + ''.join(itens_pesquisados))

        return {
            "lista_de_itens": lista_de_itens,
            "current_command_index": state["current_command_index"] + 1
        }

    def _route_commands(self, state: AgentState) -> str:
        if state["current_command_index"] >= len(state["commands"]):
            return "end"
        
        cmd = state["commands"][state["current_command_index"]]
        if cmd.acao == "pesquisar_precos":
            return "pesquisar_precos"
        else:
            return "gerenciar_lista"

    def execute_command(self, user_message: str, user_name: str, state: str = None):
        # definicao do workflow
        workflow = StateGraph(AgentState)
        
        # adiciona os nós
        workflow.add_node("analisar_mensagem", self._analisar_mensagem_node)
        workflow.add_node("gerenciar_lista", self._gerenciar_lista_node)
        workflow.add_node("pesquisar_precos", self._pesquisar_precos_node)
        
        # adiciona as transições
        workflow.add_edge(START, "analisar_mensagem")
        
        workflow.add_conditional_edges(
            "analisar_mensagem",
            self._route_commands,
            {
                "gerenciar_lista": "gerenciar_lista",
                "pesquisar_precos": "pesquisar_precos",
                "end": END
            }
        )
        
        workflow.add_conditional_edges(
            "gerenciar_lista",
            self._route_commands,
            {
                "gerenciar_lista": "gerenciar_lista",
                "pesquisar_precos": "pesquisar_precos",
                "end": END
            }
        )
        
        workflow.add_conditional_edges(
            "pesquisar_precos",
            self._route_commands,
            {
                "gerenciar_lista": "gerenciar_lista",
                "pesquisar_precos": "pesquisar_precos",
                "end": END
            }
        )
        
        # compila o grafo
        app = workflow.compile()
        
        # executa
        initial_state = {
            "user_message": user_message,
            "user_name": user_name,
            "state": state,
            "history": [],
            "commands": [],
            "current_command_index": 0,
            "resultados": [],
            "lista_de_itens": [],
            "itens_mantidos": [],
            "itens_comprados": [],
            "mensagem_direta": None
        }
        
        final_state = app.invoke(initial_state)
        
        print("RESULTADOS (LangGraph): ", final_state["resultados"])
        
        return final_state["resultados"], final_state["lista_de_itens"], final_state.get("mensagem_direta")

