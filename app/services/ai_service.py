from google import genai
from google.genai import types
from app.core.config import settings_ia_key
from app.schemas.bot_schema import RespostaIA

class AIService:
    def __init__(self):
        self.client = genai.Client(api_key=settings_ia_key())
        self.model_id = "gemini-2.5-flash-lite"

    def process_message(self, user_message: str, history: list) -> RespostaIA:
        response = self.client.models.generate_content(
            model=self.model_id,
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction="Você é um bot de lista de compras. "
                "Analise a mensagem do usuário e gere uma lista de comandos para "
                "adicionar, remover itens da lista de compras ou listar os itens da lista."
                "Considere que a mensagem pode conter itens para adicionar e itens para remover pois foram comprados "
                "e itens que já foram comprados que devem ir para o historico com o valor ou sem valor. ",
                response_mime_type="application/json", 
                response_schema=RespostaIA
            )
        )
        return response.parsed

if __name__ == "__main__":
    service = AIService()
    
    test_message = "Adicione limão, coca zero, leite em pó, café e mamão na lista de compras e compramos a banana e o açúcar, gastamos 10 reais."
    
    print(f"Enviando mensagem: {test_message}")
    response = service.process_message(test_message, [])
    
    print(response.model_dump_json(indent=2))