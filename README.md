# IA Mercado 🛒 - Assistente Inteligente de Lista de Compras

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![FastAPI](https://img.shields.io/badge/FastAPI-0058ed?style=for-the-badge&logo=fastapi&logoColor=white)
![Google Gemini](https://img.shields.io/badge/Google%20Gemini-4285F4?style=for-the-badge&logo=google&logoColor=white)
![Twilio](https://img.shields.io/badge/Twilio-F22F46?style=for-the-badge&logo=twilio&logoColor=white)
![MySQL](https://img.shields.io/badge/mysql-%2300f.svg?style=for-the-badge&logo=mysql&logoColor=white)

O **IA Mercado** é um projeto inovador que integra Inteligência Artificial Generativa com o cotidiano do usuário através do WhatsApp. O sistema permite a gestão completa de listas de compras utilizando processamento de linguagem natural, facilitando a organização doméstica de forma simples e intuitiva.

## 📝 Visão Geral

O projeto nasceu da necessidade de simplificar a criação e manutenção de listas de mercado. Em vez de utilizar aplicativos complexos ou papel, o usuário envia mensagens de texto via WhatsApp, e a IA interpreta as intenções, gerindo o banco de dados de itens de forma inteligente.

### Principais Funcionalidades:
- **Gestão via WhatsApp**: Interface familiar e acessível.
- **Processamento de Linguagem Natural**: Compreende comandos complexos como *"Adicione leite e café, mas remova o sabão"*.
- **Finalização Inteligente**: Calcula gastos totais e permite manter itens específicos na lista (ex: "comprei tudo exceto a carne").
- **Prevenção de Duplicidade**: Evita a adição repetida de produtos em uma janela de 48h.
- **Resumos Automáticos**: Gera resumos amigáveis das ações realizadas utilizando a API do Gemini. 
- **Pesquisa de Preços**: Realiza pesquisa de preços dos itens da lista em supermercados próximos ao usuário.
- **Análise de Compras**: Realiza análise de compras passadas e gera relatórios.

## 🚀 Tecnologias Utilizadas

- **Backend**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.12+)
- **IA**: [Google Gemini 3](https://ai.google.dev/)
- **Mensageria**: [Twilio API for WhatsApp](https://www.twilio.com/whatsapp) ou [EvolutionAPI CloudAPI](https://github.com/evolution-foundation/evolution-api)
- **Banco de Dados**: MySQL com [SQLAlchemy ORM](https://www.sqlalchemy.org/)
- **Migrações**: [Alembic](https://alembic.sqlalchemy.org/)
- **Tunneling**: [ngrok](https://ngrok.com/) (para desenvolvimento local)
- **Validação de Dados**: [Pydantic](https://docs.pydantic.dev/)

## 🏗️ Arquitetura

O projeto segue princípios de **Clean Code** e organização modular:

- `app/routers`: Webhooks e rotas da API.
- `app/services`: Lógica de negócio e integração com Gemini.
- `app/repositories`: Abstração da camada de dados (CRUD).
- `app/models`: Definição das tabelas SQL.
- `app/schemas`: Contratos de dados e validação.
- `app/core`: Configurações globais e conexão com DB.
- `app/tests`: Testes unitários mockados e testes de integração do LLM.

## 📋 Pré-requisitos

- Python 3.10+
- Servidor MySQL
- Conta no [Twilio Console](https://www.twilio.com/console) ou Instância no EvolutionAPI (recomendado usar CloudAPI no EvolutionAPI)
- API Key do [Google AI Studio (Gemini)](https://aistudio.google.com/)

## ⚙️ Configuração e Instalação

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/seu-usuario/ia_mercado.git
   cd ia_mercado
   ```

2. **Crie e ative o ambiente virtual:**
   ```bash
   python -m venv venv
   # No Windows:
   .\venv\Scripts\activate
   # No Linux/Mac:
   source venv/bin/activate
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Variáveis de Ambiente:**
   Crie um arquivo `.env` na raiz do projeto seguindo o modelo do `.env_example`.
   **OBS**: É necessário configurar um usuário no `.env`, a IA só responde usuários cadastrados.

5. **Banco de Dados:**
   ```bash
   alembic upgrade head
   ```

## 🛠️ Como Executar

1. **Inicie o servidor FastAPI:**
   ```bash
   uvicorn app.main:app --reload
   ```

2. **Inicie o túnel ngrok:**
   ```bash
   ngrok http 8000
   ```

3. **Configuração do Webhook:**
   No Twilio, configure a URL do seu Sandbox para:
   `https://SUA_URL_NGROK.ngrok-free.app/whatsapp_message`

## 📱 Exemplos de Uso

- **Comando**: "Adicione pão e leite."
- **Resposta**: "Pão e leite adicionados com sucesso! ✅"
<br>

- **Comando**: "Finalizei a compra, gastei 100 reais, mas mantenha a carne na lista."
- **Resposta**: "Compra finalizada (R$ 100,00). Carne continua na lista para a próxima! 🛒"

---
Projeto desenvolvido para fins de portfólio.
