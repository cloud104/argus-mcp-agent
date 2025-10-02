import asyncio
import logging
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, TypedDict, Optional, Dict, Any, Literal

from app.agent.workflow import run_initial_analysis, run_deep_dive_analysis, run_log_explanation, run_chat_turn
router = APIRouter()

# Carrega timeouts das variáveis de ambiente
TIMEOUT_INITIAL = float(os.getenv("API_TIMEOUT_INITIAL", "120"))
TIMEOUT_DEEP_DIVE = float(os.getenv("API_TIMEOUT_DEEP_DIVE", "120"))
TIMEOUT_CHAT = float(os.getenv("API_TIMEOUT_CHAT", "120"))
TIMEOUT_LOG_EXPLAIN = float(os.getenv("API_TIMEOUT_LOG_EXPLAIN", "30"))

class AnalysisRequest(BaseModel):
    msg: str
    index: str
    window: str
    session_id: str

class DeepDiveRequest(BaseModel):
    msg: str
    index: str
    session_id: str
    tool_params: Dict[str, Any]
    
    
class ChatRequest(BaseModel):
    user_input: str
    session_id: str
    initial_context: Optional[Dict[str, Any]] = None
   

class ExplainLogRequest(BaseModel):
    log_line: str

@router.post("/initial-analysis", tags=["Analysis"])
async def initial_analysis(request: AnalysisRequest):
    try:
        tool_params = {"index": request.index, "window": request.window}
        result = await asyncio.wait_for(
            run_initial_analysis(request.msg, request.session_id, tool_params),
            timeout=TIMEOUT_INITIAL,
        )
        return result
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=408,
            detail=f"A análise inicial excedeu o tempo limite de {TIMEOUT_INITIAL} segundos."
        )
    except Exception as e:
        logging.exception("Erro interno em /initial-analysis")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/deep-dive", tags=["Analysis"])
async def deep_dive_analysis(request: DeepDiveRequest):
    try:
        result = await asyncio.wait_for(
            run_deep_dive_analysis(request.msg, request.session_id, request.tool_params),
            timeout=TIMEOUT_DEEP_DIVE,
        )
        return result
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=408,
            detail=f"A análise profunda excedeu o tempo limite de {TIMEOUT_DEEP_DIVE} segundos."
        )
    except Exception as e:
        logging.error(f"Erro interno em /deep-dive: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ocorreu um erro interno na análise profunda: {e}")

@router.post("/explain-log-line", tags=["Analysis"])
async def explain_log(request: ExplainLogRequest):
    logging.info(f"Recebida solicitação para /explain-log-line com log_line: {request.log_line}")
    if not request.log_line:
        raise HTTPException(status_code=400, detail="A linha de log não pode estar vazia.")
    try:
        result = await asyncio.wait_for(
            run_log_explanation(request.log_line),
            timeout=TIMEOUT_LOG_EXPLAIN
        )
        return result
    except asyncio.TimeoutError:
         raise HTTPException(status_code=408, detail="A solicitação de explicação excedeu o tempo limite.")
    except Exception as e:
        logging.exception("Erro interno em /explain-log-line")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", tags=["Analysis"])
async def chat(request: ChatRequest):
    try:
        result = await asyncio.wait_for(
            run_chat_turn(request.user_input, request.session_id, request.initial_context),
            timeout=TIMEOUT_CHAT,
        )
        return result
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="A sua pergunta excedeu o tempo limite.")
    except Exception as e:
        logging.exception("Erro interno em /chat")
        raise HTTPException(status_code=500, detail=str(e))

