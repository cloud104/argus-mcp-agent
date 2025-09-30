import json
from pathlib import Path
from typing import List, TypedDict, Optional, Dict, Any
import logging
import uuid
import re

from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, ToolMessage
from langchain_community.cache import InMemoryCache
from langchain.globals import set_llm_cache
from langchain_core.prompts import ChatPromptTemplate

from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode, tools_condition

from app.agent.client import get_mcp_client
from app.agent.llm_provider import get_llm

# Configuração do Logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Config & Prompts
set_llm_cache(InMemoryCache())
BASE = Path(__file__).parent.parent.parent
PROMPT_SYNTHESIZER_V2 = (BASE / "prompts/synthesize_analysis_v2.md").read_text(encoding="utf-8")
PROMPT_EXPLAIN_LOG = (BASE / "prompts/explain_log_line.md").read_text(encoding="utf-8")
PROMPT_CHAT_PLANNER = (BASE / "prompts/chat_planner.md").read_text(encoding="utf-8")


# Modelos
synthesizer_llm = get_llm("synthesizer_model")
explanation_llm = get_llm("planner_model") 
chat_planner_llm = get_llm("chat_model")

# Cliente MCP
mcp_client = get_mcp_client()

# Cache de Ferramentas
_TOOLS: Optional[List[Any]] = None
_tool_node: Optional[ToolNode] = None
_initial_graph = None
_deep_dive_graph = None
_chat_graph = None


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
    # Regex to find JSON object within a string that might contain other text
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if not match:
        logger.warning("Nenhum JSON encontrado na string.")
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        logger.warning(f"Falha ao analisar a resposta do LLM como JSON: {text}")
        return None

class AgentState(TypedDict):
    messages: List[BaseMessage]
    tool_params: dict
    final_summary: str

# --- WORKFLOW 1: Análise Inicial (Apenas busca de logs) ---
def act_initial_node(state: AgentState):
    logger.info("--- NÓ (Inicial): act ---")
    # Garante que apenas os parâmetros corretos são passados para a ferramenta
    tool_args = {k: v for k, v in state["tool_params"].items() if k in ["index", "window"]}
    tool_call = {"name": "search_logs", "args": tool_args, "id": str(uuid.uuid4())}
    response = AIMessage(content="", tool_calls=[tool_call])
    logger.info(f"--- SAÍDA (act): A preparar chamada para a ferramenta 'search_logs' com os parâmetros: {tool_args}")
    return {"messages": state["messages"] + [response]}

# --- WORKFLOW 2: Análise Profunda ---
async def synthesize_deep_node(state: AgentState):
    logger.info("--- NÓ: synthesize_deep ---")
    tool_params = state.get("tool_params", {})
    logs_to_analyze = tool_params.get("logs", []) 
    
    if not logs_to_analyze:
        return {"final_summary": json.dumps({"resumo_analitico": "Nenhum log fornecido para análise.", "hipotese_causa_raiz": "N/A", "acoes_recomendadas": []})}

    # Reintroduzido para corresponder ao prompt
    entities = {
        "users": list(set(re.findall(r'user (\w+)', json.dumps(logs_to_analyze, ensure_ascii=False), re.IGNORECASE))),
        "threads": list(set(re.findall(r'Thread (\d+)', json.dumps(logs_to_analyze, ensure_ascii=False)))),
        "clients": list(set(re.findall(r'client ([\d\.]+:\d+)', json.dumps(logs_to_analyze, ensure_ascii=False))))
    }
    
    prompt_template = PROMPT_SYNTHESIZER_V2
    final_prompt = prompt_template.format(
        log_data=json.dumps(logs_to_analyze, indent=2, ensure_ascii=False),
        entities_data=json.dumps(entities, indent=2, ensure_ascii=False) # Passa o dicionário de entidades
    )
    
    logger.info("A chamar o LLM para a síntese final (deep-dive)...")
    response = await synthesizer_llm.ainvoke(final_prompt)
    summary = response.content
    logger.info(f"--- SAÍDA (synthesize_deep): Resumo gerado: {summary[:150]}...")
    
    parsed_summary = _extract_json_from_string(summary)
    
    return {"final_summary": json.dumps(parsed_summary)}

# --- WORKFLOW 3: Explicação de Linha de Log ---
async def run_log_explanation(log_message: str) -> Dict[str, str]:
    logger.info(f"Gerando explicação para o log: {log_message}")
    prompt = PROMPT_EXPLAIN_LOG.format(log_line=log_message)
    try:
        response = await explanation_llm.ainvoke(prompt)
        explanation = response.content.strip()
        return {"explanation": explanation}
    except Exception as e:
        logger.error(f"Erro ao gerar explicação do log: {e}")
        return {"explanation": "Não foi possível analisar este log no momento."}

# --- WORKFLOW 4: Chat Conversacional ---
async def chat_planner_node(state: AgentState):
    logger.info("--- NÓ (Chat): planner ---")
    prompt = ChatPromptTemplate.from_template(PROMPT_CHAT_PLANNER)

    # 👇 ESTA é a peça que faltava
    llm = chat_planner_llm.bind_tools(_TOOLS)  # opcional: tool_choice="auto"

    chain = prompt | llm
    response = await chain.ainvoke({
        "chat_history": state["messages"],
        "input": state["messages"][-1].content
    })
    logger.info(f"--- SAÍDA (planner): {response.content[:150]}...")
    return {"messages": state["messages"] + [response]}


# --- GRAPH CONSTRUCTION ---
memory = MemorySaver()
_tool_node: Optional[ToolNode] = None
_initial_graph = None
_deep_dive_graph = None
_chat_graph = None

def _build_graphs():
    global _tool_node, _initial_graph, _deep_dive_graph, _chat_graph
    _tool_node = ToolNode(_TOOLS)

    initial_builder = StateGraph(AgentState)
    initial_builder.add_node("act", act_initial_node)
    initial_builder.add_node("tools", _tool_node)
    initial_builder.add_edge(START, "act")
    initial_builder.add_edge("act", "tools")
    initial_builder.add_edge("tools", END)
    _initial_graph = initial_builder.compile(checkpointer=memory)

    deep_dive_builder = StateGraph(AgentState)
    deep_dive_builder.add_node("synthesize_deep", synthesize_deep_node)
    deep_dive_builder.add_edge(START, "synthesize_deep")
    deep_dive_builder.add_edge("synthesize_deep", END)
    _deep_dive_graph = deep_dive_builder.compile(checkpointer=memory)

    # Grafo de Chat
    chat_builder = StateGraph(AgentState)
    chat_builder.add_node("planner", chat_planner_node)
    chat_builder.add_node("tools", _tool_node)
    chat_builder.add_edge(START, "planner")
    chat_builder.add_conditional_edges("planner", tools_condition)
    chat_builder.add_edge("tools", "planner")
    _chat_graph = chat_builder.compile(checkpointer=memory)


async def ensure_graphs():
    global _TOOLS
    if _TOOLS is None:
        await init_tools()
        _build_graphs()

# --- MAIN EXECUTION FUNCTIONS ---
async def run_initial_analysis(user_input: str, session_id: str, tool_params: dict) -> Dict[str, Any]:
    await ensure_graphs()
    config = {"configurable": {"thread_id": session_id}}
    inputs = {"messages": [HumanMessage(content=user_input)], "tool_params": tool_params}
    
    final_state = await _initial_graph.ainvoke(inputs, config)
    
    tool_message = _extract_latest_tool_message_by_name(final_state["messages"], "search_logs")
    evidence_overview = {"logs_encontrados": []}
    if tool_message and tool_message.content:
        try:
            # Garante que o content é um JSON antes de fazer o parse
            content_data = json.loads(tool_message.content)
            evidence_overview = content_data if isinstance(content_data, dict) else {"logs_encontrados": []}
        except (json.JSONDecodeError, TypeError):
            logger.warning(f"A ferramenta search_logs retornou um não-JSON: {tool_message.content}")

    response = {"answer": {}, "evidence_overview": evidence_overview, "session_id": session_id}
    logger.info(f"--- RESPOSTA FINAL (initial-analysis): {len(evidence_overview.get('logs_encontrados',[]))} logs encontrados.")
    return response

async def run_deep_dive_analysis(user_input: str, session_id: str, tool_params: dict) -> Dict[str, Any]:
    await ensure_graphs()
    config = {"configurable": {"thread_id": session_id}}
    inputs = {"messages": [HumanMessage(content=user_input)], "tool_params": tool_params}
    
    final_state = await _deep_dive_graph.ainvoke(inputs, config)
    
    summary_content = final_state.get("final_summary", "{}")
    parsed_summary = _extract_json_from_string(summary_content)
    
    if not parsed_summary:
        parsed_summary = {"resumo_analitico": "Ocorreu um erro ao gerar a análise profunda."}

    response = {"answer": parsed_summary, "session_id": session_id}
    logger.info(f"--- RESPOSTA FINAL (deep-dive): {str(response)[:200]}...")
    return response

async def run_chat_turn(user_input: str, session_id: str, initial_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    await ensure_graphs()
    config = {"configurable": {"thread_id": session_id}}
    
    messages = []
    # Se for a primeira mensagem, injeta o contexto da análise e dos logs
    if initial_context and isinstance(initial_context, dict):
        analysis_summary = json.dumps(initial_context.get("analysis", {}), indent=2, ensure_ascii=False)
        logs_sample = json.dumps(initial_context.get("logs", [])[:], indent=2, ensure_ascii=False) # 5 logs de amostra
        
        context_message = (
            f"**Contexto da Análise Fornecido:**\n\n"
            f"**1. Resumo da Análise (Deep Dive):**\n```json\n{analysis_summary}\n```\n\n"
            f"**2. Amostra de Logs Analisados:**\n```json\n{logs_sample}\n```\n\n"
            f"---"
        )
        messages.append(AIMessage(content=context_message))
    else:
        # Para turnos subsequentes, recupera o histórico
        current_state = await _chat_graph.aget_state(config)
        messages = current_state.values.get("messages", [])

    # Adiciona a pergunta atual do utilizador
    inputs = {"messages": messages + [HumanMessage(content=user_input)]}
    
    final_state = await _chat_graph.ainvoke(inputs, config)
    
    ai_message = next((msg for msg in reversed(final_state['messages']) if isinstance(msg, AIMessage) and not msg.tool_calls), None)
    
    return {"answer": ai_message.content if ai_message else "Não foi possível processar a sua pergunta.", "session_id": session_id}

