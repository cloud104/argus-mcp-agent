import os
import json
from pathlib import Path
import importlib
from dotenv import load_dotenv

load_dotenv()

# Define o caminho para o ficheiro de configuração de modelos
BASE_DIR = Path(__file__).parent.parent.parent
MODELS_CONFIG_PATH = BASE_DIR / "config" / "models.json"

def load_models_config():
    """Lê e carrega a configuração dos modelos do ficheiro JSON."""
    try:
        with open(MODELS_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"AVISO: Não foi possível carregar {MODELS_CONFIG_PATH}, a usar valores padrão. Erro: {e}")
        return {}

MODEL_MAP = load_models_config()

# Mapeia o 'provider' da configuração para a variável de ambiente correta
API_KEY_MAP = {
    "openai": "OPENAI_API_KEY",
    "google": "GOOGLE_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY"
}

def get_llm(model_key: str, temperature: float = 0.1):
    """
    Retorna uma instância de um modelo de linguagem com base na configuração externa,
    passando explicitamente a chave de API.
    """
    if not MODEL_MAP:
        raise RuntimeError("A configuração de modelos não pôde ser carregada. Verifique o ficheiro config/models.json.")

    if model_key not in MODEL_MAP:
        raise ValueError(f"Chave de modelo '{model_key}' não encontrada em config/models.json.")

    config = MODEL_MAP[model_key]
    provider = config.get("provider")
    class_path = config.get("class_path")
    model_name = config.get("model_name")

    if not all([provider, class_path, model_name]):
         raise ValueError(f"Configuração inválida para a chave '{model_key}' em models.json.")

    # Obtém o nome da variável de ambiente e lê a chave
    api_key_name = API_KEY_MAP.get(provider)
    if not api_key_name:
        raise ValueError(f"Provedor '{provider}' desconhecido na configuração de chaves de API.")
    
    api_key = os.getenv(api_key_name)
    if not api_key:
        raise ValueError(f"A chave de API '{api_key_name}' não foi encontrada nas variáveis de ambiente. Verifique o seu ficheiro .env.")

    try:
        module_path, class_name = class_path.rsplit('.', 1)
        module = importlib.import_module(module_path)
        model_class = getattr(module, class_name)
    except (ImportError, AttributeError) as e:
        raise ImportError(f"Não foi possível carregar a classe '{class_path}': {e}")

    # Passa a chave de API diretamente para o construtor do modelo
    return model_class(
        model=model_name,
        temperature=temperature,
        api_key=api_key
    )

