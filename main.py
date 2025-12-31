import os
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

app = FastAPI(title="RFQ Deep Agent – Conversational Build")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = "data"
EXPORT_DIR = "exports"
os.makedirs(EXPORT_DIR, exist_ok=True)

app.mount("/exports", StaticFiles(directory="exports"), name="exports")


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

    system_prompt = """
You are a professional RFQ conversational assistant.

STRICT RULES:
1️⃣ Default mode → ONLY Impact Analysis
- 🔎 RFQ Impact Analysis
- ✔️ What changed
- 🔄 Dependent dependencies
- ✅ Short recommendations
- NO RFQ rewriting

2️⃣ BUT WHEN USER EXPLICITLY SAYS ANY OF:
"apply", "update rfq", "generate final rfq", 
"draft rfq", "final structured rfq", 
"apply recommended changes", "update document"

→ SWITCH MODE

You MUST:
- Rewrite ONLY the RFQ
- Output CLEAN RFQ only
- No emojis
- No chat text
- No storytelling
- No impact analysis
- No explanation
- Maintain OEM RFQ structure exactly:

BACKGROUND & OBJECTIVE
SCOPE OF WORK
TECHNICAL REQUIREMENTS
SERVICE LEVEL AGREEMENT
COMPLIANCE & STANDARDS
COMMERCIAL TERMS
DELIVERY TIMELINE
EVALUATION CRITERIA
REVISION HISTORY
"""


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

    question = f"""
You are validating whether a requirement is related to AUTOMOBILE / AUTOMOTIVE industry.

Requirement:
{data.requirement}

Rules:
- Consider automotive manufacturing, components, electronics, ECUs, lighting, safety systems, testing, wiring, chassis, plastics, propulsion, EV, hybrid, spare parts etc.
- Do NOT depend only on the words "vehicle", "car", "automobile".
- Understand context. If ambiguous, answer "MAYBE".

Answer ONLY ONE WORD:
YES
NO
MAYBE
"""

    result = chat_with_llm([
        {"role": "system", "content": "You are an RFQ domain validator."},
        {"role": "user", "content": question}
    ]).strip().lower()

    if result.startswith("yes"):
        return {"valid": True, "message": "Valid Automobile Requirement"}

    if result.startswith("maybe"):
        return {
            "valid": False,
            "message": "It looks partially related. Please provide little more clarity."
        }

    return {"valid": False, "message": "Not related to automobile domain"}


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

    prompt = f"""
You are a senior automotive OEM procurement expert.
Generate a STRICT PROFESSIONAL RFQ with OEM standard quality.

Requirement:
{data.requirement}

User Inputs:
{data.filled_data}

Reference RFQ file name (for context only, do NOT mention in output):
{data.reference_file}

MANDATORY STRUCTURE:
BACKGROUND & OBJECTIVE
SCOPE OF WORK
TECHNICAL REQUIREMENTS
SERVICE LEVEL AGREEMENT
COMPLIANCE & STANDARDS
COMMERCIAL TERMS
DELIVERY TIMELINE
EVALUATION CRITERIA
REVISION HISTORY

STRICT RULES:
- DO NOT add emojis
- DO NOT be conversational
- NO headings like "Here is the RFQ"
- Just output final RFQ body text
- Must feel like Stellantis / OEM professional RFQ
"""

    final_text = chat_with_llm([
        {"role": "system", "content": "You are a strict RFQ drafting agent. Output only RFQ text."},
        {"role": "user", "content": prompt}
    ])

    clean = clean_rfq_text(final_text)

    return {
        "status": "SUCCESS",
        "draft": clean
    }


@app.post("/analyze_changes")
def analyze_changes(data: ChangeModel):

    prompt = f"""
You are an RFQ impact analysis expert.

Compare ORIGINAL RFQ vs EDITED RFQ and identify:
1️⃣ What user changed
2️⃣ Which other sections SHOULD also be updated because of dependency
3️⃣ Short actionable recommendations
4️⃣ DO NOT rewrite RFQ
5️⃣ Be concise, bullet points only

--- ORIGINAL RFQ ---
{data.old_text}

--- EDITED RFQ ---
{data.new_text}
"""

    reply = chat_with_llm([
        {"role": "system", "content": "You are a strict RFQ impact analysis assistant."},
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


@app.post("/export/pdf")
async def export_pdf(body: str = Body(..., media_type="text/plain")):

    clean = clean_rfq_text(body)

    rfq = {"name": "CUSTOM_RFQ", "domain": "Automobile", "body": clean}
    file_bytes = render_pdf(rfq, 1)

    path = os.path.join(EXPORT_DIR, "RFQ_Final.pdf")
    open(path, "wb").write(file_bytes)

    return {"path": path.replace("\\", "/")}


@app.post("/export/docx")
async def export_docx(body: str = Body(..., media_type="text/plain")):

    clean = clean_rfq_text(body)

    rfq = {"name": "CUSTOM_RFQ", "domain": "Automobile", "body": clean}
    file_bytes = render_docx(rfq, 1)

    path = os.path.join(EXPORT_DIR, "RFQ_Final.docx")
    open(path, "wb").write(file_bytes)

    return {"path": path.replace("\\", "/")}
