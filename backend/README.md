# RFQ Deep Agent – Conversational RFQ Generator

An intelligent RFQ Assistant built using **FastAPI + LLM + Retrieval System** to:
- Validate automotive domain requirements
- Search relevant RFQs using hybrid search
- Load RFQ templates
- Conversationally guide users
- Perform RFQ Impact Analysis
- Auto-apply recommended changes
- Generate Strict OEM-Standard RFQs
- Export Professionally Structured RFQ as PDF / DOCX

This is NOT a toy chatbot.  
This behaves like a professional RFQ expert.

---

## ✨ Features

### ✔️ Conversational RFQ Assistant
- Welcomes user dynamically based on time
- Understands natural language RFQ needs
- Asks clarification questions only when required

### ✔️ Domain Validation
Checks if the requirement is actually Automotive related.

### ✔️ RFQ Retrieval
Uses Hybrid Search to retrieve best matching RFQs.

### ✔️ RFQ Editing + Impact Analysis
Whenever user edits something:
- Identifies WHAT changed
- Detects DEPENDENT SECTIONS
- Gives ACTIONABLE RECOMMENDATIONS
- No unnecessary rewriting

### ✔️ Intelligent RFQ Auto-Drafting
When user explicitly asks for:
- *apply changes*
- *generate final structured rfq*
- *update rfq*
- *create final rfq*

LLM switches into **STRICT OEM RFQ Mode** and generates a highly professional structured RFQ.

### ✔️ Clean RFQ Text Engine
Fixes formatting issues:
- Removes junk text
- Ensures headings spacing
- Proper bullet structure
- Clean sections

### ✔️ Export Engine
Exports perfectly formatted:
- PDF (ReportLab)
- DOCX

With:
- Cover Page
- Table of Contents
- Section Formatting
- Revision History
- Page Headers & Footers

---

## 🏗️ Project Structure

```
backend/
├── api/                    # API route handlers
│   ├── documents.py       # Document management endpoints
│   ├── generator.py       # RFQ generation endpoints
│   └── rfqs.py           # RFQ management endpoints
├── core/                  # Core business logic
│   ├── embedding_model.py # Text embedding utilities
│   ├── image_processor.py # Image classification & embedding
│   ├── ingestion.py      # Document ingestion pipeline
│   ├── llm_agent.py      # Conversational agent logic
│   ├── llm_provider.py   # Multi-provider LLM support
│   ├── prompt_loader.py  # Prompt template management
│   ├── retriever.py      # Hybrid search implementation
│   └── text_utils.py     # Text processing utilities
├── prompts/              # LLM prompt templates
├── data/                 # Document storage (gitignored)
├── exports/              # Generated RFQ exports (gitignored)
├── database.py           # PostgreSQL + pgvector connection
├── logging_config.py     # Centralized logging setup
├── main.py              # FastAPI application entry point
├── render.py            # PDF/DOCX rendering engine
├── settings.py          # Configuration management
└── requirements.txt     # Python dependencies
```

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.10+
- PostgreSQL with pgvector extension
- Docker (for database)

### 1. Start Database
```bash
docker-compose up -d
```

### 2. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 3. Configure Environment
Copy `.env.example` to `.env` and configure:
```bash
cp .env.example .env
```

Required settings:
- `LLM_API_KEY` - Your Groq/OpenAI/Anthropic API key
- `HUGGINGFACE_TOKEN` - For image models (optional)
- `POSTGRES_*` - Database credentials (default works with docker-compose)

### 4. Run Server
```bash
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

API will be available at: http://127.0.0.1:8000  
API Documentation: http://127.0.0.1:8000/docs

---

## 🧪 Testing Ideas

Try these conversational cases:
- *need rfq for steering components*
- *change delivery timeline to 3 weeks*
- *apply the recommended changes*
- *generate final structured rfq*
- *auto update dependent sections*
- *export as pdf*

---

## ⚙️ Configuration

### LLM Providers
Supports multiple providers via `.env`:
- **Groq** (default, fast and free)
- **OpenAI** (GPT-4, GPT-3.5)
- **Anthropic** (Claude)
- **Google** (Gemini)

### Image Models
- **Primary**: `jinaai/jina-clip-v1` (configurable)
- **Fallback**: `openai/clip-vit-base-patch32`

Change via `IMAGE_MODEL_NAME` in `.env`

---

## ⚠️ Known Constraints
- Only supports AUTOMOTIVE domain (by design)
- Requires internet for LLM responses
- Must not manually break formatting logic

---

## 🏁 Status
Actively Functional  
Used for real RFQ conversational automation  
Not a demo toy.

---

## 🤝 Credits
Built with:
- FastAPI
- Groq LLM
- PostgreSQL + pgvector
- Sentence Transformers
- JinaCLIP
- ReportLab
- Python-Docx
