from typing import List, Dict, Optional, Tuple
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
import traceback

# Import existing singletons/config
from settings import settings
from database import db
from core.llm_provider import llm
from core.retriever import hybrid_search
from core.prompt_loader import load_prompt

def clean_text(text: str) -> str:
    """Helper to remove markdown code blocks"""
    return text.replace("```markdown", "").replace("```", "").strip()

class ChatAgent:
    """
    Simple agentic RAG without langchain.agents dependency
    """

    def __init__(self):
        self.tools = self._define_tools()
        # Context for the current turn
        self.current_draft_context: Optional[str] = None
        self.pending_update: Optional[Dict] = None

    def _define_tools(self):
        """Define available tools"""
        return {
            "search_documents": self._search_documents,
            "list_all_documents": self._list_all_documents,
            "get_full_summary": self._get_full_summary,
            "update_rfq_draft": self._update_rfq_draft,
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
            return f"Complete summary for {filename}:\n{row[0]}", [{"file": filename, "score": 100, "preview": "Full Document Accessed"}]
        return "Summary not found.", []

    def _update_rfq_draft(self, instructions: str):
        """
        Update the current RFQ draft based on specific user instructions.
        Uses the 'current_draft_context' stored in the agent.
        """
        print(f"\n   🔧 Tool: update_rfq_draft('{instructions}')")
        
        if not self.current_draft_context:
            return "Error: No active draft found. Ask the user to start a draft first or provide content.", []

        try:
            # 1. Apply Edit
            edit_prompt = load_prompt("edit_rfq_user.md", 
                                      instruction=instructions, 
                                      current_text=self.current_draft_context)
            
            # Helper for sub-calls
            def sub_invoke(sys_file, user_text):
                msgs = [
                    SystemMessage(content=load_prompt(sys_file)),
                    HumanMessage(content=user_text)
                ]
                return llm.invoke(msgs).content

            updated_text = sub_invoke("edit_rfq_system.md", edit_prompt)
            updated_text = clean_text(updated_text)
            
            # 2. Analyze Impact
            analysis_prompt = load_prompt("analyze_changes_user.md", 
                                          old_text=self.current_draft_context, 
                                          new_text=updated_text)
            
            analysis = sub_invoke("impact_analysis_system.md", analysis_prompt)
            
            # Store result to be returned by process()
            self.pending_update = {
                "updated_text": updated_text,
                "analysis": analysis
            }
            
            return f"Draft updated successfully based on: {instructions}. Impact analysis generated.", []

        except Exception as e:
            traceback.print_exc()
            return f"Failed to update draft: {str(e)}", []


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

    def process(self, messages: List[dict], current_draft: str = None, mode: str = "agent") -> Tuple[str, List, Dict]:
        """
        Process messages with native tool-calling logic.
        :param current_draft: The text of the currently open draft (if any)
        :param mode: 'agent' or 'manual'. If 'manual', disable update tool.
        :return: (response_text, found_documents, update_payload)
        """
        
        # Reset state for this turn
        self.current_draft_context = current_draft
        self.pending_update = None
        
        # Define Pydantic/OpenAI-style tool schemas
        tools_schema = [
            {
                "type": "function",
                "function": {
                    "name": "search_documents",
                    "description": "Search for documents (Knowledge Base). Use for research or finding info.",
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
        
        # Only enable Edit Tool in AGENT mode and if there is a draft
        if mode == "agent" and current_draft:
            tools_schema.append({
                "type": "function",
                "function": {
                    "name": "update_rfq_draft",
                    "description": "Update/Edit the current RFQ draft text based on instructions. Use this when the user asks to change, add, or remove content in the draft.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "instructions": {
                                "type": "string", 
                                "description": "Precise instructions for the edit (e.g. 'Add a section on Lithium Batteries')"
                            }
                        },
                        "required": ["instructions"]
                    }
                }
            })
        
        # Build context
        context_messages = []
        found_documents = []
        
        # System prompt
        base_prompt = """You are an intelligent RFQ Assistant.
1. **Search**: Use `search_documents` to find info.
2. **Context**: You can see the current draft if provided.
"""
        if mode == "agent" and current_draft:
            base_prompt += """3. **Editing**: You have the power to EDIT the draft using `update_rfq_draft`. 
   - If the user asks to change the text, USE THE TOOL.
   - Do NOT just say "I can do that", actually DO IT."""
   
        context_messages.append(SystemMessage(content=base_prompt))
        
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
                        
                        if tool_name == "search_documents":
                            tool_result_text, tool_docs = self._search_documents(args.get("query", ""))
                        elif tool_name == "get_full_summary":
                            tool_result_text, tool_docs = self._get_full_summary(args.get("filename", ""))
                        elif tool_name == "list_all_documents":
                            tool_result_text, tool_docs = self._list_all_documents()
                        elif tool_name == "update_rfq_draft":
                             # This tool modifies internal state (pending_update)
                            tool_result_text, tool_docs = self._update_rfq_draft(args.get("instructions", ""))
                        
                        # Collect docs
                        found_documents.extend(tool_docs)
                        
                        # Append tool output message
                        context_messages.append(ToolMessage(
                            content=tool_result_text,
                            tool_call_id=tool_call_id
                        ))
                    
                    # Continue loop to let LLM generate response based on tool output
                    continue
                
                # No tool call -> Final Response
                response_text = response.content
                print(f"✅ Final Response. Found docs: {len(found_documents)}")
                return response_text, found_documents, self.pending_update
                
            except Exception as e:
                print(f"❌ Agent Error: {e}")
                # Fallback: if tool binding fails, just try raw LLM one last time
                if iteration == 0:
                     try:
                        return llm.invoke(context_messages).content, [], None
                     except:
                        pass
                return "I apologize, but I encountered an error. Please try again.", [], None
        
        return "I found some information but need more specific guidance.", found_documents, self.pending_update


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
