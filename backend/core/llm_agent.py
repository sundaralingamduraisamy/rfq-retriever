from typing import List, Dict, Optional, Tuple
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
import traceback
import re
import json

# Import existing singletons/config
from settings import settings
from database import db
from core.llm_provider import llm
from core.retriever import hybrid_search, search_images
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
            "search_images": self._search_images,
        }

    def _search_documents(self, query: str):
        """Search indexed documents using vector similarity"""
        # print(f"\n   🔧 Tool: search_documents('{query}')")
        results = hybrid_search(query)

        if not results:
            return "No matching documents found.", []

        # Deduplicate by filename, keeping highest relevance score
        seen_files = {}
        for item in results:
            filename = item["source"]["file"]
            relevance = item["relevance"]
            
            if filename not in seen_files or relevance > seen_files[filename]["relevance"]:
                seen_files[filename] = item
        
        # Convert back to list and sort by relevance
        results = sorted(seen_files.values(), key=lambda x: x["relevance"], reverse=True)
        
        # Limit to top 3 results to reduce tokens
        results = results[:3]

        summary = f"Found {len(results)} relevant documents:\n\n"
        found_docs = []
        
        for i, item in enumerate(results, 1):
            src = item["source"]
            # Truncate text to reduce token usage
            full_text = item["text"]
            truncated_text = full_text[:500] + "..." if len(full_text) > 500 else full_text
            preview = truncated_text[:200].replace("\n", " ")
            
            summary += f"{i}. [{src['file']}] (Relevance: {item['relevance']}%)\n"
            summary += f"   TECHNICAL DATA: {truncated_text}\n\n"
            
            # Add to found list
            found_docs.append({
                "file": src["file"],
                "score": item["relevance"],
                "preview": preview,
                "full_text": truncated_text  # Truncated to save tokens
            })

        return summary, found_docs

    def _search_images(self, query: str):
        """Search for relevant past automotive images using vector similarity"""
        # print(f"\n   🔧 Tool: search_images('{query}')")
        images = search_images(query)
        
        # SLICE TO MAXIMUM OF 3 IMAGES
        if images:
            images = images[:3]
        
        if not images:
            return "No relevant automobile images found.", []
            
        summary = f"Found {len(images)} relevant images:\n\n"
        found_imgs = []
        for i, img in enumerate(images, 1):
            summary += f"{i}. [ID: {img['id']}] Description: {img['description']} (from {img['file']}) (Score: {img['relevance']}%)\n"
            found_imgs.append({
                "file": img['file'],
                "image_id": img['id'],
                "description": img['description'],
                "text": f"IMAGE INFO: [ID: {img['id']}] Description: {img['description']}"
            })
            
        summary += "\nCRITICAL: If these images are relevant, you MUST include them using [[IMAGE_ID:n]] in Section 1 or 2 of the RFQ draft."
        return summary, found_imgs

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
            full_summary = row[0]
            # Truncate to 800 chars to avoid token limits
            truncated = full_summary[:800] + "..." if len(full_summary) > 800 else full_summary
            return f"Summary for {filename}:\n{truncated}", [{"file": filename, "score": 100, "preview": "Full Document Accessed", "full_text": truncated}]
        return "Summary not found.", []

    def _extract_previous_images(self, messages: List[Dict]) -> List[Dict]:
        """Scans assistant messages for image IDs and descriptions AND verifies they still exist in DB"""
        found = []
        # Pattern like: 1. [ID: 67] Description: brake schematic (from...)
        pattern = r"\[ID: (\d+)\] Description: (.*?) \(from"
        
        # 1. Collect all candidate IDs mentioned in history
        candidate_ids = []
        for m in messages:
            if m.get("role") in ["assistant", "agent"] or m.get("role") == "assistant":
                content = m.get("content") or ""
                matches = re.finditer(pattern, content)
                for match in matches:
                    candidate_ids.append(match.group(1))
        
        if not candidate_ids:
            return []

        # 2. Verify existence in DB to prevent "memory leaks" from deleted files
        unique_ids = list(set(candidate_ids))
        placeholders = ','.join(['%s'] * len(unique_ids))
        try:
            db_rows = db.execute_query(
                f"SELECT id, description FROM document_images WHERE id IN ({placeholders})", 
                tuple(unique_ids)
            )
            valid_db_ids = {str(r[0]): r[1] for r in db_rows}
        except:
            valid_db_ids = {}

        # 3. Only re-populate context with images that still exist
        for m in messages:
            if m.get("role") in ["assistant", "agent"]:
                content = m.get("content") or ""
                matches = re.finditer(pattern, content)
                for match in matches:
                    img_id = match.group(1)
                    
                    if img_id in valid_db_ids:
                        # Deduplicate within recovery
                        if not any(f.get("image_id") == int(img_id) for f in found):
                            found.append({
                                "image_id": int(img_id),
                                "description": valid_db_ids[img_id],
                                "text": f"IMAGE INFO: [ID: {img_id}] Description: {valid_db_ids[img_id]}",
                                "file": "Previous Search"
                            })
        
        if candidate_ids and not found:
            print(f"🕵️ Recovery: All {len(candidate_ids)} images mentioned in history were purged from DB. Memory cleared.")
            
        return found

    def _update_rfq_draft(self, instructions: str, context_docs: List[Dict] = []):
        """
        Internal tool to update the draft editor.
        Update the current RFQ draft based on specific user instructions.
        Uses the 'current_draft_context' stored in the agent.
        """
        # print(f"\n   🔧 Tool: update_rfq_draft('{instructions}')")
        
        if self.current_draft_context is None:
            return "Error: No active draft found. Ask the user to start a draft first or provide content.", []

        try:
            # 1. Apply Edit
            # Deduplicate context documents and images before sending to LLM
            unique_context = []
            seen_ids = set()
            
            for d in context_docs:
                # Use filename+chunk_id for docs, image_id for images
                cid = d.get("image_id") or f"{d.get('file')}:{d.get('chunk_id')}"
                if cid not in seen_ids:
                    seen_ids.add(cid)
                    unique_context.append(d)
            
            context_parts = []
            for d in unique_context:
                filename = d.get("file") or (d.get("source", {}).get("file")) or "Unknown Source"
                text = d.get("full_text") or d.get("text") or d.get("preview") or ""
                image_id = d.get("image_id")
                
                if image_id:
                    context_parts.append(f"CRITICAL - ATTACHED IMAGE: [[IMAGE_ID:{image_id}]] - Description: {d.get('description', '')}")
                elif text:
                    context_parts.append(f"SOURCE: {filename}\n{text}")
            
            context_text = "\n\n".join(context_parts)
            
            edit_prompt = load_prompt("edit_rfq_user.md", 
                                      instruction=instructions, 
                                      current_text=self.current_draft_context,
                                      context_documents=context_text)
            
            # Helper for sub-calls
            def sub_invoke(sys_file, user_text):
                msgs = [
                    SystemMessage(content=load_prompt(sys_file)),
                    HumanMessage(content=user_text)
                ]
                return llm.invoke(msgs).content

            updated_text = sub_invoke("edit_rfq_system.md", edit_prompt)
            updated_text = clean_text(updated_text)
            
            # --- IMAGE DEDUPLICATION & HALLUCINATION GUARD ---
            # Extract valid image IDs from the context to verify the agent isn't inventing them
            valid_ids = [str(d.get("image_id")) for d in context_docs if d.get("image_id")]
            seen_in_draft = set()

            def image_guard_callback(match):
                mid = match.group(1)
                # Valid if: It's numeric AND it was provided in context AND it hasn't appeared yet
                if mid.isdigit() and mid in valid_ids and mid not in seen_in_draft:
                    seen_in_draft.add(mid)
                    return f"[[IMAGE_ID:{mid}]]"
                
                # Otherwise, it's a hallucination or a duplicate - REMOVE IT
                # print(f"⚠️ Image Guard: Removing tag [[IMAGE_ID:{mid}]] (Reason: {'Duplicate' if mid in seen_in_draft else 'Invalid/Hallucinated'})")
                return ""

            # Apply the guard to the entire updated text
            updated_text = re.sub(r"\[\[IMAGE_ID:([^\]]+)\]\]", image_guard_callback, updated_text)
            
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
            
            return f"TECHNICAL UPDATE SUCCESSFUL: Applied instructions: {instructions}. Impact analysis is ready for review.", []

        except Exception as e:
            traceback.print_exc()
            return f"Failed to update draft: {str(e)}", []


    def _rescue_tool_calls(self, text: str, iteration: int) -> List[Dict]:
        """Rescue hallucinated tool calls from raw text when native calling fails."""
        tool_calls = []
        # Pattern 1: <function=name{"arg": "val"}></function>
        # Pattern 2: function=name{"arg": "val"}
        # Pattern 3: name(query="vals") 
        # Pattern 4: name query="vals"
        
        patterns = [
            r"function=(\w+)\s*(\{.*?\})",                         # function=name{...}
            r"<function=(\w+)\s*(\{.*?\}).*?</function>",          # <function=name{...}></function>
            r"(\w+)\((.*?)\)",                                     # name(args)
            r"(\w+)\s+query=[\"'](.*?)[\"']",                      # name query="..."
            r"(\w+)\s+instructions=[\"'](.*?)[\"']",               # name instructions="..."
            r"(\w+)\s+insstructions=[\"'](.*?)[\"']",              # name insstructions="..." (typo fix)
            r"(\w+)\s+filename=[\"'](.*?)[\"']"                    # name filename="..."
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.DOTALL):
                name = match.group(1)
                raw_args = match.group(2)
                
                # Check if name is real
                if name not in self.tools:
                    continue
                    
                args = {}
                try:
                    # Try JSON first
                    args = json.loads(raw_args)
                except:
                    # Fallback for name(query="...") style
                    # Extract key="val" pairs
                    arg_matches = re.findall(r"(\w+)=[\"'](.*?)[\"']", raw_args)
                    if arg_matches:
                        args = {k: v for k, v in arg_matches}
                        # Map typo
                        if "insstructions" in args:
                            args["instructions"] = args.pop("insstructions")
                    elif len(raw_args.strip()) > 0 and len(arg_matches) == 0:
                        # Single positional-ish arg
                        if name == "search_documents" or name == "search_images":
                            args = {"query": raw_args.strip().strip('"').strip("'")}
                        elif name == "update_rfq_draft":
                            args = {"instructions": raw_args.strip().strip('"').strip("'")}
                        elif name == "get_full_summary":
                            args = {"filename": raw_args.strip().strip('"').strip("'")}

                if name and (args or name == "list_all_documents"):
                    tool_calls.append({"name": name, "args": args, "id": f"rescue_{iteration}_{len(tool_calls)}"})
        
        return tool_calls

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
                    "description": "Find technical information in manuals.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search term"}
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
                            "filename": {
                                "type": "string", 
                                "description": "The EXACT filename of the document as shown in the file list (e.g., 'manual_v1.pdf')."
                            }
                        },
                        "required": ["filename"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_images",
                    "description": "Find technical diagrams of car parts.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Part name (e.g. 'brake')"}
                        },
                        "required": ["query"]
                    }
                }
            }
        ]
        
        # Only enable Edit Tool in AGENT mode and if there is a draft
        if mode == "agent" and current_draft is not None:
            tools_schema.append({
                "type": "function",
                "function": {
                    "name": "update_rfq_draft",
                    "description": "CRITICAL: ONLY use this tool if you have high-quality technical specs. DO NOT use for generic drafts or nonsense inputs unless the user explicitly said 'Proceed with generic'.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "instructions": {
                                "type": "string", 
                                "description": "Detailed instructions for the current edit (e.g. 'Add a technical section on battery safety using info from source X')."
                            }
                        },
                        "required": ["instructions"]
                    }
                }
            })
        
        # Build context
        context_messages = []
        
        # 0. Recover previous context images from history to prevent "lost images" during editing
        # This ensures the drafter sub-agent always has the required Metadata for IDs mentioned in history
        found_documents = self._extract_previous_images(messages)
        
        response_text = "I analyzed the context but couldn't finalize a response after several attempts. Please try again."
        
        # System prompt
        base_prompt = load_prompt("chat_system_prompt.md")
   
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
                # 0. Invoke with tools bound
                response = llm_with_tools.invoke(context_messages)
                
                # 1. Native Check
                tool_calls = getattr(response, "tool_calls", [])
                
                # 2. Text-based Check (If response has content but no native calls)
                if not tool_calls and response.content:
                    tool_calls = self._rescue_tool_calls(response.content, iteration)

                # Handle Tool Calls
                if tool_calls:
                    # print(f"🛠️ Tool Call Detected (Iter {iteration}): {tool_calls}")
                    
                    # Ensure tool_calls is on the message for history
                    response.tool_calls = tool_calls
                    context_messages.append(response)
                    
                    # Execute each tool call
                    for tool_call in tool_calls:
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
                        elif tool_name == "search_images":
                            tool_result_text, tool_docs = self._search_images(args.get("query", ""))
                        elif tool_name == "update_rfq_draft":
                             # This tool modifies internal state (pending_update)
                             # PASS COLLECTED DOCS FOR CONTEXT
                            tool_result_text, tool_docs = self._update_rfq_draft(args.get("instructions", ""), found_documents)
                        
                        # Deduplicate and extend found_documents
                        for d in tool_docs:
                            # Create unique key for deduplication
                            d_id = d.get("image_id") or f"{d.get('file')}:{d.get('chunk_id')}"
                            # Check if already in found_documents
                            exists = False
                            for fd in found_documents:
                                fd_id = fd.get("image_id") or f"{fd.get('file')}:{fd.get('chunk_id')}"
                                if d_id == fd_id:
                                    exists = True
                                    break
                            if not exists:
                                found_documents.append(d)
                        
                        # Append tool output message
                        context_messages.append(ToolMessage(
                            content=tool_result_text,
                            tool_call_id=tool_call_id
                        ))
                    
                    # Continue loop to let LLM generate response based on tool output
                    continue
                
                # No tool call -> Final Response
                response_text = response.content
                
                # --- FINAL IMAGE SCRUBBER ---
                # Remove any [[IMAGE_ID:n]] tags that are not in our verified found_documents
                # This prevents the AI from "hallucinating" or using deleted IDs in the final chat message
                valid_ids = [str(d.get("image_id")) for d in found_documents if d.get("image_id")]
                
                def final_scrub_cb(match):
                    mid = match.group(1)
                    if mid in valid_ids:
                        return f"[[IMAGE_ID:{mid}]]"
                    return "" # Remove invalid/deleted tag

                response_text = re.sub(r"\[\[IMAGE_ID:([^\]]+)\]\]", final_scrub_cb, response_text)
                # ---------------------------

                # print(f"✅ Final Response. Found docs: {len(found_documents)}")
                return response_text, found_documents, self.pending_update
                
            except Exception as e:
                err_str = str(e)
                print(f"❌ Agent Tool Error: {err_str}")
                
                # RESCUE ATTEMPT: If Groq errored but the error message contains the tool call
                # (Common in 400 errors where the model outputs invalid XML)
                rescued_calls = self._rescue_tool_calls(err_str, iteration)
                
                if rescued_calls:
                    # print(f"🩹 Rescued {len(rescued_calls)} calls from error message!")
                    # Synthesize an AI message with tool calls
                    rescue_msg = AIMessage(content="Attempting rescued tool call...", tool_calls=rescued_calls)
                    context_messages.append(rescue_msg)
                    
                    for tool_call in rescued_calls:
                        tool_name = tool_call["name"]
                        args = tool_call["args"]
                        tool_call_id = tool_call["id"]
                        
                        tool_result_text = "Error: Tool failed"
                        try:
                            if tool_name in self.tools:
                                # Special handling for draft update to pass docs
                                if tool_name == "update_rfq_draft":
                                    res = self._update_rfq_draft(args.get("instructions", ""), found_documents)
                                else:
                                    res = self.tools[tool_name](**args)
                                    
                                if isinstance(res, tuple):
                                    tool_result_text, tool_docs = res
                                    found_documents.extend(tool_docs)
                                else:
                                    tool_result_text = str(res)
                        except Exception as te:
                            tool_result_text = f"Tool Execution Error: {te}"

                        context_messages.append(ToolMessage(
                            content=tool_result_text,
                            tool_call_id=tool_call_id
                        ))
                    continue # Try again after rescue
                
                # Final Fallback
                if iteration == 0:
                     try:
                        return llm.invoke(context_messages).content, found_documents, None
                     except:
                        pass
                return f"I encountered an issue while generating the chat response, but I have successfully applied your draft updates: {err_str}", [], self.pending_update
        
        # Only return sources if we actually updated the draft or if it's the final turn
        # This prevents sources from "popping up" prematurely during validation turns
        final_sources = found_documents if (self.pending_update or iteration >= 2) else []
        return response_text, final_sources, self.pending_update


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
