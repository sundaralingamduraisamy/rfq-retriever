import operator
from typing import Annotated, List, TypedDict, Union


from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from langgraph.graph import StateGraph, END

from settings import settings

# ------------------------------------------------------------------
# 1. Setup LLM
# ------------------------------------------------------------------
from core.llm_provider import llm
from core.prompt_loader import load_prompt

# ------------------------------------------------------------------
# 2. Define State
# ------------------------------------------------------------------
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    intent: str

# ------------------------------------------------------------------
# 3. Define Prompts
# ------------------------------------------------------------------
SYSTEM_PROMPT_GENERAL = load_prompt("general_agent_system.md")
SYSTEM_PROMPT_DRAFTER = load_prompt("drafter_agent_system.md")

# ------------------------------------------------------------------
# 4. Define Nodes
# ------------------------------------------------------------------
def router_node(state: AgentState):
    """
    Simple heuristic router to decide intent.
    In a real agent, this could be an LLM call.
    """
    messages = state["messages"]
    last_msg = messages[-1].content.lower() if messages else ""
    
    triggers = [
        "apply", "update rfq", "generate final rfq", 
        "draft rfq", "final structured rfq", 
        "apply recommended changes", "update document"
    ]
    
    if any(t in last_msg for t in triggers):
        return {"intent": "draft"}
    return {"intent": "chat"}

def general_chat_node(state: AgentState):
    messages = state["messages"]
    # Prepend system prompt if not present (or we can just let the graph handle it dynamically)
    # For a simple chat, we just invoke the LLM
    
    # We want to force the system prompt behavior
    conversation = [SystemMessage(content=SYSTEM_PROMPT_GENERAL)] + messages
    response = llm.invoke(conversation)
    return {"messages": [response]}

def drafter_node(state: AgentState):
    messages = state["messages"]
    # For drafting, we might want to ignore history or use it as context. 
    # Usually drafting needs the specific instructions.
    
    # We will use the generic system prompt for drafting
    conversation = [SystemMessage(content=SYSTEM_PROMPT_DRAFTER)] + messages
    response = llm.invoke(conversation)
    return {"messages": [response]}

# ------------------------------------------------------------------
# 5. Build Graph
# ------------------------------------------------------------------
workflow = StateGraph(AgentState)

workflow.add_node("router", router_node)
workflow.add_node("general_chat", general_chat_node)
workflow.add_node("drafter", drafter_node)

workflow.set_entry_point("router")

def route_decision(state: AgentState):
    if state["intent"] == "draft":
        return "drafter"
    return "general_chat"

workflow.add_conditional_edges(
    "router",
    route_decision,
    {
        "drafter": "drafter",
        "general_chat": "general_chat"
    }
)

workflow.add_edge("general_chat", END)
workflow.add_edge("drafter", END)

app = workflow.compile()

# ------------------------------------------------------------------
# 6. Legacy Adapter
# ------------------------------------------------------------------
def normalize_role(role):
    if role == "agent":
        return "assistant"
    if role in ["assistant", "system", "user"]:
        return role
    return "user"

def chat_with_llm(messages: List[dict]):
    """
    Adapter function to maintain compatibility with main.py
    Input: List of dicts [{"role": "user", "content": "..."}]
    Output: String response
    """
    
    # Convert dict messages to LangChain messages
    langchain_messages = []
    custom_system_content_for_bypass = None
    
    for m in messages:
        role = normalize_role(m.get("role"))
        content = m.get("content") or m.get("text") or ""
        
        if role == "system":
            # Check if this is the main default prompt (which we want to ignore in favor of Graph prompts)
            if "STRICT RULES" in content and "Reference RFQ" not in content:
                continue
            
            # Check for bypass keywords (Validator, Impact Analysis, Direct Drafter)
            # These are specific "functions" called by main.py that shouldn't go through the conversational router
            lower_content = content.lower()
            if any(k in lower_content for k in ["validator", "impact analysis", "drafting agent"]):
                custom_system_content_for_bypass = content
                continue
            
            # If it's "Reference RFQ" or other context, we KEEP it as a system message
            langchain_messages.append(SystemMessage(content=content))
        
        elif role == "user":
            langchain_messages.append(HumanMessage(content=content))
        elif role == "assistant":
            langchain_messages.append(AIMessage(content=content))
            
    # If we detected a custom system (like validator), bypass the graph
    if custom_system_content_for_bypass:
        msgs = [SystemMessage(content=custom_system_content_for_bypass)] + langchain_messages
        # We invoke the LLM directly
        res = llm.invoke(msgs)
        return res.content

    # Otherwise, use the LangGraph Agent
    try:
        inputs = {"messages": langchain_messages}
        result = app.invoke(inputs)
        
        # Extract the last message
        last_message = result["messages"][-1]
        return last_message.content

    except Exception as e:
        print(f"Graph Error: {e}")
        # Fallback error message
        return "I'm having trouble connecting to the AI agent right now. Please check your connection or API key."
