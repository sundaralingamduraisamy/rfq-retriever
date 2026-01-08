import os
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import Response
from database import db
from core.ingestion import indexer
from core.retriever import get_full_rfq
from core.text_utils import clean_rfq_text

router = APIRouter()

# ----------------------------------------------------------------
# Document Management (DB Based)
# ----------------------------------------------------------------

@router.get("/documents")
def list_documents():
    """List documents from PostgreSQL"""
    if not db:
        raise HTTPException(500, "Database connection failed")
    
    # Query DB - include category
    results = db.execute_query("""
        SELECT id, filename, category, file_size, uploaded_at 
        FROM documents 
        ORDER BY uploaded_at DESC
    """)
    
    files = []
    for row in results:
        doc_id, filename, category, size, uploaded_at = row
        ext = filename.split(".")[-1].lower() if "." in filename else "unknown"
        
        files.append({
            "id": str(doc_id), # Use DB ID for uniqueness
            "name": filename,
            "type": ext,
            "category": category or "General",  # Default if null
            "size": size,
            "uploadedAt": uploaded_at.isoformat() if uploaded_at else "",
            "relevanceScore": 100
        })
        
    return files

@router.post("/upload")
async def upload_document(file: UploadFile = File(...), category: str = Form("General")):
    """Upload PDF directly to PostgreSQL and Ingest"""
    if not db:
        raise HTTPException(500, "Database connection failed")

    allowed = {".pdf", ".docx"}
    ext = os.path.splitext(file.filename)[1].lower()
    
    if ext not in allowed:
         raise HTTPException(400, f"Invalid file type. Only PDF and DOCX allowed. Got: {ext}")

    try:
        # Read content
        content = await file.read()
        
        # Trigger Indexer with category
        success = indexer.index_document(file.filename, content, category)
        
        if success:
            return {"filename": file.filename, "status": "Uploaded & Indexed Successfully"}
        else:
             raise HTTPException(500, "Failed to index document")
             
    except Exception as e:
        print(f"Upload error: {e}")
        raise HTTPException(500, f"Upload failed: {str(e)}")


@router.delete("/documents/{filename}")
def delete_document(filename: str):
    """Delete document from DB (Cascades to chunks/summaries)"""
    if not db:
        raise HTTPException(500, "Database connection failed")
        
    # Check if exists
    exists = db.execute_query_single("SELECT id FROM documents WHERE filename = %s", (filename,))
    if not exists:
        raise HTTPException(404, "File not found")
        
    # Delete (Cascade should handle children)
    success = db.execute_update("DELETE FROM documents WHERE filename = %s", (filename,))
    
    if success:
        return {"status": "deleted", "filename": filename}
    else:
        raise HTTPException(500, "Failed to delete document")


@router.get("/rfq_pdf/{filename}")
def get_pdf(filename: str):
    """Serve PDF content from DB"""
    if not db:
        raise HTTPException(500, "Database connection failed")

    result = db.execute_query_single("SELECT file_content FROM documents WHERE filename = %s", (filename,))
    
    if not result:
        raise HTTPException(404, "Document not found")
        
    file_bytes = bytes(result[0])
    
    return Response(content=file_bytes, media_type="application/pdf")

@router.get("/rfq_text/{filename}")
def get_rfq_text(filename: str):
    """Get RFQ text content from DB"""
    try:
        row = db.execute_query_single("SELECT file_content FROM documents WHERE filename=%s", (filename,))
        if not row:
            raise HTTPException(404, "Document not found")
            
        # Using get_full_rfq from retriever to reconstruct/fetch text
        text = get_full_rfq(filename)
        return {"text": clean_rfq_text(text)}
    except:
        raise HTTPException(404, "RFQ Text Not Found")

@router.get("/documents/{doc_id}/view")
def view_document_by_id(doc_id: int):
    """Serve raw document content for inline viewing by ID"""
    if not db:
        raise HTTPException(500, "Database connection failed")

    row = db.execute_query_single("SELECT filename, file_content FROM documents WHERE id=%s", (doc_id,))
    if not row:
        raise HTTPException(404, "Document not found")
    
    filename = row[0]
    content = bytes(row[1])
    ext = filename.split('.')[-1].lower()
    
    media_type = "application/pdf"
    if ext in ["docx", "doc"]:
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif ext == "xlsx":
         media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
         
    return Response(content=content, media_type=media_type, headers={"Content-Disposition": "inline"})

@router.get("/documents/view/by-name/{filename}")
def view_document_by_name(filename: str):
    """Serve raw document content for inline viewing by Filename (For Generator)"""
    if not db:
        raise HTTPException(500, "Database connection failed")

    row = db.execute_query_single("SELECT file_content FROM documents WHERE filename=%s", (filename,))
    if not row:
        raise HTTPException(404, "Document not found")
    
    content = bytes(row[0])
    ext = filename.split('.')[-1].lower()
    
    media_type = "application/pdf"
    if ext in ["docx", "doc"]:
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif ext == "xlsx":
         media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
         
    return Response(content=content, media_type=media_type, headers={"Content-Disposition": "inline"})

@router.get("/documents/{doc_id}/download")
def download_document_by_id(doc_id: int):
    """Serve document content for download by ID"""
    if not db:
        raise HTTPException(500, "Database connection failed")

    row = db.execute_query_single("SELECT filename, file_content FROM documents WHERE id=%s", (doc_id,))
    if not row:
        raise HTTPException(404, "Document not found")
    
    filename = row[0]
    content = bytes(row[1])
    ext = filename.split('.')[-1].lower()
    
    media_type = "application/octet-stream" 
    if ext == "pdf": media_type = "application/pdf"
    
    return Response(content=content, media_type=media_type, headers={"Content-Disposition": f'attachment; filename="{filename}"'})
