import os
import uuid
import uvicorn
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from starlette.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime
import random

from core.retriever import hybrid_search, get_full_rfq
from render import render_pdf, render_docx
from core.llm_agent import chat_with_llm
from core.prompt_loader import load_prompt

from settings import settings

app = FastAPI(title=settings.APP_TITLE)

# Debug: Print loaded LLM config
print(f"✅ LLM Config: Provider={settings.LLM_PROVIDER}, Model={settings.LLM_MODEL_NAME}")

# Generate a unique instance ID on startup
SERVER_INSTANCE_ID = str(uuid.uuid4())

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = settings.DATA_DIR
EXPORT_DIR = settings.EXPORT_DIR
os.makedirs(EXPORT_DIR, exist_ok=True)

app.mount("/exports", StaticFiles(directory=settings.EXPORT_DIR), name="exports")


class ValidateModel(BaseModel):
    requirement: str


class SearchModel(BaseModel):
    query: str


class FinalRFQModel(BaseModel):
    requirement: str
    filled_data: dict
    reference_file: str


class ChatModel(BaseModel):
    history: list
    user_message: str
    selected_rfq: str | None = None


class ChangeModel(BaseModel):
    old_text: str
    new_text: str



class EditRFQModel(BaseModel):
    current_text: str
    instruction: str


class LoginRequest(BaseModel):
    username: str
    password: str


@app.get("/api/config")
def get_config():
    return {
        "appName": settings.APP_NAME,
        "appRole": settings.APP_ROLE,
        "instanceId": SERVER_INSTANCE_ID
    }


@app.post("/api/login")
def login(creds: LoginRequest):
    if creds.username == settings.APP_USER and creds.password == settings.APP_PASSWORD:
        return {
            "token": "valid-session",  # simplified session
            "user": {
                "name": settings.APP_NAME,
                "role": settings.APP_ROLE
            },
            "instanceId": SERVER_INSTANCE_ID
        }
    raise HTTPException(status_code=401, detail="Invalid Credentials")


@app.get("/")
def root():
    return {"message": "RFQ Deep Agent Running"}


def clean_rfq_text(raw: str) -> str:
    if not raw:
        return ""

    txt = raw.replace("\r", "")

    junk = [
        "How does this look",
        "Do you want more changes",
        "😊",
        "🤔",
        "I've updated",
        "Here is the updated version",
        "Please review",
        "How does this updated RFQ look",
        "Let me know",
        "Here is the revised RFQ",
    ]
    for j in junk:
        txt = txt.replace(j, "")

    section_map = {
        "BACKGROUND & OBJECTIVE": "\n\nBACKGROUND & OBJECTIVE\n\n",
        "SCOPE OF WORK": "\n\nSCOPE OF WORK\n\n",
        "TECHNICAL REQUIREMENTS": "\n\nTECHNICAL REQUIREMENTS\n\n",
        "SERVICE LEVEL AGREEMENT": "\n\nSERVICE LEVEL AGREEMENT\n\n",
        "COMPLIANCE & STANDARDS": "\n\nCOMPLIANCE & STANDARDS\n\n",
        "COMMERCIAL TERMS": "\n\nCOMMERCIAL TERMS\n\n",
        "DELIVERY TIMELINE": "\n\nDELIVERY TIMELINE\n\n",
        "EVALUATION CRITERIA": "\n\nEVALUATION CRITERIA\n\n",
        "REVISION HISTORY": "\n\nREVISION HISTORY\n\n",
    }

    # ---- section cleanup ----
    for k in list(section_map.keys()):
        txt = txt.replace(f"**{k}**", section_map[k])
        txt = txt.replace(f"{k} :", section_map[k])
        txt = txt.replace(f"{k}:", section_map[k])
        txt = txt.replace(k, section_map[k])

    # ---- bullet normalization ----
    txt = txt.replace("•", "\n• ")
    txt = txt.replace("- ", "\n• ")
    txt = txt.replace("* ", "\n• ")

    # ---- numbered points ----
    for i in range(1, 20):
        txt = txt.replace(f"{i}.", f"\n{i}.")

    # ---- remove empty lines ----
    txt = "\n".join([line.strip() for line in txt.splitlines() if line.strip()])

    return txt.strip()

@app.post("/chat")
def chat(req: ChatModel):

    if req.user_message == "start_session":
        hour = datetime.now().hour

        if 5 <= hour < 12:
            greeting = "Good morning 🌤️"
        elif 12 <= hour < 17:
            greeting = "Good afternoon ☀️"
        elif 17 <= hour < 21:
            greeting = "Good evening 🌇"
        else:
            greeting = "Hello 🌙"

        dynamic_lines = [
            "I’m here to support you throughout your RFQ journey.",
            "Let’s work together to create the perfect RFQ.",
            "Just tell me what you need, I’ll handle the rest.",
            "Ready when you are. What RFQ do you want to work on?",
        ]

        return {
            "reply": f"""{greeting}
I’m your RFQ Assistant. {random.choice(dynamic_lines)}
I can help with requirement validation, RFQ search, intelligent drafting, editing and exporting."""
        }

    system_prompt = load_prompt("chat_system_prompt.md")


    messages = [{"role": "system", "content": system_prompt}]

    for m in req.history:
        messages.append({
            "role": "assistant" if m["role"] == "agent" else "user",
            "content": m["text"]
        })

    if req.selected_rfq:
        try:
            rfq_text = get_full_rfq(req.selected_rfq)
            messages.append({
                "role": "system",
                "content": f"Reference RFQ document content:\n{rfq_text}"
            })
        except:
            pass

    messages.append({"role": "user", "content": req.user_message})

    reply = chat_with_llm(messages)

    reply = reply.replace("Here is the revised RFQ", "")
    reply = reply.replace("Here is the updated RFQ", "")

    return {"reply": reply}


@app.post("/validate_requirement")
def validate_requirement(data: ValidateModel):
    print(f"📥 Validating Requirement: {data.requirement}")
    try:
        question = load_prompt("validate_requirement_user.md", requirement=data.requirement)

        result = chat_with_llm([
            {"role": "system", "content": load_prompt("validator_system.md")},
            {"role": "user", "content": question}
        ]).strip().lower()

        print(f"🤖 Validation Result: {result}")

        if "trouble generating" in result or "LLM model is unavailable" in result:
             return {
                "valid": False,
                "message": "⚠️ **System Error**: LLM functionality is unavailable. Please check your **LLM_API_KEY** in `.env`."
            }
    except Exception as e:
        print(f"❌ Error in validate_requirement: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

    if result.startswith("yes"):
        return {"valid": True, "message": "Valid Automobile Requirement"}

    if result.startswith("maybe"):
        return {
            "valid": False,
            "message": "It looks partially related. Please provide little more clarity."
        }
    
    # Allow meta-questions to pass validation so they can reach the chat agent (if we want that)
    # OR keep it strict. For now, let's keep strict but improve the rejection message if it looks like a question.
    
    return {"valid": False, "message": "Not related to automobile domain. Please describe a vehicle component or manufacturing requirement."}


@app.post("/search_rfq")
def search_rfq(data: SearchModel):
    results = hybrid_search(data.query)

    return {
        "results": [
            {"file": r["source"]["file"], "score": r["relevance"]}
            for r in results
        ]
    }


@app.get("/rfq_pdf/{filename}")
def get_pdf(filename: str):
    path = os.path.join(DATA_DIR, filename)

    if not os.path.exists(path):
        raise HTTPException(404, "RFQ PDF Not Found")

    return FileResponse(path, media_type="application/pdf")


# ================================
#  ⭐ INTELLIGENT RFQ BUILDER HERE
# ================================
@app.post("/generate_final_rfq")
def generate_final_rfq(data: FinalRFQModel):

    prompt = load_prompt("generate_final_rfq_user.md", 
                         requirement=data.requirement, 
                         filled_data=data.filled_data, 
                         reference_file=data.reference_file)

    final_text = chat_with_llm([
        {"role": "system", "content": load_prompt("drafter_strict_system.md")},
        {"role": "user", "content": prompt}
    ])

    clean = clean_rfq_text(final_text)

    return {
        "status": "SUCCESS",
        "draft": clean
    }


@app.post("/analyze_changes")
def analyze_changes(data: ChangeModel):

    prompt = load_prompt("analyze_changes_user.md", old_text=data.old_text, new_text=data.new_text)

    reply = chat_with_llm([
        {"role": "system", "content": load_prompt("impact_analysis_system.md")},
        {"role": "user", "content": prompt}
    ])

    return {"analysis": reply}


@app.get("/rfq_text/{filename}")
def get_rfq_text(filename: str):
    try:
        text = get_full_rfq(filename)
        return {"text": clean_rfq_text(text)}
    except:
        raise HTTPException(404, "RFQ Text Not Found")


class ExportRequest(BaseModel):
    content: str


@app.post("/export/pdf")
async def export_pdf(data: ExportRequest):

    clean = clean_rfq_text(data.content)

    rfq = {"name": "CUSTOM_RFQ", "domain": "Automobile", "body": clean}
    file_bytes = render_pdf(rfq, 1)

    path = os.path.join(EXPORT_DIR, "RFQ_Final.pdf")
    open(path, "wb").write(file_bytes)

    return FileResponse(path, media_type="application/pdf", filename="RFQ_Final.pdf")


@app.post("/export/docx")
async def export_docx(data: ExportRequest):

    clean = clean_rfq_text(data.content)

    rfq = {"name": "CUSTOM_RFQ", "domain": "Automobile", "body": clean}
    file_bytes = render_docx(rfq, 1)

    path = os.path.join(EXPORT_DIR, "RFQ_Final.docx")
    open(path, "wb").write(file_bytes)

    return FileResponse(path, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", filename="RFQ_Final.docx")


@app.post("/edit_rfq")
def edit_rfq(data: EditRFQModel):

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


@app.get("/documents")
def list_documents():
    """
    List all documents in the DATA_DIR with metadata.
    """
    if not os.path.exists(DATA_DIR):
        return []

    files = []
    for f in os.listdir(DATA_DIR):
        path = os.path.join(DATA_DIR, f)
        if os.path.isfile(path):
            stats = os.stat(path)
            
            # Determine category based on extension
            ext = f.split(".")[-1].lower() if "." in f else "unknown"
            
            files.append({
                "id": f,
                "name": f,
                "type": ext,
                "category": ext.upper(), # Simple categorization
                "size": stats.st_size,
                "uploadedAt": datetime.fromtimestamp(stats.st_mtime).isoformat(),
                "relevanceScore": 100 # Default for now, or could be omitted
            })
            
    # Sort by newest first
    files.sort(key=lambda x: x["uploadedAt"], reverse=True)
    return files


@app.get("/rfqs")
def list_rfqs():
    """
    List all generated RFQs in the EXPORT_DIR.
    """
    if not os.path.exists(EXPORT_DIR):
        return {"files": []}
    
    files = [f for f in os.listdir(EXPORT_DIR) if os.path.isfile(os.path.join(EXPORT_DIR, f))]
    # Sort files by modification time (newest first)
    files.sort(key=lambda x: os.path.getmtime(os.path.join(EXPORT_DIR, x)), reverse=True)
    return {"files": files}


# Mount the export directory for viewing PDFs
app.mount("/rfq_pdf", StaticFiles(directory=settings.EXPORT_DIR), name="rfq_pdf")


if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)
