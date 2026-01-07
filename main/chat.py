import os
import sys
import time
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

import psycopg2
from psycopg2.pool import SimpleConnectionPool
from sentence_transformers import SentenceTransformer

from langchain_core.tools import StructuredTool
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()


# ============================================================================
# CONFIGURATION
# ============================================================================
class Config:
    """Configuration from .env"""
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5433")
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "documents_db")
    POSTGRES_POOL_SIZE = int(os.getenv("POSTGRES_POOL_SIZE", "5"))

    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    VECTOR_SEARCH_K = int(os.getenv("VECTOR_SEARCH_K", "5"))
    MIN_SIMILARITY_THRESHOLD = float(os.getenv("MIN_SIMILARITY_THRESHOLD", "0.3"))
    PREVIEW_LENGTH = int(os.getenv("PREVIEW_LENGTH", "200"))

    # Groq Configuration (for answering)
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    GROQ_TEMPERATURE = float(os.getenv("GROQ_TEMPERATURE", "0.7"))

    DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"


# ============================================================================
# DATA CLASSES
# ============================================================================
class MessageRole(Enum):
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class RetrievedSource:
    """Retrieved document source"""
    summary_id: int
    filename: str
    similarity: float
    preview: str


@dataclass
class RetrievalResult:
    """Vector retrieval result"""
    sources: List[RetrievedSource]
    search_time_ms: float
    total_results: int


# ============================================================================
# DATABASE MANAGER
# ============================================================================
class DatabaseManager:
    """PostgreSQL connection pool"""

    def __init__(self, config: Config):
        self.config = config
        try:
            self.pool = SimpleConnectionPool(
                1, config.POSTGRES_POOL_SIZE,
                host=config.POSTGRES_HOST,
                port=config.POSTGRES_PORT,
                user=config.POSTGRES_USER,
                password=config.POSTGRES_PASSWORD,
                database=config.POSTGRES_DB,
                connect_timeout=5
            )
            if config.DEBUG_MODE:
                print(f"✅ Database pool created: {config.POSTGRES_HOST}:{config.POSTGRES_PORT}")
        except psycopg2.Error as e:
            print(f"❌ Database connection failed: {e}")
            raise

    def get_connection(self):
        return self.pool.getconn()

    def return_connection(self, conn):
        self.pool.putconn(conn)

    def close_all(self):
        self.pool.closeall()

    def execute_query(self, query: str, params: tuple = None) -> List[tuple]:
        """Execute SELECT query"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params or ())
            return cursor.fetchall()
        except psycopg2.Error as e:
            print(f"❌ Query error: {e}")
            return []
        finally:
            cursor.close()
            self.return_connection(conn)

    def execute_query_single(self, query: str, params: tuple = None) -> Optional[tuple]:
        """Execute SELECT and return single result"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params or ())
            return cursor.fetchone()
        except psycopg2.Error as e:
            print(f"❌ Query error: {e}")
            return None
        finally:
            cursor.close()
            self.return_connection(conn)


# ============================================================================
# VECTOR RETRIEVER
# ============================================================================
class VectorRetriever:
    """
    MAIN CLASS: Retrieve embeddings from pgvector

    This searches pgvector for similar embeddings
    """

    def __init__(self, db_manager: DatabaseManager, embedding_model: SentenceTransformer, config: Config):
        self.db = db_manager
        self.embedding_model = embedding_model
        self.config = config

    def retrieve_similar(self, query: str, top_k: Optional[int] = None) -> RetrievalResult:
        """
        ⭐ MAIN RETRIEVAL FUNCTION ⭐

        INPUT: User query (text)

        STEP 1: Encode query to embedding
        STEP 2: Search pgvector for similar embeddings
        STEP 3: Return top K matches
        """

        if top_k is None:
            top_k = self.config.VECTOR_SEARCH_K

        start_time = time.time()

        try:
            # ================================================================
            # STEP 1: ENCODE QUERY TO EMBEDDING (SentenceTransformer)
            # ================================================================
            print(f"   🔍 Encoding query: '{query}'")
            query_embedding = self.embedding_model.encode(query)
            # Result: array of 384 numbers (same as document embeddings)
            embedding_str = str(query_embedding.tolist())
            print(f"   ✅ Query embedding: {len(query_embedding)} dimensions")

            # ================================================================
            # STEP 2: SEARCH PGVECTOR FOR SIMILAR EMBEDDINGS
            # ================================================================
            print(f"   🔍 Searching {top_k} documents in pgvector...")

            sql_query = """
                SELECT 
                    ds.id as summary_id,
                    d.filename,
                    1 - (se.embedding <=> %s::vector) as similarity,
                    ds.summary_text
                FROM summary_embeddings se
                JOIN document_summaries ds ON se.summary_id = ds.id
                JOIN documents d ON ds.document_id = d.id
                WHERE (1 - (se.embedding <=> %s::vector)) > %s
                ORDER BY similarity DESC
                LIMIT %s
            """

            results = self.db.execute_query(
                sql_query,
                (embedding_str, embedding_str, self.config.MIN_SIMILARITY_THRESHOLD, top_k)
            )

            # ================================================================
            # STEP 3: FORMAT RESULTS
            # ================================================================
            sources = [
                RetrievedSource(
                    summary_id=r[0],
                    filename=r[1],
                    similarity=float(r[2]),
                    preview=r[3][:self.config.PREVIEW_LENGTH]
                )
                for r in results
            ]

            search_time = (time.time() - start_time) * 1000

            print(f"   ✅ Found {len(sources)} matches in {search_time:.1f}ms")

            if self.config.DEBUG_MODE:
                print(f"\n   Retrieved sources:")
                for src in sources:
                    print(f"   - {src.filename}: {src.similarity:.1%}")

            return RetrievalResult(
                sources=sources,
                search_time_ms=search_time,
                total_results=len(sources)
            )

        except Exception as e:
            print(f"   ❌ Retrieval error: {e}")
            return RetrievalResult(sources=[], search_time_ms=0, total_results=0)


# ============================================================================
# CHAT AGENT WITH RETRIEVAL
# ============================================================================
class ChatAgent:
    """
    Chat agent that retrieves embeddings and answers questions

    Flow:
    1. User asks question
    2. Retrieve similar documents (VectorRetriever)
    3. LangChain agent uses Groq LLM to generate answer
    4. Return natural language response with citations
    """

    def __init__(self, db_manager: DatabaseManager, config: Config):
        self.config = config
        self.db = db_manager
        self.embedding_model = SentenceTransformer(config.EMBEDDING_MODEL)
        self.retriever = VectorRetriever(db_manager, self.embedding_model, config)
        self.conversation = []

        print(f"✅ Embedding model loaded: {config.EMBEDDING_MODEL}")
        print(f"✅ Groq LLM: {config.GROQ_MODEL}")

        self._setup_agent()

    def _setup_agent(self):
        """Setup LangChain agent with tools"""

        # Initialize Groq LLM
        self.llm = ChatGroq(
            model_name=self.config.GROQ_MODEL,
            groq_api_key=self.config.GROQ_API_KEY,
            temperature=self.config.GROQ_TEMPERATURE,
            max_tokens=1024
        )

        # =====================================================================
        # DEFINE TOOLS
        # =====================================================================

        def search_documents(query: str) -> str:
            """
            Search indexed documents using vector similarity.
            Uses pgvector to find similar embeddings based on semantic meaning.

            Returns top matching documents with relevance scores.
            """
            print(f"\n   🔧 Tool: search_documents('{query}')")
            retrieval_result = self.retriever.retrieve_similar(query)

            if not retrieval_result.sources:
                return "No matching documents found. Try a different query."

            summary = f"Found {retrieval_result.total_results} relevant documents:\n\n"
            for i, src in enumerate(retrieval_result.sources[:5], 1):
                summary += f"{i}. [{src.filename}] (Relevance: {src.similarity:.0%})\n"
                summary += f"   {src.preview}\n\n"

            return summary

        def get_full_summary(summary_id: int) -> str:
            """Get the complete summary text of a document"""
            try:
                row = self.db.execute_query_single(
                    "SELECT summary_text FROM document_summaries WHERE id = %s",
                    (summary_id,)
                )
                if row:
                    return f"Complete summary:\n{row[0]}"
                return "Summary not found."
            except Exception as e:
                return f"Error: {e}"

        def list_all_documents() -> str:
            """List all indexed documents in the database"""
            try:
                results = self.db.execute_query(
                    """
                    SELECT 
                        d.filename,
                        ds.word_count,
                        SUBSTRING(ds.summary_text, 1, 50) as preview
                    FROM document_summaries ds
                    JOIN documents d ON ds.document_id = d.id
                    ORDER BY d.filename
                    """
                )

                if not results:
                    return "No documents indexed in the system."

                formatted = "📚 Indexed Documents:\n\n"
                for filename, word_count, preview in results:
                    formatted += f"📄 {filename}\n"
                    formatted += f"   Summary: {word_count} words\n"
                    formatted += f"   Preview: {preview}...\n\n"

                return formatted
            except Exception as e:
                return f"Error: {e}"

        # Create tools
        tools = [
            StructuredTool.from_function(search_documents),
            StructuredTool.from_function(get_full_summary),
            StructuredTool.from_function(list_all_documents),
        ]

        # System prompt
        system_prompt = """You are an intelligent RFQ Assistant. Your goal is to help users find specific details in documents, but you must behave like a consultant, not a search engine.

RULES:
1. When the user asks a broad question (e.g., "ADAS components"), DO NOT show the document content immediately.
2. First, use `search_documents` to see what is available.
3. Then, Ask a CLARIFYING QUESTION to narrow down the user's intent.
   - Example: "I found multiple documents related to ADAS. Are you interested in the 'Scope of Work', 'Technical Specifications', or 'Pricing'?"
4. ONLY provides the full answer/content when the user confirms what successful specific aspect they want.
5. You must be conversational. Remember what the user said previously.

Always use the tools to find information, but gate the final answer behind a clarification interaction."""

        # Create prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        # Create agent
        agent = create_tool_calling_agent(self.llm, tools, prompt)

        # Create Executor with memory handling
        self.executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process user query with conversational memory
        """
        start_time = time.time()

        # Update local history with the current user query
        self.conversation.append({
            "role": "user",
            "content": query,
            "timestamp": datetime.now()
        })

        # Format history for LangChain
        # We take the last 6 messages to keep context window manageable
        history_objects = []
        for msg in self.conversation[-6:]: # Include current user query in history for the LLM
            if msg["role"] == "user":
                history_objects.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                history_objects.append(SystemMessage(content=msg["content"]))

        print(f"\n🤖 Processing query with Groq LLM...")

        try:
            response_obj = self.executor.invoke({
                "input": query,
                "chat_history": history_objects
            })
            response_text = response_obj.get("output", "I couldn't process that query.")
        except Exception as e:
            response_text = f"Error: {e}"

        # Update local history with the assistant's response
        self.conversation.append({
            "role": "assistant",
            "content": response_text,
            "timestamp": datetime.now()
        })

        elapsed = (time.time() - start_time) * 1000

        return {
            "response": response_text,
            "time_ms": elapsed,
        }


# ============================================================================
# TERMINAL UI
# ============================================================================
class TerminalUI:
    """Terminal interface with colored output"""

    COLORS = {
        'CYAN': '\033[96m', 'GREEN': '\033[92m', 'YELLOW': '\033[93m',
        'BLUE': '\033[94m', 'RED': '\033[91m', 'RESET': '\033[0m', 'BOLD': '\033[1m',
    }

    @staticmethod
    def colored(text: str, color: str) -> str:
        return f"{TerminalUI.COLORS.get(color, '')}{text}{TerminalUI.COLORS['RESET']}"

    @staticmethod
    def print_header():
        header = """
╔══════════════════════════════════════════════════════════════════╗
║     RFQ CHAT v2.0 - VECTOR RETRIEVAL WITH EMBEDDINGS            ║
║     Powered by: pgvector + SentenceTransformer + Groq LLM       ║
║                                                                  ║
║  How it works:                                                   ║
║  1. You ask a question                                          ║
║  2. Query is converted to embedding (384 numbers)               ║
║  3. pgvector searches for similar embeddings (cosine distance)  ║
║  4. Retrieved document summaries sent to Groq LLM               ║
║  5. Natural language answer is generated with citations         ║
╚══════════════════════════════════════════════════════════════════╝
        """
        print(TerminalUI.colored(header, 'CYAN'))

    @staticmethod
    def print_response(response: Dict[str, Any]):
        print("\n" + TerminalUI.colored("=" * 70, 'BLUE'))
        print(TerminalUI.colored("ANSWER:", 'BOLD'))
        print(TerminalUI.colored("=" * 70, 'BLUE'))
        print(response['response'])
        print(TerminalUI.colored("-" * 70, 'BLUE'))
        print(f"⏱️  Response Time: {response['time_ms']:.1f}ms")
        print(TerminalUI.colored("=" * 70, 'BLUE') + "\n")


# ============================================================================
# MAIN APPLICATION
# ============================================================================
class ChatApp:
    """Main chat application"""

    def __init__(self, config: Config):
        self.config = config
        self.db_manager = DatabaseManager(config)
        self.agent = ChatAgent(self.db_manager, config)

    def run(self):
        """Run interactive chat loop"""
        TerminalUI.print_header()

        print(TerminalUI.colored("✅ Vector retrieval system ready", 'GREEN'))
        print(TerminalUI.colored("✅ pgvector database connected", 'GREEN'))
        print(TerminalUI.colored("✅ Groq LLM initialized", 'GREEN'))

        print(TerminalUI.colored("\nAvailable Commands:", 'YELLOW'))
        print(TerminalUI.colored("  /list  - Show all indexed documents", 'YELLOW'))
        print(TerminalUI.colored("  /exit  - Quit the application\n", 'YELLOW'))

        print(TerminalUI.colored("Start asking questions about your documents!", 'GREEN'))
        print(TerminalUI.colored("=" * 70 + "\n", 'BLUE'))

        turn = 0
        max_turns = 100

        while turn < max_turns:
            try:
                print(TerminalUI.colored("You: ", 'GREEN'), end="", flush=True)
                user_input = input().strip()

                if not user_input:
                    continue

                turn += 1

                if user_input.lower() == '/exit':
                    print(TerminalUI.colored("👋 Thank you for using RFQ Chat!", 'CYAN'))
                    break

                if user_input.lower() == '/list':
                    results = self.db_manager.execute_query(
                        """
                        SELECT d.filename, ds.word_count
                        FROM document_summaries ds
                        JOIN documents d ON ds.document_id = d.id
                        ORDER BY d.filename
                        """
                    )
                    print("\n" + TerminalUI.colored("📚 Indexed Documents:", 'CYAN') + "\n")
                    if results:
                        for filename, word_count in results:
                            print(f"   ✓ {filename} ({word_count} words)")
                    else:
                        print("   No documents indexed.")
                    print()
                    continue

                print(TerminalUI.colored("\n🔍 Searching indexed documents...", 'YELLOW'))
                response = self.agent.process_query(user_input)
                TerminalUI.print_response(response)

            except KeyboardInterrupt:
                print("\n" + TerminalUI.colored("👋 Goodbye!", 'CYAN'))
                break
            except Exception as e:
                print(TerminalUI.colored(f"❌ Error: {e}", 'RED'))
                if self.config.DEBUG_MODE:
                    import traceback
                    traceback.print_exc()

        self.cleanup()

    def cleanup(self):
        self.db_manager.close_all()


# ============================================================================
# ENTRY POINT
# ============================================================================
def main():
    config = Config()

    print("\n" + "=" * 70)
    print("💬 CHAT WITH VECTOR RETRIEVAL - Groq + pgvector")
    print("=" * 70)
    print("\nConfiguration:")
    print(f"  Database: {config.POSTGRES_HOST}:{config.POSTGRES_PORT}")
    print(f"  Embedding Model: {config.EMBEDDING_MODEL}")
    print(f"  LLM: {config.GROQ_MODEL}")
    print(f"  Similarity Threshold: {config.MIN_SIMILARITY_THRESHOLD}")
    print(f"  Debug Mode: {config.DEBUG_MODE}")

    try:
        app = ChatApp(config)
        app.run()
    except Exception as e:
        print(TerminalUI.colored(f"❌ Fatal error: {e}", 'RED'))
        if config.DEBUG_MODE:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()