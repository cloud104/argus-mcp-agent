from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os
import httpx
import logging

# Carrega as variáveis de ambiente
load_dotenv()

# Importa o router do ficheiro de rotas
from app.api import routes

# Cria a instância da aplicação
app = FastAPI(title="SRE Agent com LangGraph e MCP")

# Inclui as rotas definidas no outro ficheiro
app.include_router(routes.router)

# Serve o frontend
static_dir = os.path.join(os.path.dirname(__file__), 'app/frontend')
app.mount("/static", StaticFiles(directory=static_dir), name="static")

logger = logging.getLogger(__name__)

# Health check helpers
async def check_mcp_server() -> bool:
    """Verifica se o MCP server está disponível."""
    mcp_url = os.getenv("MCP_SERVER_URL", "http://argus-mcp-server:8002/mcp/")
    base_url = mcp_url.rstrip("/mcp/")
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(f"{base_url}/")
            return response.status_code == 200
    except Exception as e:
        logger.warning(f"MCP server check failed: {e}")
        return False

@app.get("/", response_class=FileResponse, include_in_schema=False)
def read_root():
    """Serve o ficheiro HTML do frontend."""
    return FileResponse(os.path.join(static_dir, 'index.html'))

@app.get("/health/live", tags=["Health"])
async def liveness():
    """
    Liveness probe - Verifica se a aplicação está viva.
    Retorna 200 se o processo está rodando.
    """
    return {"status": "alive"}

@app.get("/health/ready", tags=["Health"])
async def readiness():
    """
    Readiness probe - Verifica se a aplicação está pronta para receber tráfego.
    Verifica dependências: MCP Server.
    """
    checks = {
        "mcp_server": await check_mcp_server()
    }
    all_ready = all(checks.values())
    status_code = 200 if all_ready else 503
    return JSONResponse(
        content={
            "status": "ready" if all_ready else "not_ready",
            "checks": checks
        },
        status_code=status_code
    )

@app.get("/health/startup", tags=["Health"])
async def startup():
    """
    Startup probe - Verifica se a aplicação terminou a inicialização.
    Kubernetes usa isso para saber quando começar os outros probes.
    """
    # Verifica se os grafos foram inicializados
    try:
        from app.agent.workflow import _initial_graph
        tools_initialized = _initial_graph is not None
    except Exception:
        tools_initialized = False

    return JSONResponse(
        content={
            "status": "started" if tools_initialized else "starting",
            "tools_initialized": tools_initialized
        },
        status_code=200 if tools_initialized else 503
    )

@app.on_event("shutdown")
async def shutdown_event():
    """
    Graceful shutdown - Fecha recursos e aguarda requests em andamento.
    """
    logger.info("Iniciando shutdown graceful...")
    # Aqui poderíamos fechar outros recursos se necessário
    logger.info("Shutdown completo")

# Bloco de execução (opcional, já que usamos 'uv run')
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=9003, reload=True)

