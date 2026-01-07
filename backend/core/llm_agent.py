from typing import List, Dict
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

# Import existing singletons/config
from settings import settings
from database import db
from core.llm_provider import llm
from core.retriever import hybrid_search


class ChatAgent:
    """
    Simple agentic RAG without langchain.agents dependency
    """

    def __init__(self):
        self.tools = self._define_tools()

    def _define_tools(self):
        """Define available tools"""
        return {
            "search_documents": self._search_documents,
            "list_all_documents": self._list_all_documents,
            "get_full_summary": self._get_full_summary,
        }

    def _search_documents(self, query: str):
        """Search indexed documents using vector similarity"""
        print(f"\n   🔧 Tool: search_documents('{query}')")
        results = hybrid_search(query)

        if not results:
            return "No matching documents found.", []

        summary = f"Found {len(results)} relevant documents:\n\n"
        found_docs = []
        
        for i, item in enumerate(results, 1):
            src = item["source"]
            preview = item["text"][:200].replace("\n", " ")
            summary += f"{i}. [{src['file']}] (Relevance: {item['relevance']}%)\n"
            summary += f"   Preview: {preview}...\n"
            summary += f"   Full Summary: {item['text']}\n\n"
            
            # Add to found list
            found_docs.append({
                "file": src["file"],
                "score": item["relevance"],
                "preview": preview
            })

        return summary, found_docs

    def _get_full_summary(self, filename: str):
        """Get the complete summary text of a document by filename"""
        row = db.execute_query_single(
            """
            SELECT ds.summary_text 
            FROM document_summaries ds
            JOIN documents d ON ds.document_id = d.id
            WHERE d.filename = %s
            """,
            (filename,)
        )
        if row:
            return f"Complete summary for {filename}:\n{row[0]}", []
        return "Summary not found.", []

    def _list_all_documents(self, _: str = ""):
        """List all indexed documents in the database"""
        results = db.execute_query(
            """
            SELECT d.filename, ds.word_count
            FROM document_summaries ds
            JOIN documents d ON ds.document_id = d.id
            ORDER BY d.filename
            """
        )
        if not results:
            return "No documents indexed.", []

        formatted = "📚 Indexed Documents:\n\n"
        # We don't necessarily treat listing as "finding" for the UI panel, 
        # but we could. For now let's just return text.
        for filename, word_count in results:
            formatted += f"📄 {filename} ({word_count} summary words)\n"
        return formatted, []

    def process(self, messages: List[dict]):
        """Process messages with native tool-calling logic"""
        
        # Define Pydantic/OpenAI-style tool schemas
        tools_schema = [
            {
                "type": "function",
                "function": {
                    "name": "search_documents",
                    "description": "Search for documents based on a query string",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_all_documents",
                    "description": "List all available documents in the system",
                    "parameters": {"type": "object", "properties": {}, "required": []}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_full_summary",
                    "description": "Get the complete text/summary of a specific document",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filename": {"type": "string", "description": "The exact filename of the document"}
                        },
                        "required": ["filename"]
                    }
                }
            }
        ]
        
        # Build context
        context_messages = []
        found_documents = []
        
        # System prompt - Removed strict formatting instructions
        system_prompt = """You are an intelligent RFQ Assistant. You help users find and understand documents.

IMPORTANT:
1. **For greetings** (hi, etc.): Just answer warmly.
2. **For technical queries**: CALL THE `search_documents` TOOL IMMEDIATELY.
   - Do NOT ask clarifying questions if you can search first.
   - Search for the key technical terms.
3. Use the tools provided to find information."""

        context_messages.append(SystemMessage(content=system_prompt))
        
        # Add history
        for m in messages[:-1]:
            role = m.get("role")
            content = m.get("content") or ""
            if role == "user":
                context_messages.append(HumanMessage(content=content))
            elif role == "assistant" or role == "agent":
                context_messages.append(AIMessage(content=content))
        
        # Add current query
        user_query = messages[-1].get("content") or ""
        context_messages.append(HumanMessage(content=user_query))
        
        # Bind tools to LLM
        # This tells the API "I support these tools" so valid tool format acts as a tool call, not an error
        llm_with_tools = llm.bind_tools(tools_schema)

        # Process with loop (max 3 tool calls)
        for iteration in range(3):
            try:
                # Invoke with tools bound
                response = llm_with_tools.invoke(context_messages)
                
                # Check for tool calls
                if response.tool_calls:
                    print(f"🛠️ Tool Call Detected (Iter {iteration}): {response.tool_calls}")
                    
                    # Append assistant's tool call message
                    context_messages.append(response)
                    
                    # Execute each tool call
                    for tool_call in response.tool_calls:
                        tool_name = tool_call["name"]
                        args = tool_call["args"]
                        tool_call_id = tool_call["id"]
                        
                        tool_result_text = "Error: Tool not found"
                        tool_docs = []
                        
                        if tool_name in self.tools:
                            # Map args correctly
                            if tool_name == "search_documents":
                                tool_result_text, tool_docs = self._search_documents(args.get("query", ""))
                            elif tool_name == "get_full_summary":
                                tool_result_text, tool_docs = self._get_full_summary(args.get("filename", ""))
                            elif tool_name == "list_all_documents":
                                tool_result_text, tool_docs = self._list_all_documents()
                        
                        # Collect docs
                        found_documents.extend(tool_docs)
                        
                        # Append tool output message (Standard LangChain format)
                        # Note: We append a generic ToolMessage or HumanMessage representing the tool output
                        from langchain_core.messages import ToolMessage
                        context_messages.append(ToolMessage(
                            content=tool_result_text,
                            tool_call_id=tool_call_id
                        ))
                    
                    # Continue loop to let LLM generate response based on tool output
                    continue
                
                # No tool call -> Final Response
                response_text = response.content
                print(f"✅ Final Response. Found docs: {len(found_documents)}")
                return response_text, found_documents
                
            except Exception as e:
                print(f"❌ Agent Error: {e}")
                # Fallback: if tool binding fails, just try raw LLM one last time
                if iteration == 0:
                     try:
                        return llm.invoke(context_messages).content, []
                     except:
                        pass
                return "I apologize, but I encountered an error. Please try again.", []
        
        return "I found some information but need more specific guidance.", found_documents


# Singleton
agent = ChatAgent()


# ----------------------------------------------------------------
# ADAPTER (For compatibility with main.py)
# ----------------------------------------------------------------
def chat_with_llm(messages: List[dict]) -> str:
    """
    Adapter function that routes calls to the new Agent.
    """
    # Check for direct bypass (Validator/Impact Analysis)
    if len(messages) > 0:
        system_msg = next((m for m in messages if m.get("role") == "system"), None)
        
        if system_msg:
            sys_content = system_msg.get("content", "")
            # Heuristic: If it's the validator or drafter, bypass Agent
            if "IDENTITY:" in sys_content or "Impact Analysis" in sys_content:
                # Direct invoke
                lang_msgs = []
                for m in messages:
                    role = m.get("role")
                    content = m.get("content", "")
                    if role == "system":
                        lang_msgs.append(SystemMessage(content=content))
                    elif role == "user":
                        lang_msgs.append(HumanMessage(content=content))
                    elif role == "assistant":
                        lang_msgs.append(AIMessage(content=content))
                
                return llm.invoke(lang_msgs).content

    return agent.process(messages)
