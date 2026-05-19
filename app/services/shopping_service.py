from sqlalchemy.orm import Session
from app.services.ai_service import AIService
from app.repositories.shopping_repository import ShoppingRepository
from app.repositories.chat_log_repository import ChatLogRepository

prioridade = {
    "manter": 1,
    "finalizar": 2,
    "adicionar": 3,
    "remover": 4,
    "listar": 5,
    "analise": 6
}

class ShoppingService:
    def __init__(self, db: Session):
        self.db: Session = db
        self.ai_service = AIService()
        self.repository = ShoppingRepository

    def execute_command(self, user_message: str, user_name: str):
        user_messages = ChatLogRepository.get_last_user_messages(self.db, user_name)
        history = []
        for msg in user_messages:
            history.append({"role": "user", "parts": [{"text": msg.pergunta}]})
            history.append({"role": "model", "parts": [{"text": msg.resposta}]})

        ia_response = self.ai_service.process_message(user_message, history)

        # prepara listas
        itens_recem_adicionados = []
        itens_comprados = []
        itens_mantidos = []
        lista_de_itens = []
        itens_para_pesquisar = []
        resultados = []

        # ordena os comandos por ordem lógica para evitar problemas na execução
        ia_response.comandos.sort(key=lambda x: prioridade[x.acao.value])

        for comando in ia_response.comandos:
            print(f"DEBUG: Acao={comando.acao.value}, Items={comando.itens}, Valor={comando.valor}, Supermercado={comando.supermercado}")
            if comando.acao == "listar":
                itens_lista = self.repository.get_all_items_from_list(self.db)
                for item in itens_lista:
                    lista_de_itens.append(f"{item.nome_item}")

            elif comando.acao == "adicionar":
                for item in comando.itens:
                    item = item.lower()
                    if self.repository.check_if_product_has_been_added_in_last_48_hours(self.db, item):
                        itens_recem_adicionados.append(item)
                        resultados.append(f"produto {item} ja foi adicionado nas ultimas 48h")
                    else:
                        self.repository.add_item_to_list(self.db, user_name, item, 1)
                        resultados.append(f"produto {item} adicionado na lista de compras")

            elif comando.acao == "remover":
                if "todos os itens" in comando.itens:
                    self.repository.remove_all_items_from_list(self.db)                    
                    resultados.append(f"todos os itens foram removidos da lista de compras")
                else:
                    for item in comando.itens:
                        item = item.lower()
                        if self.repository.remove_item_from_list(self.db, item):
                            resultados.append(f"produto {item} removido da lista de compras")
                        else:
                            resultados.append(f"produto {item} nao foi encontrado na lista de compras")
                        
            elif comando.acao == "manter":
                for item in comando.itens:
                    item = item.lower()
                    itens_mantidos.append(item)
                    resultados.append(f"produto {item} mantido na lista de compras")

            elif comando.acao == "finalizar":
                itens_lista = self.repository.get_all_items_from_list(self.db)
                for item in itens_lista:
                    if item.nome_item not in itens_mantidos:
                        item.nome_item = item.nome_item.lower()
                        itens_comprados.append(item.nome_item)
                        self.repository.remove_item_from_list(self.db, item.nome_item)
                self.repository.add_shopping_to_history(self.db, user_name, comando.valor, comando.supermercado, itens_comprados)
                if comando.supermercado:
                    resultados.append(f"compra finalizada, valor total: R$ {comando.valor:.2f} no supermercado {comando.supermercado}")
                else:
                    resultados.append(f"compra finalizada, valor total: R$ {comando.valor:.2f}")
            
            elif comando.acao == "pesquisar_precos":
                itens_lista = self.repository.get_all_items_from_list(self.db)
                for item in itens_lista:
                    itens_para_pesquisar.append(item.nome_item)
                itens_pesquisados = self.ai_service.search(itens_para_pesquisar, comando.supermercado)
                

        print("RESULTADOS: ", resultados)
        # print("ITENS COMPRADOS", itens_comprados)
        # print("ITENS MANTIDOS", itens_mantidos)
        # print("LISTA DE ITENS", lista_de_itens)
        # print("ITENS RECEM ADICIONADOS", itens_recem_adicionados)
        
        return resultados, lista_de_itens
