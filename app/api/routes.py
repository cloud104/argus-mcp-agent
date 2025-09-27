import asyncio
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from app.agent.workflow import run_initial_analysis, run_deep_dive_analysis

router = APIRouter()
ANALYSIS_TIMEOUT = 60.0

class AnalysisRequest(BaseModel):
    msg: str
    index: str
    window: str
    session_id: str

# --- CORREÇÃO ---
# O modelo agora espera 'tool_params' em vez de 'window',
# alinhando-se com o que o frontend envia.
class DeepDiveRequest(BaseModel):
    msg: str
    index: str
    session_id: str
    tool_params: Dict[str, Any]

@router.post("/initial-analysis", tags=["Analysis"])
async def initial_analysis(request: AnalysisRequest):
    try:
        tool_params = {"index": request.index, "window": request.window}
        result = await asyncio.wait_for(
            run_initial_analysis(request.msg, request.session_id, tool_params),
            timeout=ANALYSIS_TIMEOUT,
        )
        return result
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=408,
            detail=f"A análise excedeu o tempo limite de {ANALYSIS_TIMEOUT} segundos."
        )
    except Exception:
        logging.exception("Erro interno em /initial-analysis")
        raise HTTPException(status_code=500, detail="Ocorreu um erro interno na análise inicial.")

@router.post("/deep-dive", tags=["Analysis"])
async def deep_dive_analysis(request: DeepDiveRequest):
    try:
        # Agora usamos request.tool_params diretamente, que é o que o frontend envia.
        result = await asyncio.wait_for(
            run_deep_dive_analysis(request.msg, request.session_id, request.tool_params),
            timeout=ANALYSIS_TIMEOUT,
        )
        return result
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=408,
            detail=f"A análise profunda excedeu o tempo limite de {ANALYSIS_TIMEOUT} segundos."
        )
    except Exception:
        logging.exception("Erro interno em /deep-dive")
        raise HTTPException(status_code=500, detail="Ocorreu um erro interno na análise profunda.")

