# Argus Agent - SRE Assistant

Este projeto implementa um agente de IA para análise de logs, construído com uma arquitetura modular e robusta, usando LangGraph e o protocolo MCP.

## Arquitetura
- **Aplicação Principal (`main.py`):** Serve a interface web (FastAPI) na porta 8000 e hospeda o cérebro do agente.
- **Servidor de Ferramentas (`tools/server.py`):** Um servidor MCP (FastMCP) que expõe as ferramentas para o agente na porta 8002.
- **RAG com ChromaDB:** Usa ChromaDB para criar uma base de conhecimento persistente com o histórico das análises, guardada na pasta `chroma_db`.

## Setup

1.  **Crie e entre no diretório do projeto:**
    ```bash
    mkdir argus-agent && cd argus-agent
    ```
    *Copie o conteúdo deste script para os ficheiros correspondentes dentro desta pasta.*

2.  **Copie a Configuração de Ambiente:**
    ```bash
    cp .env.example .env
    ```
    Edite o ficheiro `.env` e adicione as suas chaves de API e verifique as credenciais do Elasticsearch.

3.  **Crie o Ambiente Virtual e Instale as Dependências:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # ou .venv\Scripts\activate no Windows
    uv pip install -r requirements.txt
    ```

## Como Executar

Você precisará de **dois terminais** a correr em simultâneo, ambos dentro da pasta `argus-agent`.

**Terminal 1: Inicie o Servidor de Ferramentas**
```bash
uv run uvicorn tools.server:mcp --port 8002 --reload
```

**Terminal 2: Inicie a Aplicação Principal**
```bash
uv run uvicorn main:app --port 8000 --reload

