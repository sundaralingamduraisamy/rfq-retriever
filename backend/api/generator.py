from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.llm_agent import chat_with_llm, agent
from core.prompt_loader import load_prompt
from core.prompt_loader import load_prompt
from core.retriever import hybrid_search, get_full_rfq, search_images
from core.text_utils import clean_rfq_text

router = APIRouter()

# Models
class ChatModel(BaseModel):
    history: list
    user_message: str
    selected_rfq: str | None = None
    current_draft: str | None = None
    mode: str = "agent"  # 'agent' or 'manual'

class ValidateModel(BaseModel):
    requirement: str

class SearchModel(BaseModel):
    query: str

class FinalRFQModel(BaseModel):
    requirement: str
    filled_data: dict
    reference_file: str

class ChangeModel(BaseModel):
    old_text: str
    new_text: str

class EditRFQModel(BaseModel):
    current_text: str
    instruction: str


# ----------------------------------------------------------------
# Core Logic APIs (Chat, Validate, Generate)
# ----------------------------------------------------------------

@router.post("/chat")
def chat(req: ChatModel):
    # Short circuit for start_session
    if req.user_message == "start_session":
         return {"reply": "Hi! I'm your RFQ Assistant. I can help you draft, validate, and search your RFQs."}

    # Prepare messages
    messages = []
    for m in req.history:
        messages.append({
            "role": m.get("role", "user"),
            "content": m.get("text", "") or m.get("content", "")
        })
    
    # Add context if selected_rfq is provided but no draft (Reference Context)
    if req.selected_rfq and not req.current_draft:
         try:
             rfq_text = get_full_rfq(req.selected_rfq)
             messages.append({"role": "system", "content": f"User is viewing reference document: {req.selected_rfq}\nContent:\n{rfq_text}"})
         except: pass

    # Add current message
    messages.append({"role": "user", "content": req.user_message})

    # Call Agent
    reply, docs, update_info = agent.process(messages, current_draft=req.current_draft, mode=req.mode)
    
    return {
        "reply": reply,
        "related_documents": docs, 
        "updated_draft": update_info["updated_text"] if update_info else None,
        "impact_analysis": update_info["analysis"] if update_info else None
    }

@router.post("/validate_requirement")
def validate_requirement(data: ValidateModel):
    """Validate if user input is a valid requirement or chat message"""
    try:
        # Allow common greetings and questions
        user_input = data.requirement.strip().lower()
        greetings = ["hi", "hello", "hey", "help", "what", "how", "can you", "tell me", "show me"]
        
        # If it's a greeting or question, allow it
        if any(user_input.startswith(g) for g in greetings) or "?" in user_input:
            return {"valid": True, "message": "Valid"}
        
        # For everything else, check with LLM
        res = chat_with_llm([
            {"role": "system", "content": load_prompt("validator_system.md")},
            {"role": "user", "content": data.requirement}
        ])
        
        if "yes" in res.lower():
            return {"valid": True, "message": "Valid Automobile Requirement"}
        
        if "maybe" in res.lower():
            return {"valid": False, "message": "Please provide more clarity"}
        
        return {"valid": False, "message": "Not related to automobile domain"}
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/search_rfq")
def search_rfq(data: SearchModel):
    # Use PgVector Hybrid Search
    results = hybrid_search(data.query)
    
    # Deduplicate by filename, keeping highest relevance score
    seen_files = {}
    for r in results:
        filename = r["source"]["file"]
        relevance = r["relevance"]
        
        if filename not in seen_files or relevance > seen_files[filename]["relevance"]:
            seen_files[filename] = r
    
    # Convert back to list and sort by relevance
    results = sorted(seen_files.values(), key=lambda x: x["relevance"], reverse=True)
    
    # Limit to top 5 results
    results = results[:5]
    
    return {
        "results": [
            {"file": r["source"]["file"], "score": r["relevance"]}
            for r in results
        ]
    }

@router.post("/generate_final_rfq")
def generate_final_rfq(data: FinalRFQModel):
    # Keep existing logic
    # 1. Search for relevant images
    images = search_images(data.requirement, top_k=3)
    
    image_context = ""
    if images:
        image_context = "\n\nAVAILABLE IMAGES (Use [[IMAGE_ID:n]] to insert):"
        for img in images:
            image_context += f"\n- Image ID: {img['id']}\n  Description: {img['description']}\n  Filename: {img['file']}"
        
        # Append instruction to prompt
        image_context += "\n\nIMPORTANT: You MUST insert the above images into the RFQ where relevant using the [[IMAGE_ID:id]] syntax."

    # 2. Load Prompt with Image Context
    prompt = load_prompt("generate_final_rfq_user.md", 
                         requirement=data.requirement + image_context, 
                         filled_data=data.filled_data, 
                         reference_file=data.reference_file)
    
    final_text = chat_with_llm([
        {"role": "system", "content": load_prompt("drafter_strict_system.md")},
        {"role": "user", "content": prompt}
    ])
    
    return {"status": "SUCCESS", "draft": clean_rfq_text(final_text)}

@router.post("/analyze_changes")
def analyze_changes(data: ChangeModel):
    """Analyze impact of changes between two versions"""
    prompt = load_prompt("analyze_changes_user.md", old_text=data.old_text, new_text=data.new_text)
    
    reply = chat_with_llm([
        {"role": "system", "content": load_prompt("impact_analysis_system.md")},
        {"role": "user", "content": prompt}
    ])
    
    return {"analysis": reply}

@router.post("/edit_rfq")
def edit_rfq(data: EditRFQModel):
    """Edit RFQ with instructions and analyze impact"""
    # 1. Apply Edit
    edit_prompt = load_prompt("edit_rfq_user.md", 
                              instruction=data.instruction, 
                              current_text=data.current_text)
    
    updated_text = chat_with_llm([
        {"role": "system", "content": load_prompt("edit_rfq_system.md")},
        {"role": "user", "content": edit_prompt}
    ])
    
    updated_text = clean_rfq_text(updated_text)
    
    # 2. Analyze Impact
    analysis_prompt = load_prompt("analyze_changes_user.md", 
                                  old_text=data.current_text, 
                                  new_text=updated_text)
    
    analysis = chat_with_llm([
        {"role": "system", "content": load_prompt("impact_analysis_system.md")},
        {"role": "user", "content": analysis_prompt}
    ])
    
    return {
        "updated_text": updated_text,
        "analysis": analysis
    }
