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
    """Implementação concreta do gestor de RAG usando ChromaDB persistente."""
    def __init__(self, path: str = "./chroma_db"):
        self.client = chromadb.PersistentClient(path=path)
        # Usa DefaultEmbeddingFunction (leve, sem modelos ML pesados)
        # Para produção, considere usar OpenAI/HuggingFace API embeddings
        self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
        print("INFO: (RAG) Cliente ChromaDB persistente inicializado com DefaultEmbeddingFunction.")

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
    """
    return ChromaRAGManager()
