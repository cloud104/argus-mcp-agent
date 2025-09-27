import json
from pathlib import Path
from typing import List, TypedDict, Optional, Dict, Any, Literal
import logging
import uuid
import re
from collections import Counter

from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, ToolMessage
from langchain_community.cache import InMemoryCache
from langchain.globals import set_llm_cache

from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode

from app.agent.client import get_mcp_client
from app.agent.llm_provider import get_llm

# Configuração do Logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Config & Prompts
set_llm_cache(InMemoryCache())
BASE = Path(__file__).parent.parent.parent
PROMPT_INITIAL_SUMMARY = (BASE / "prompts/initial_summary.md").read_text(encoding="utf-8")
PROMPT_SYNTHESIZER = (BASE / "prompts/synthesize_analysis.md").read_text(encoding="utf-8")

# Modelos
initial_llm = get_llm("planner_model")
planner_llm = get_llm("planner_model")
synthesizer_llm = get_llm("synthesizer_model")

# Cliente MCP
mcp_client = get_mcp_client()

# Cache de Ferramentas
_TOOLS: Optional[List[Any]] = None
_tool_node: Optional[ToolNode] = None
_initial_graph = None
_deep_dive_graph = None

async def init_tools() -> List[Any]:
    global _TOOLS
    if _TOOLS is None:
        logger.info("A inicializar ferramentas do servidor MCP pela primeira vez...")
        _TOOLS = await mcp_client.get_tools()
        logger.info(f"Ferramentas MCP carregadas: {[t.name for t in _TOOLS] if _TOOLS else 'Nenhuma'}")
    return _TOOLS

def _extract_latest_tool_message_by_name(messages: List[BaseMessage], tool_name: str) -> Optional[ToolMessage]:
    for msg in reversed(messages):
        if isinstance(msg, ToolMessage) and msg.name == tool_name:
            return msg
    return None

def _extract_json_from_string(text: str) -> Optional[dict]:
    match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match:
        text = match.group(1)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.warning("Falha ao analisar a resposta do LLM como JSON direto.")
        return None

class AgentState(TypedDict):
    messages: List[BaseMessage]
    tool_params: dict
    final_summary: str
    kpis: Dict[str, Any]

# WORKFLOW 1: Análise Inicial
def act_initial_node(state: AgentState):
    logger.info("--- NÓ (Inicial): act ---")
    tool_call = {"name": "search_logs", "args": state["tool_params"], "id": str(uuid.uuid4())}
    response = AIMessage(content="", tool_calls=[tool_call])
    logger.info("--- SAÍDA (act): A preparar chamada para a ferramenta 'search_logs'")
    return {"messages": state["messages"] + [response]}

def aggregate_logs_node(state: AgentState):
    """Processa os logs brutos e calcula os KPIs."""
    logger.info("--- NÓ (Inicial): aggregate_logs ---")
    tool_message = _extract_latest_tool_message_by_name(state["messages"], "search_logs")
    logs = []
    if tool_message and tool_message.content:
        try:
            logs = json.loads(tool_message.content).get("logs_encontrados", [])
        except (json.JSONDecodeError, TypeError):
            logs = []
    
    kpis = { "critical_errors": 0, "warnings": 0, "info_events": 0 }
    if not logs:
        logger.info("--- SAÍDA (aggregate_logs): Nenhum log para agregar.")
        return {"kpis": kpis}

    severities = [log.get("severity", "").upper() for log in logs]
    counts = Counter(severities)
    
    kpis["critical_errors"] = counts.get("FATAL", 0) + counts.get("ERROR", 0) + counts.get("CRITICAL", 0)
    kpis["warnings"] = counts.get("WARNING", 0)
    kpis["info_events"] = counts.get("INFO", 0)

    logger.info(f"--- SAÍDA (aggregate_logs): KPIs calculados: {kpis}")
    return {"kpis": kpis}

async def synthesize_initial_node(state: AgentState):
    logger.info("--- NÓ (Inicial): synthesize ---")
    tool_message = _extract_latest_tool_message_by_name(state["messages"], "search_logs")
    tool_result_content = tool_message.content if tool_message else ""
    kpis = state.get("kpis", {})

    if not tool_result_content.strip() or tool_result_content in ("{}", "[]"):
        logger.info("--- SAÍDA (synthesize_initial): Sem dados para analisar, a retornar mensagem padrão.")
        answer = {"sem_dados": True, "motivo": "A ferramenta de busca não retornou logs."}
        return {"messages": state["messages"] + [AIMessage(content=json.dumps(answer))]}

    kpi_context = f"## KPIs Pré-agregados\n\n{json.dumps(kpis, indent=2)}"
    final_prompt = f"{PROMPT_INITIAL_SUMMARY}\n\n{kpi_context}\n\n## Evidências (Logs Brutos)\n\n{tool_result_content}"
    response = await initial_llm.ainvoke(final_prompt)
    logger.info("--- SAÍDA (synthesize_initial): Dashboard inicial gerado.")
    return {"messages": state["messages"] + [AIMessage(content=response.content)]}

# WORKFLOW 2: Análise Profunda
def retrieve_node(state: AgentState):
    logger.info("--- NÓ: retrieve ---")
    user_input = next((m.content for m in state["messages"] if isinstance(m, HumanMessage)), "")
    idx = state["tool_params"].get("index", "")
    tool_call = {"name": "retrieve_historical_context", "args": {"index": idx, "query": user_input}, "id": str(uuid.uuid4())}
    logger.info("--- SAÍDA (retrieve): A preparar chamada para 'retrieve_historical_context'")
    return {"messages": state["messages"] + [AIMessage(content="", tool_calls=[tool_call])]}

def planner_node(state: AgentState):
    logger.info("--- NÓ: planner ---")
    tool_call = {"name": "search_logs", "args": state["tool_params"], "id": str(uuid.uuid4())}
    logger.info("--- SAÍDA (planner): A preparar chamada para a ferramenta 'search_logs'")
    return {"messages": state["messages"] + [AIMessage(content="", tool_calls=[tool_call])]}

async def synthesize_deep_node(state: AgentState):
    logger.info("--- NÓ: synthesize ---")
    search_logs_msg = _extract_latest_tool_message_by_name(state["messages"], "search_logs")
    tool_result_content = search_logs_msg.content if search_logs_msg else "Sem evidências em tempo real."
    retrieve_msg = _extract_latest_tool_message_by_name(state["messages"], "retrieve_historical_context")
    historical_context = "Sem histórico relevante."
    if retrieve_msg and retrieve_msg.content:
        try:
            content_dict = json.loads(retrieve_msg.content)
            history = content_dict.get("historico_relevante")
            if history and isinstance(history, list): historical_context = "\n".join(history)
        except (json.JSONDecodeError, TypeError): pass

    final_prompt = f"{PROMPT_SYNTHESIZER}\n\n## Histórico e Evidências\n\nContexto Histórico:\n{historical_context}\n\nEvidências:\n{tool_result_content}"
    logger.info("A chamar o LLM para a síntese final (deep-dive)...")
    response = await synthesizer_llm.ainvoke(final_prompt)
    summary = response.content
    logger.info(f"--- SAÍDA (synthesize): Resumo gerado (primeiros 100 chars): {summary[:100].replace(chr(10), ' ')}...")
    return {"final_summary": summary}

def save_node(state: AgentState):
    logger.info("--- NÓ: save ---")
    summary_to_save = state.get("final_summary")
    if summary_to_save and "INDETERMINADA" not in summary_to_save:
        summary_obj = _extract_json_from_string(summary_to_save)
        if summary_obj:
            tool_call = {"name": "save_analysis_summary", "args": {"index": state['tool_params']['index'], "summary": json.dumps(summary_obj)}, "id": str(uuid.uuid4())}
            logger.info("--- SAÍDA (save): A preparar chamada para a ferramenta 'save_analysis_summary'")
            return {"messages": state["messages"] + [AIMessage(content="", tool_calls=[tool_call])]}
    logger.info("--- SAÍDA (save): Nenhum resumo para guardar. A saltar.")
    return {}

def conditional_router(state: AgentState) -> Literal["plan", "synthesize", "__end__"]:
    logger.info("--- NÓ: conditional_router ---")
    last_message = state["messages"][-1] if state.get("messages") else None
    if isinstance(last_message, ToolMessage):
        if last_message.name == "retrieve_historical_context":
            logger.info("--- Router: Histórico recuperado. A ir para o planeamento.")
            return "plan"
        if last_message.name == "search_logs":
            logger.info("--- Router: Logs de busca obtidos. A ir para a síntese.")
            return "synthesize"
        if last_message.name == "save_analysis_summary":
            logger.info("--- Router: Resumo guardado. A terminar o fluxo.")
            return "__end__"
    logger.warning(f"--- Router: Condição inesperada. A terminar. Última mensagem: {type(last_message).__name__}")
    return "__end__"

_tool_node: Optional[ToolNode] = None; _initial_graph = None; _deep_dive_graph = None; memory = MemorySaver()

def _build_initial_graph(tool_node: ToolNode):
    gb = StateGraph(AgentState)
    gb.add_node("act", act_initial_node)
    gb.add_node("tools", tool_node)
    gb.add_node("aggregate", aggregate_logs_node)
    gb.add_node("synthesize", synthesize_initial_node)
    gb.add_edge(START, "act"); gb.add_edge("act", "tools"); gb.add_edge("tools", "aggregate"); gb.add_edge("aggregate", "synthesize"); gb.add_edge("synthesize", END)
    return gb.compile(checkpointer=memory)

def _build_deep_graph(tool_node: ToolNode):
    gb = StateGraph(AgentState)
    gb.add_node("retrieve", retrieve_node); gb.add_node("plan", planner_node)
    gb.add_node("synthesize", synthesize_deep_node); gb.add_node("save", save_node)
    gb.add_node("tools", tool_node)
    gb.add_edge(START, "retrieve"); gb.add_edge("retrieve", "tools")
    gb.add_conditional_edges("tools", conditional_router, {"plan": "plan", "synthesize": "synthesize", "__end__": END})
    gb.add_edge("plan", "tools"); gb.add_edge("synthesize", "save"); gb.add_edge("save", "tools")
    return gb.compile(checkpointer=memory)

async def ensure_graphs():
    global _tool_node, _initial_graph, _deep_dive_graph
    if _tool_node is None:
        _tool_node = ToolNode(await init_tools())
    if _initial_graph is None:
        _initial_graph = _build_initial_graph(_tool_node)
    if _deep_dive_graph is None:
        _deep_dive_graph = _build_deep_graph(_tool_node)

async def run_initial_analysis(user_input: str, session_id: str, tool_params: dict) -> Dict[str, Any]:
    await ensure_graphs()
    config = {"configurable": {"thread_id": session_id}}
    inputs = {"messages": [HumanMessage(content=user_input)], "tool_params": tool_params}
    final_state = await _initial_graph.ainvoke(inputs, config)
    answer_content = final_state["messages"][-1].content if final_state and final_state.get("messages") else "{}"
    tool_message = _extract_latest_tool_message_by_name(final_state["messages"], "search_logs")
    evidence_overview = json.loads(tool_message.content) if tool_message and tool_message.content else {}
    parsed_answer = _extract_json_from_string(answer_content) or {"error": "A resposta da análise inicial não era um JSON válido."}
    response = {"answer": parsed_answer, "evidence_overview": evidence_overview, "session_id": session_id}
    logger.info(f"--- RESPOSTA FINAL (initial-analysis): {str(response)[:200]}...")
    return response

async def run_deep_dive_analysis(user_input: str, session_id: str, tool_params: dict) -> Dict[str, Any]:
    await ensure_graphs()
    config = {"configurable": {"thread_id": session_id}}
    current_state = _deep_dive_graph.get_state(config)
    messages = current_state.values.get('messages', []) if current_state else []
    if not any(isinstance(m, HumanMessage) for m in messages):
         messages.append(HumanMessage(content=user_input))
    inputs = {"messages": messages, "tool_params": tool_params}
    final_state = await _deep_dive_graph.ainvoke(inputs, config)
    answer_obj = _extract_json_from_string(final_state.get("final_summary", "{}")) or {"error": "Não foi possível gerar uma análise final."}
    tool_message = _extract_latest_tool_message_by_name(final_state.get("messages", []), "search_logs")
    evidence_overview = json.loads(tool_message.content) if tool_message and tool_message.content else {}
    response = {"answer": answer_obj, "evidence_overview": evidence_overview, "session_id": session_id}
    logger.info(f"--- RESPOSTA FINAL (deep-dive): {str(response)[:200]}...")
    return response

