# tools/server.py
import os
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from fastapi import FastAPI
from dotenv import load_dotenv
from elasticsearch import AsyncElasticsearch
import pandas as pd
from sklearn.ensemble import IsolationForest

from fastmcp import FastMCP
from tools.rag_manager import get_rag_manager

load_dotenv()

ES_HOST = os.getenv("ES_HOST")
ES_USER = os.getenv("ES_USER")
ES_PASSWORD = os.getenv("ES_PASSWORD")
if not all([ES_HOST, ES_USER, ES_PASSWORD]):
    raise RuntimeError("ES_HOST, ES_USER e ES_PASSWORD devem estar definidos.")

# ---------------- MCP server ----------------
mcp = FastMCP("SRE Analysis Tools 🚀")

_es: Optional[AsyncElasticsearch] = None
rag_manager = get_rag_manager()

async def _ensure_es() -> AsyncElasticsearch:
    global _es
    if _es is None:
        print("[tools] Inicializando conexão ES…")
        _es = AsyncElasticsearch(
            ES_HOST,
            basic_auth=(ES_USER, ES_PASSWORD),
            verify_certs=False,
            request_timeout=30,
        )
        info = await _es.info()
        print(f"[tools] ES conectado: cluster='{info.get('cluster_name')}'")
    return _es

def _collection_from_index(index: str) -> str:
    parts = index.split("_")
    return f"{parts[0]}_{parts[1]}" if len(parts) > 1 else index

# ---------------- TOOLS ----------------
@mcp.tool()
async def search_logs(index: str, window: str = "2h") -> Dict[str, Any]:
    """Busca até 200 logs recentes do índice dentro da janela (ex.: '2h', '15m')."""
    es = await _ensure_es()
    resp = await es.search(
        index=index,
        query={"range": {"timestamp": {"gte": f"now-{window}", "lte": "now"}}},
        size=200,
        sort=[{"timestamp": {"order": "desc"}}],
    )
    hits = (resp.get("hits") or {}).get("hits", [])
    return {"logs_encontrados": [h.get("_source", {}) for h in hits]}

@mcp.tool()
def retrieve_historical_context(index: str, query: str) -> Dict[str, Any]:
    """Consulta resumos históricos no RAG para o índice informado."""
    collection_name = _collection_from_index(index)
    summaries = rag_manager.query_summaries(collection_name, query)
    return {"historico_relevante": summaries}

@mcp.tool()
def save_analysis_summary(index: str, summary: str) -> Dict[str, Any]:
    """Persiste um resumo de análise no RAG store."""
    collection_name = _collection_from_index(index)
    metadata = {"timestamp": datetime.now(timezone.utc).isoformat()}
    rag_manager.add_summary(collection_name, summary, metadata)
    return {"status": "success"}

@mcp.tool()
def detect_timeseries_anomalies(data: List[Dict[str, Any]], contamination: float = 0.1) -> Dict[str, Any]:
    """Detecta anomalias simples em série temporal via IsolationForest."""
    if not data or len(data) < 2:
        return {"error": "Dados insuficientes para detecção de anomalias."}
    df = pd.DataFrame(data)
    if "timestamp" not in df.columns or "value" not in df.columns:
        return {"error": "Entrada deve conter 'timestamp' e 'value'."}
    model = IsolationForest(contamination=contamination, random_state=42)
    preds = model.fit_predict(df[["value"]].values)
    df["is_anomaly"] = (preds == -1)
    return {"anomalies_detected": df[df["is_anomaly"]].to_dict("records")}

mcp_app = mcp.http_app(path="/")  # <<=== IMPORTANTE: path="/" dentro do sub-app
app = FastAPI(title="Tool Server (MCP HTTP)", lifespan=mcp_app.lifespan)
app.mount("/mcp", mcp_app)        # sub-app recebe /mcp/*  -> dentro dele vira "/"

@app.get("/")
def health():
    return {"status": "ok", "server": "SRE Analysis Tools 🚀"}
if __name__ == "__main__":
    import uvicorn
    # Forçar lifespan ON e evitar reload enquanto valida integração
    uvicorn.run("tools.server:app", host="0.0.0.0", port=8002, reload=False, lifespan="on")
