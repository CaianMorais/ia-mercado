from google import genai
from google.genai import types
from app.core.config import settings_ia_key
from app.schemas.bot_schema import RespostaIA, ResumoIA, PesquisaPrecos
from sqlalchemy.orm import Session

class AIService:
    def __init__(self):
        self.client = genai.Client(api_key=settings_ia_key())
        self.model_id = ["gemini-3.1-flash-lite", "gemini-3.1-flash-lite-preview", "gemini-2.5-flash-lite", "gemini-2.5-flash", "gemini-3-flash-preview"]

    def process_message(self, user_message: str, history: list) -> RespostaIA:
        for model_id in self.model_id:
            try:
                current_message = {"role": "user", "parts": [{"text": user_message}]}
                messages = history + [current_message]

                response = self.client.models.generate_content(
                    model=model_id,
                    contents=messages,
                    config=types.GenerateContentConfig(
                        system_instruction="Você é um bot de lista de compras. "
                        "Analise a mensagem do usuário e gere uma lista de comandos para "
                        "adicionar, remover itens da lista de compras ou listar os itens da lista."
                        "Considere que a mensagem pode conter itens para adicionar e itens para remover."
                        "Ao ser informado que todos os itens deve ser removido, use a ação remover e adicione o termo 'todos os itens' em itens no comando "
                        "Ao ser informado que a compra foi finalizada, a ação será finalizar a compra com todos os itens da lista e salvando o valor"
                        "Se for informado exceção de compra de algum item da lista use a ação manter para manter o item na lista "
                        "Se for informado o nome de um supermercado, identifique-o use a ação supermercado no comando "
                        "Sempre analise o histórico para resolver pronomes (como 'ele', 'o', 'aquele'). "
                        "Se o usuário pedir para remover 'o' ou 'este' logo após adicionar um item, "
                        "entenda que ele se refere ao último item mencionado, e não à lista completa, "
                        "a menos que ele diga explicitamente 'tudo' ou 'todos'. "
                        "Se for feito um pedido de pesquisa de preços, use a ação pesquisar_precos no comando "
                        "Se for feito um pedido de pesquisa de preços com o nome de um supermercado, use a ação pesquisar_precos no comando e adicione o nome do supermercado no comando "
                        "Se na mensagem der a entender que o usuário quer economizar ou quer o mercado que seja mais em conta, não adicione nada em supermercado no comando"
                        "Se for feito um pedido de pesquisa de preços com os itens da lista, apenas adicione o termo 'todos os itens' em items no comando. "
                        "Se na mensagem der a entender que o usuário quer que seja feita uma análise de compras passadas, use a ação analisar no comando." 
                        "Se for feito um pedido de análise de compras, o usuário pode informar que é no período de 30 dias OU no mês atual, adicione o termo '30 dias' ou 'mês atual' no campo periodo, "
                        "Se nao tiver período na mensagem adicione o periodo 'mês atual' no campo periodo por padrao.",
                        response_mime_type="application/json", 
                        response_schema=RespostaIA
                    )
                )
                if response.parsed:
                    return response.parsed
            except Exception as e:
                print(f"MODEL: {model_id} -ERRO AO PROCESSAR MENSAGEM: {e}")
                continue

        return ""

    def resume(self, resultado: list):
        for model_id in self.model_id:
            try:
                resumo = self.client.models.generate_content(
                    model=model_id,
                    contents=resultado,
                    config=types.GenerateContentConfig(
                        system_instruction="Você vai receber informações e dados de ações realizadas, pesquisar ou análises feitas"
                        "Considere que você pode receber uma lista com tudo que foi feito na lista de compras, "
                        "considere que também pode chegar uma lista com pesquisa de preços, "
                        "Considere que também pode chegar uma lista com uma análise de todas as compras feitas no período, "
                        "agora faça um pequeno resumo das informações recebidas. "
                        "Tenha em mente que de acordo com o que foi recebido, o resumo deve estar estruturado de uma forma coerente e organizada"
                        "Evite colocar o nome dos produtos entre aspas no resumo."
                        "Se receber valores em reais (R$) mostre-os da maneira correta."
                        "Se receber nome de supermercado, mostre-o no resumo.",
                        response_mime_type="application/json",
                        response_schema=ResumoIA
                    )
                )
                if resumo.parsed:
                    return resumo.parsed
            except Exception as e:
                print(f"MODEL: {model_id} -ERRO AO PROCESSAR RESUMO: {e}")
                continue
                
        return ""

    def search(self, item: list = [], supermarket: str = None, estado: str = None):
        for model_id in self.model_id:
            try:
                print(f"MODELO EM USO: {model_id}")
                if item and supermarket:
                    conteudo = f"{item} no supermercado {supermarket}"
                else:
                    conteudo = f"{item}"

                if estado:
                    conteudo = f"{conteudo} no estado de {estado}"
                
                print(f"CONTEUDO: {conteudo}")

                grounding_tool = types.Tool(
                    google_search=types.GoogleSearch()
                )

                search = self.client.models.generate_content(
                    model=model_id,
                    contents=conteudo,
                    config=types.GenerateContentConfig(
                        tools=[grounding_tool],
                        system_instruction="Você receberá uma lista de itens e um nome de supermercado "
                        "e deve retornar o preço mais barato de cada item no supermercado pesquisado. "
                        "Se você receber apenas a lista com um item ou mais, sem o nome do supermercado, "
                        "A pesquisa deve retornar o preço daquele item ou itens mais barato possível em grandes redes de supermercados do estado informado, "
                        "mas dê preferência a redes de supermercado que tenha um site próprio onde possa ser feito a pesquisa com os preços em tempo real."
                        "Se não for informado nenhum estado, pesquise em redes de supermercados do Brasil."
                        "Caso você receba o nome do item sem especificar peso, tipo, marca ou tamanho, "
                        "especifique a opção mais comum entre compradores domesticos para aquele item. "
                        "Retorne os resultados na mesma ordem que os itens foram enviados. "
                        "Retorne o preço de cada item individualmente, ao final dê também o resultado somado. "
                        "Adicione o nome do supermercado na resposta.",
                        response_schema=PesquisaPrecos
                    )
                )
                #print("METADADOS DA BUSCA:", search.candidates[0].grounding_metadata)

                if search.parsed:
                    return search.parsed
            except Exception as e:
                print(f"MODEL: {model_id} - ERRO AO PROCESSAR PESQUISA: {e}")
                continue
        return ""

# if __name__ == "__main__":
#     service = AIService()
    
#     test_message = "Adicione limão, coca zero, leite em pó, café e mamão na lista de compras e compramos a banana e o açúcar, gastamos 10 reais."
    
#     print(f"Enviando mensagem: {test_message}")
#     response = service.process_message(test_message, [])
    
#     print(response.model_dump_json(indent=2))