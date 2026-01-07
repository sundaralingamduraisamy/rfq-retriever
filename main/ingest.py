
import os
import sys
import glob
import io

# Force UTF-8 for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Tuple, Optional
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from sentence_transformers import SentenceTransformer
from datetime import datetime
import fitz  # PyMuPDF for PDF reading
from langchain_groq import ChatGroq
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

    # Groq Configuration (No more OpenAI!)
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    SUMMARY_MAX_TOKENS = int(os.getenv("SUMMARY_MAX_TOKENS", "300"))
    SUMMARY_TEMPERATURE = float(os.getenv("SUMMARY_TEMPERATURE", "0.5"))

    # Data folder
    DATA_FOLDER = os.getenv("DATA_FOLDER", "../data")

    DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"

# ============================================================================
# PDF READER
# ============================================================================
class PDFReader:
    """Read and extract text from PDF files"""

    @staticmethod
    def extract_text(pdf_path: str) -> str:
        """Extract text from PDF file"""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page_num in range(len(doc)):
                page = doc[page_num]
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            print(f"❌ Error reading PDF {pdf_path}: {e}")
            return ""

    @staticmethod
    def get_pdf_files(folder: str) -> List[Tuple[str, str]]:
        """Get all PDF files from folder"""
        try:
            pdf_files = glob.glob(os.path.join(folder, "*.pdf"))
            pdf_files.sort()

            result = []
            for pdf_path in pdf_files:
                filename = os.path.basename(pdf_path)
                result.append((pdf_path, filename))

            return result
        except Exception as e:
            print(f"❌ Error reading folder {folder}: {e}")
            return []

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

    def create_tables(self):
        """Create necessary database tables"""
        queries = [
            "CREATE EXTENSION IF NOT EXISTS vector;",
            """
            CREATE TABLE IF NOT EXISTS documents (
                id SERIAL PRIMARY KEY,
                filename TEXT UNIQUE NOT NULL,
                file_size INTEGER,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS document_summaries (
                id SERIAL PRIMARY KEY,
                document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
                summary_text TEXT,
                word_count INTEGER,
                UNIQUE(document_id)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS summary_embeddings (
                id SERIAL PRIMARY KEY,
                summary_id INTEGER REFERENCES document_summaries(id) ON DELETE CASCADE,
                embedding vector(384),
                UNIQUE(summary_id)
            );
            """
        ]
        
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                for query in queries:
                    cur.execute(query)
                conn.commit()
                if self.config.DEBUG_MODE:
                    print("✅ Database tables created successfully")
        except psycopg2.Error as e:
            conn.rollback()
            print(f"❌ Failed to create tables: {e}")
            raise
        finally:
            self.return_connection(conn)

    def execute_update(self, query: str, params: tuple = None) -> bool:
        """Execute INSERT/UPDATE/DELETE"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params or ())
            conn.commit()
            return True
        except psycopg2.Error as e:
            conn.rollback()
            print(f"❌ Update error: {e}")
            return False
        finally:
            cursor.close()
            self.return_connection(conn)

# ============================================================================
# LLM SUMMARIZER (Groq)
# ============================================================================
class GroqSummarizer:
    """Creates document summaries using Groq LLM"""

    def __init__(self, config: Config):
        self.config = config

        if not config.GROQ_API_KEY:
            print("❌ GROQ_API_KEY not set in .env")
            raise ValueError("GROQ_API_KEY required")

        try:
            self.llm = ChatGroq(
                model_name=config.GROQ_MODEL,
                groq_api_key=config.GROQ_API_KEY,
                temperature=config.SUMMARY_TEMPERATURE,
                max_tokens=config.SUMMARY_MAX_TOKENS
            )
            if config.DEBUG_MODE:
                print(f"✅ Groq LLM initialized: {config.GROQ_MODEL}")
        except Exception as e:
            print(f"❌ Groq initialization failed: {e}")
            raise

    def summarize(self, text: str) -> str:
        """Summarize document using Groq"""
        try:
            # Truncate text if too long (Groq has context limits)
            max_input_chars = 4000
            text_to_summarize = text[:max_input_chars]

            messages = [
                SystemMessage(
                    content="You are a technical document summarizer. Summarize focusing on: 1) Main services/products, 2) Key requirements, 3) Important constraints, 4) Timeline/pricing. Keep concise and structured."
                ),
                HumanMessage(
                    content=f"Summarize this RFQ document in {self.config.SUMMARY_MAX_TOKENS} tokens:\n\n{text_to_summarize}"
                )
            ]

            response = self.llm.invoke(messages)
            summary = response.content

            if self.config.DEBUG_MODE:
                print(f"✅ Groq summary: {len(summary.split())} words")

            return summary
        except Exception as e:
            print(f"⚠️  Groq summarization failed: {e}. Using fallback.")
            return self._fallback_summary(text)

    def _fallback_summary(self, text: str) -> str:
        """Fallback: First N sentences"""
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        summary = '. '.join(sentences[:15])
        if self.config.DEBUG_MODE:
            print(f"✅ Fallback summary: {len(summary.split())} words")
        return summary

# ============================================================================
# EMBEDDING INDEXER
# ============================================================================
class EmbeddingIndexer:
    """
    MAIN CLASS: Extract → Summarize → Embed → Store

    This is the complete indexing pipeline:
    1. Extract text from PDF
    2. Summarize with Groq LLM
    3. Create embedding with SentenceTransformer
    4. Store in pgvector
    """

    def __init__(self, db_manager: DatabaseManager, config: Config):
        self.db = db_manager
        self.config = config
        self.embedding_model = SentenceTransformer(config.EMBEDDING_MODEL)
        self.summarizer = GroqSummarizer(config)

        if config.DEBUG_MODE:
            print(f"✅ Embedding model loaded: {config.EMBEDDING_MODEL}")

    def index_unprocessed_documents(self) -> int:
        """
        Index documents from 'documents' table that haven't been summarized yet
        """
        # Fetch documents that don't have a summary
        print(f"\n📝 Checking for unprocessed documents in database...")
        
        pending_docs = self.db.execute_query(
            """
            SELECT d.id, d.filename, d.file_content 
            FROM documents d
            LEFT JOIN document_summaries ds ON d.id = ds.document_id
            WHERE ds.id IS NULL
            """
        )

        if not pending_docs:
            print("✅ All documents in database are already processed.")
            return 0

        print(f"\n📁 Found {len(pending_docs)} unprocessed documents")

        success_count = 0
        for doc_id, filename, file_content in pending_docs:
            if self.index_db_document(doc_id, filename, bytes(file_content)):
                success_count += 1
            else:
                print(f"❌ Failed to process {filename}")

        return success_count

    def index_db_document(self, doc_id: int, filename: str, file_content: bytes) -> bool:
        """
        Index a document directly from binary content (from DB)
        """
        try:
            print(f"\n📄 Indexing: {filename} (ID: {doc_id})")

            # ================================================================
            # STEP 0: EXTRACT TEXT FROM BYTES
            # ================================================================
            print("   Step 0/3: Extracting text from binary...")
            
            # Use fitz to open from bytes
            doc = fitz.open(stream=file_content, filetype="pdf")
            full_text = ""
            for page in doc:
                full_text += page.get_text()
            doc.close()

            if not full_text or len(full_text.strip()) < 50:
                print(f"   ❌ No text extracted from PDF")
                return False

            text_length = len(full_text.split())
            print(f"   ✅ Extracted: {text_length} words")

            # ================================================================
            # STEP 1: SUMMARIZE (Groq LLM)
            # ================================================================
            print("   Step 1/3: Creating summary with Groq...")
            summary = self.summarizer.summarize(full_text)
            print(f"   ✅ Summary: {len(summary.split())} words")

            # ================================================================
            # STEP 2: EMBED (SentenceTransformer)
            # ================================================================
            print("   Step 2/3: Creating embedding...")
            summary_embedding = self.embedding_model.encode(summary)
            # Result: array of 384 numbers
            embedding_str = str(summary_embedding.tolist())
            print(f"   ✅ Embedding: {len(summary_embedding)} dimensions")

            # ================================================================
            # STEP 3: STORE IN PGVECTOR
            # ================================================================
            print("   Step 3/3: Storing in pgvector...")
            
            # Insert summary
            summary_stored = self.db.execute_update(
                """
                INSERT INTO document_summaries 
                (document_id, summary_text, word_count)
                VALUES (%s, %s, %s)
                ON CONFLICT (document_id) DO UPDATE 
                SET summary_text = EXCLUDED.summary_text,
                    word_count = EXCLUDED.word_count
                """,
                (doc_id, summary, len(summary.split()))
            )

            if not summary_stored:
                print(f"   ❌ Failed to store summary")
                return False

            # Get summary ID
            summary_id_result = self.db.execute_query_single(
                "SELECT id FROM document_summaries WHERE document_id = %s",
                (doc_id,)
            )

            if not summary_id_result:
                print(f"   ❌ Failed to retrieve summary ID")
                return False

            summary_id = summary_id_result[0]

            # Store embedding in pgvector
            embedding_stored = self.db.execute_update(
                """
                INSERT INTO summary_embeddings (summary_id, embedding)
                VALUES (%s, %s)
                ON CONFLICT (summary_id) DO UPDATE 
                SET embedding = EXCLUDED.embedding
                """,
                (summary_id, embedding_str)
            )

            if not embedding_stored:
                print(f"   ❌ Failed to store embedding")
                return False

            print(f"   ✅ Stored in pgvector")
            return True

        except Exception as e:
            print(f"   ❌ Indexing error: {e}")
            if self.config.DEBUG_MODE:
                import traceback
                traceback.print_exc()
            return False

    def index_pdf_document(self, pdf_path: str, filename: str) -> bool:
        """
        ⭐ MAIN INDEXING FUNCTION FOR PDF ⭐

        STEP 0: Extract text from PDF
        STEP 1: Summarize (Groq LLM)
        STEP 2: Embed (SentenceTransformer)
        STEP 3: Store in pgvector
        """

        try:
            print(f"\n📄 Indexing: {filename}")

            # ================================================================
            # STEP 0: EXTRACT TEXT FROM PDF
            # ================================================================
            print("   Step 0/3: Extracting text from PDF...")
            full_text = PDFReader.extract_text(pdf_path)

            if not full_text or len(full_text.strip()) < 50:
                print(f"   ❌ No text extracted from PDF")
                return False

            text_length = len(full_text.split())
            print(f"   ✅ Extracted: {text_length} words")

            # Read binary content for storage
            with open(pdf_path, 'rb') as f:
                file_content_bytes = f.read()

            # ================================================================
            # STEP 1: SUMMARIZE (Groq LLM)
            # ================================================================
            print("   Step 1/3: Creating summary with Groq...")
            summary = self.summarizer.summarize(full_text)
            print(f"   ✅ Summary: {len(summary.split())} words")

            # ================================================================
            # STEP 2: EMBED (SentenceTransformer)
            # ================================================================
            print("   Step 2/3: Creating embedding...")
            summary_embedding = self.embedding_model.encode(summary)
            # Result: array of 384 numbers
            embedding_str = str(summary_embedding.tolist())
            print(f"   ✅ Embedding: {len(summary_embedding)} dimensions")

            # ================================================================
            # STEP 3: STORE IN PGVECTOR
            # ================================================================
            print("   Step 3/3: Storing in pgvector...")

            # Insert document record first
            doc_stored = self.db.execute_update(
                """
                INSERT INTO documents (filename, file_size, file_content, uploaded_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (filename) DO UPDATE 
                SET file_size = EXCLUDED.file_size,
                    file_content = EXCLUDED.file_content,
                    uploaded_at = EXCLUDED.uploaded_at
                """,
                (filename, len(full_text), file_content_bytes, datetime.now())
            )

            if not doc_stored:
                print(f"   ❌ Failed to store document record")
                return False

            # Get document ID
            doc_id_result = self.db.execute_query_single(
                "SELECT id FROM documents WHERE filename = %s",
                (filename,)
            )

            if not doc_id_result:
                print(f"   ❌ Failed to retrieve document ID")
                return False

            doc_id = doc_id_result[0]

            # Insert summary
            summary_stored = self.db.execute_update(
                """
                INSERT INTO document_summaries 
                (document_id, summary_text, word_count)
                VALUES (%s, %s, %s)
                ON CONFLICT (document_id) DO UPDATE 
                SET summary_text = EXCLUDED.summary_text,
                    word_count = EXCLUDED.word_count
                """,
                (doc_id, summary, len(summary.split()))
            )

            if not summary_stored:
                print(f"   ❌ Failed to store summary")
                return False

            # Get summary ID
            summary_id_result = self.db.execute_query_single(
                "SELECT id FROM document_summaries WHERE document_id = %s",
                (doc_id,)
            )

            if not summary_id_result:
                print(f"   ❌ Failed to retrieve summary ID")
                return False

            summary_id = summary_id_result[0]

            # Store embedding in pgvector
            embedding_stored = self.db.execute_update(
                """
                INSERT INTO summary_embeddings (summary_id, embedding)
                VALUES (%s, %s)
                ON CONFLICT (summary_id) DO UPDATE 
                SET embedding = EXCLUDED.embedding
                """,
                (summary_id, embedding_str)
            )

            if not embedding_stored:
                print(f"   ❌ Failed to store embedding")
                return False

            print(f"   ✅ Stored in pgvector")
            print(f"   ✅ Document indexed successfully!\n")

            return True

        except Exception as e:
            print(f"   ❌ Indexing error: {e}")
            if self.config.DEBUG_MODE:
                import traceback
                traceback.print_exc()
            return False

    def index_pdf_folder(self, folder: str) -> int:
        """
        Index all PDF files in a folder

        Input: folder path (e.g., "data")
        Returns: Number of successfully indexed documents
        """
        pdf_files = PDFReader.get_pdf_files(folder)

        if not pdf_files:
            print(f"❌ No PDF files found in {folder}")
            return 0

        print(f"\n📁 Found {len(pdf_files)} PDF files in {folder}")

        success_count = 0
        for pdf_path, filename in pdf_files:
            if self.index_pdf_document(pdf_path, filename):
                success_count += 1

        return success_count

# ============================================================================
# MAIN APPLICATION
# ============================================================================
class IndexingApp:
    """Main indexing application"""

    def __init__(self, config: Config):
        self.config = config
        self.db_manager = DatabaseManager(config)
        self.indexer = EmbeddingIndexer(self.db_manager, config)
        self.db_manager.create_tables()

    def run(self):
        """Run indexing from data folder"""

        print("\n" + "="*70)
        print("PDF INDEXING - Extract → Summarize → Embed → Store")
        print("="*70)
        print("\nConfiguration:")
        print(f"  Database: {self.config.POSTGRES_HOST}:{self.config.POSTGRES_PORT}")
        print(f"  Embedding Model: {self.config.EMBEDDING_MODEL}")
        print(f"  LLM Model: {self.config.GROQ_MODEL}")
        print(f"  Data Folder: {self.config.DATA_FOLDER}")
        print(f"  Debug Mode: {self.config.DEBUG_MODE}")

        # Index pending documents
        print(f"\n📝 Checking for unprocessed documents in database...\n")
        success = self.indexer.index_unprocessed_documents()

        print("\n" + "="*70)
        print(f"INDEXING COMPLETE: {success} new documents processed")
        print("="*70)

        # Show what's in database
        self.show_indexed_documents()

    def show_indexed_documents(self):
        """Show all indexed documents in database"""
        print("\n📊 INDEXED DOCUMENTS IN PGVECTOR:\n")

        results = self.db_manager.execute_query(
            """
            SELECT 
                ds.id,
                d.filename,
                d.file_size,
                ds.word_count,
                SUBSTRING(ds.summary_text, 1, 100) as preview,
                (SELECT COUNT(*) FROM summary_embeddings WHERE summary_id = ds.id) as has_embedding
            FROM document_summaries ds
            JOIN documents d ON ds.document_id = d.id
            ORDER BY ds.id
            """
        )

        if not results:
            print("❌ No documents indexed yet.")
            return

        for idx, (summary_id, filename, file_size, word_count, preview, has_embedding) in enumerate(results, 1):
            embedding_status = "✅ Yes" if has_embedding else "❌ No"
            print(f"{idx}. {filename}")
            print(f"   Summary ID: {summary_id}")
            print(f"   Original Size: {file_size} characters")
            print(f"   Summary Words: {word_count}")
            print(f"   Embedding: {embedding_status}")
            print(f"   Preview: {preview}...")
            print()

    def cleanup(self):
        """Cleanup resources"""
        self.db_manager.close_all()

# ============================================================================
# ENTRY POINT
# ============================================================================
def main():
    config = Config()

    try:
        app = IndexingApp(config)
        app.run()
        app.cleanup()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        if config.DEBUG_MODE:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()