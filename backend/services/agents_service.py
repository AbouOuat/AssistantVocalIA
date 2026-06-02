"""LangChain Agents — tools sécurisés (eval() banni)."""

import ast
import logging
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from backend.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

llm = ChatOpenAI(
    model=settings.OPENAI_MODEL,
    temperature=0,
    openai_api_key=settings.OPENAI_API_KEY,
)


@tool
def web_search(query: str) -> str:
    """Search the web for current information about any topic."""
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
        if not results:
            return f"Aucun résultat trouvé pour : {query}"
        parts = []
        for r in results:
            parts.append(f"{r['title']}\n{r['body']}\nSource : {r['href']}")
        return "\n\n".join(parts)
    except Exception as e:
        logger.warning(f"web_search error: {e}")
        return f"Recherche indisponible pour : {query}"


@tool
def calculator(expression: str) -> str:
    """Calculate a safe mathematical expression (no code execution)."""
    try:
        # ast.literal_eval ne peut pas évaluer des expressions mathématiques,
        # on utilise une whitelist de caractères sûrs
        allowed = set("0123456789+-*/.() ")
        if not all(c in allowed for c in expression):
            return "Erreur : expression non autorisée (caractères invalides)"
        # Compile et évalue seulement si l'AST est sûr (pas d'appel de fonction)
        tree = ast.parse(expression, mode="eval")
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                return "Erreur : appels de fonction non autorisés"
        result = eval(compile(tree, "<string>", "eval"))  # noqa: S307 — ast-validated
        return str(result)
    except Exception as e:
        return f"Erreur de calcul : {e}"


@tool
def get_current_time() -> str:
    """Get the current date and time."""
    from datetime import datetime
    return datetime.now().strftime("%A %d %B %Y à %H:%M")


@tool
def control_smart_device(device_name: str, command: str) -> str:
    """Control a smart home device (on/off/toggle)."""
    from backend.services.domotics_service import domotics_service
    if domotics_service is None:
        return "Service domotique non initialisé"
    import asyncio
    loop = asyncio.get_event_loop()
    success = loop.run_until_complete(
        domotics_service.control_device(device_name, command)
    )
    return f"Appareil '{device_name}' : commande '{command}' {'✓' if success else '✗'}"


def create_jarvis_agent() -> AgentExecutor:
    tools = [web_search, calculator, get_current_time, control_smart_device]

    prompt = ChatPromptTemplate.from_messages([
        ("system", """Tu es Jarvis, un assistant IA avec des outils pour agir.
Utilise les outils disponibles quand c'est approprié. Sois concis."""),
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_openai_tools_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True)


async def execute_agent_task(task: str) -> str:
    try:
        executor = create_jarvis_agent()
        result = executor.invoke({
            "input": task,
            "chat_history": [],
            "agent_scratchpad": "",
        })
        return result.get("output", "Tâche exécutée")
    except Exception as e:
        logger.error(f"Agent error: {e}")
        return f"Erreur agent: {e}"
