import json
from pathlib import Path
from typing import List, Any, Optional

# Importa o cliente oficial da biblioteca de adaptadores
from langchain_mcp_adapters.client import MultiServerMCPClient

# -----------------------------------------------------------------------------
# Lógica para carregar a configuração do servidor a partir do JSON
# -----------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent.parent.parent
SETTINGS_PATH = BASE_DIR / "config" / "settings.json"

_MCP_CLIENT: Optional[MultiServerMCPClient] = None

def get_mcp_client() -> MultiServerMCPClient:
    """
    Cria e retorna uma instância singleton do MultiServerMCPClient,
    lendo a configuração do ficheiro settings.json.
    """
    global _MCP_CLIENT
    
    if _MCP_CLIENT is None:
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                settings = json.load(f)
            
            # A estrutura esperada em settings.json é:
            # { "mcp_servers": { "tools": { "transport": "...", "url": "..." } } }
            server_config = settings.get("mcp_servers")
            if not server_config:
                raise ValueError("A chave 'mcp_servers' não foi encontrada em settings.json")

            print(f"INFO: (MCPClient) A inicializar cliente com a configuração: {server_config}")
            _MCP_CLIENT = MultiServerMCPClient(server_config)

        except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
            print(f"AVISO: (MCPClient) Falha ao carregar {SETTINGS_PATH}. A usar configuração padrão. Erro: {e}")
            # Fallback para a configuração padrão se o ficheiro falhar
            default_config = {
                "tools": {
                    "transport": "streamable_http",
                    "url": "http://127.0.0.1:9001/mcp",
                }
            }
            _MCP_CLIENT = MultiServerMCPClient(default_config)

    return _MCP_CLIENT

