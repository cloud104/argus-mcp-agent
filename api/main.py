from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import httpx
import logging

# Carrega as variáveis de ambiente
load_dotenv()

# Importa o router do ficheiro de rotas
from app.api import routes
from app.auth import routes as auth_routes
from app.metrics import routes as metrics_routes
from app.auth.database import init_db

# Cria a instância da aplicação
app = FastAPI(title="Argus API - SRE Agent com LangGraph e MCP")

# CORS - permite requisições do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique o domínio do frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclui as rotas de autenticação
app.include_router(auth_routes.router)

# Inclui as rotas da API principal
app.include_router(routes.router)

# Inclui as rotas de métricas
app.include_router(metrics_routes.router)

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

@app.get("/")
def read_root():
    """Root endpoint - API info."""
    return {
        "name": "Argus API",
        "version": "1.0.0",
        "description": "SRE Agent API com LangGraph e MCP",
        "docs": "/docs"
    }

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

@app.on_event("startup")
async def startup_event():
    """
    Startup - Inicializa banco de dados de autenticação, grafos e ferramentas do MCP.
    """
    logger.info("Iniciando aplicação...")

    # Inicializa banco de dados de autenticação
    try:
        await init_db()
        logger.info("Banco de dados de autenticação inicializado")
    except Exception as e:
        logger.error(f"Erro ao inicializar banco de dados: {e}")

    # Inicializa grafos e ferramentas
    try:
        from app.agent.workflow import ensure_graphs
        await ensure_graphs()
        logger.info("Grafos e ferramentas inicializados com sucesso")
    except Exception as e:
        logger.error(f"Erro ao inicializar grafos: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """
    Graceful shutdown - Fecha recursos e aguarda requests em andamento.
    """
    logger.info("Iniciando shutdown graceful...")

    # Fechar pool de conexões PostgreSQL
    try:
        from app.auth.database import close_pool
        await close_pool()
        logger.info("Pool PostgreSQL fechado")
    except Exception as e:
        logger.error(f"Erro ao fechar pool PostgreSQL: {e}")

    logger.info("Shutdown completo")

# Bloco de execução (opcional, já que usamos 'uv run')
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=9003, reload=True)

