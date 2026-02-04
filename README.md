# Stellantis RFQ AI Agent 🚙🤖

A powerful Retrieval-Augmented Generation (RAG) system designed to automate the creation of automotive Requests for Quotation (RFQs). This agent leverages advanced LLMs (Groq enabled) and State-of-the-Art Vision Models (JinaCLIP) to research technical manuals, identify components, and draft professional RFQ documents in seconds.

## 🌟 Key Features

*   **⚡ Zero-Touch Proactive Drafting:** Just ask for a component (e.g., "Brake Caliper"), and the agent automatically researches and updates the draft.
*   **🖼️ Intelligent Image Search (JinaCLIP):** Uses `jinaai/jina-clip-v1` to semantically understand and retrieve relevant automotive diagrams from your documents, filtering out irrelevant noise.
*   **📂 RAG Knowledge Base:** Upload PDF/DOCX manuals, and the system indexes them for instant retrieval.
*   **📄 Professional Exports:** Export your finished RFQ to beautifully formatted PDF or DOCX files with automatically generated tables of contents and embedded images.
*   **🔒 Secure & Local:** Runs locally with Docker support, keeping your proprietary data safe.

## 🛠️ Technology Stack

*   **Backend:** Python (FastAPI), PyTorch, Transformers, LangChain.
*   **Frontend:** React (Vite), Tailwind CSS, Lucide Icons.
*   **Database:** PostgreSQL (pgvector) for vector embeddings.
*   **AI Models:**
    *   **LLM:** Llama-3 (via Groq API) for reasoning and drafting.
    *   **Vision:** `jinaai/jina-clip-v1` for semantic image understanding.
    *   **Embedding:** `sentence-transformers` for text retrieval.

## 🚀 Getting Started

### Prerequisites

*   Docker & Docker Compose
*   Python 3.10+ (for local backend dev)
*   Node.js 18+ (for local frontend dev)

## 🩺 Quick Start for Reviewers (Team Lead)

If you are cloning this repository for the first time, follow these steps to get a working environment:

1.  **Clone the Repo:**
    ```bash
    git clone https://github.com/sundaralingamduraisamy/rfq-retriever.git
    cd rfq-retriever
    ```
2.  **Environment Setup:**
    - Copy `backend/.env.example` to `backend/.env` and fill in your `LLM_API_KEY` (Groq) and `HUGGINGFACE_TOKEN`.
    - Copy `frontend/.env.example` to `frontend/.env`.
3.  **Deploy (Quickest):**
    ```bash
    docker-compose up --build
    ```
4.  **Verification:**
    - Open `http://localhost:5173` for the UI.
    - Open `http://localhost:8000/docs` for the API documentation.

### 1. Environment Setup

**Backend:**
Create a `.env` file in the `backend/` directory (use `backend/.env.example` as a template):

```bash
LLM_PROVIDER="groq"
LLM_API_KEY="your_groq_key"
HUGGINGFACE_TOKEN="hf_..."  # REQUIRED for JinaCLIP model access
POSTGRES_PASSWORD="your_db_password"
```

**Frontend:**
Create a `.env` file in the `frontend/` directory (use `frontend/.env.example` as a template):

```bash
VITE_BACKEND_URL="http://localhost:8000"
```

> **IMPORTANT:** You MUST provide a valid Hugging Face User Access Token in `HUGGINGFACE_TOKEN` to download the JinaCLIP model.

### 2. Run with Docker (Recommended)

```bash
docker-compose up --build
```

Access the app at `http://localhost:5173`.

### 3. Run Locally

**Backend:**
```bash
cd backend
pip install -r requirements.txt
python main.py
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## 📚 Documentation

*   **API Docs:** `http://localhost:8000/docs`
*   **Walkthrough:** See `walkthrough.md` in the artifacts folder for recent update details.
