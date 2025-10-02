import os
import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Any

class RAGManager:
    """
    Uma classe base abstrata para definir o contrato de um gestor de RAG.
    """
    def add_summary(self, collection_name: str, summary: str, metadata: Dict[str, Any]):
        raise NotImplementedError

    def query_summaries(self, collection_name: str, query: str, n_results: int = 3) -> List[str]:
        raise NotImplementedError

class ChromaRAGManager(RAGManager):
    """Implementação concreta do gestor de RAG usando ChromaDB (embedded ou standalone)."""
    def __init__(self, mode: str = "embedded", host: str = "localhost", port: int = 8000, path: str = "./chroma_db"):
        """
        Inicializa o cliente ChromaDB.

        Args:
            mode: 'embedded' para modo local, 'standalone' para servidor HTTP
            host: Host do servidor ChromaDB (usado apenas em modo standalone)
            port: Porta do servidor ChromaDB (usado apenas em modo standalone)
            path: Caminho local para persistência (usado apenas em modo embedded)
        """
        if mode == "standalone":
            self.client = chromadb.HttpClient(host=host, port=port)
            print(f"INFO: (RAG) Cliente ChromaDB HTTP inicializado: {host}:{port}")
        else:
            self.client = chromadb.PersistentClient(path=path)
            print(f"INFO: (RAG) Cliente ChromaDB persistente inicializado: {path}")

        # Usa DefaultEmbeddingFunction (leve, sem modelos ML pesados)
        # Para produção, considere usar OpenAI/HuggingFace API embeddings
        self.embedding_function = embedding_functions.DefaultEmbeddingFunction()

    def _get_collection(self, collection_name: str):
        return self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function
        )

    def add_summary(self, collection_name: str, summary: str, metadata: Dict[str, Any]):
        collection = self._get_collection(collection_name)
        # Usa o timestamp como ID para garantir unicidade
        doc_id = str(metadata.get("timestamp", ""))
        collection.upsert(
            documents=[summary],
            metadatas=[metadata],
            ids=[doc_id]
        )
        print(f"INFO: (RAG) Resumo guardado na coleção '{collection_name}' com ID '{doc_id}'.")

    def query_summaries(self, collection_name: str, query: str, n_results: int = 3) -> List[str]:
        try:
            collection = self._get_collection(collection_name)
            if collection.count() == 0:
                return []
            results = collection.query(
                query_texts=[query],
                n_results=min(n_results, collection.count())
            )
            return results['documents'][0] if results and results['documents'] else []
        except Exception as e:
            print(f"AVISO: (RAG) Não foi possível consultar a coleção '{collection_name}': {e}")
            return []

def get_rag_manager() -> RAGManager:
    """
    Função de fábrica que retorna a instância do gestor de RAG.
    Lê configuração de variáveis de ambiente:
    - CHROMA_MODE: 'embedded' ou 'standalone' (padrão: embedded)
    - CHROMA_HOST: host do servidor (padrão: localhost)
    - CHROMA_PORT: porta do servidor (padrão: 8000)
    """
    mode = os.getenv("CHROMA_MODE", "embedded")
    host = os.getenv("CHROMA_HOST", "localhost")
    port = int(os.getenv("CHROMA_PORT", "8000"))
    path = os.getenv("CHROMA_PATH", "./chroma_db")

    return ChromaRAGManager(mode=mode, host=host, port=port, path=path)
