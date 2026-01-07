from datetime import datetime
from sentence_transformers import SentenceTransformer
from database import db
from settings import settings
import time

from core.embedding_model import get_embedding_model

# Initialize model lazily in functions
# embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)

def hybrid_search(query: str):
    """
    Search for documents using Vector Similarity on Summaries
    """
    start_time = time.time()
    
    if not db:
        print("❌ Database not initialized")
        return []

    try:
        # 1. Encode Query
        model = get_embedding_model()
        query_vec = model.encode(query)
        embedding_str = str(query_vec.tolist())

        # 2. Search in DB (Cosine Distance)
        # We search document_summaries via summary_embeddings table
        # 1 - (embedding <=> query) = Cosine Similarity
        sql_query = """
            SELECT 
                d.filename,
                ds.summary_text,
                1 - (se.embedding <=> %s::vector) as similarity,
                ds.id as summary_id
            FROM summary_embeddings se
            JOIN document_summaries ds ON se.summary_id = ds.id
            JOIN documents d ON ds.document_id = d.id
            ORDER BY similarity DESC
            LIMIT %s
        """

        results = db.execute_query(sql_query, (embedding_str, settings.RETRIEVER_TOP_K))
        
        # 3. Format Results
        formatted_results = []
        for r in results:
            filename = r[0]
            summary_text = r[1]
            similarity = float(r[2])
            summary_id = r[3]

            formatted_results.append({
                "source": {
                    "file": filename,
                    "chunk_id": summary_id # Map summary_id to "chunk_id" for compatibility
                },
                "text": summary_text, # The AI sees the summary
                "relevance": round(similarity * 100, 2)
            })

        print(f"✅ Search found {len(formatted_results)} results in {(time.time() - start_time)*1000:.1f}ms")
        return formatted_results

    except Exception as e:
        print(f"❌ Search error: {e}")
        return []

def get_full_rfq(filename: str) -> str:
    """
    Retrieve full text content from DB for a given filename.
    Supports both PDF and DOCX files.
    """
    if not db:
        return "Database not connection."

    try:
        # Fetch binary content
        row = db.execute_query_single("SELECT file_content FROM documents WHERE filename = %s", (filename,))
        if not row:
            return "Document not found in database."
        
        file_content = bytes(row[0])
        file_ext = filename.split('.')[-1].lower()
        
        # Extract Text based on file type
        if file_ext == 'pdf':
            import fitz
            doc = fitz.open(stream=file_content, filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            
        elif file_ext == 'docx':
            import docx
            import io
            doc = docx.Document(io.BytesIO(file_content))
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        text += cell.text + " "
                text += "\n"
        else:
            return f"Unsupported file type: {file_ext}"
            
        return text.strip()

    except Exception as e:
        print(f"❌ Error reading full document: {e}")
        return "Error reading document."
