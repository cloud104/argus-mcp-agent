from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os

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

@app.get("/", response_class=FileResponse, include_in_schema=False)
def read_root():
    """Serve o ficheiro HTML do frontend."""
    return FileResponse(os.path.join(static_dir, 'index.html'))

# Bloco de execução (opcional, já que usamos 'uv run')
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=9003, reload=True)

