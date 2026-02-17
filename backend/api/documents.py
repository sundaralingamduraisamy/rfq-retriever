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
    """List documents from PostgreSQL with image status"""
    if not db:
        raise HTTPException(500, "Database connection failed")
    
    # Query DB - include count of images
    results = db.execute_query("""
        SELECT d.id, d.filename, d.category, d.file_size, d.uploaded_at,
               (SELECT COUNT(*) FROM document_images di WHERE di.document_id = d.id) as img_count
        FROM documents d
        ORDER BY d.uploaded_at DESC
    """)
    
    files = []
    for row in results:
        doc_id, filename, category, size, uploaded_at, img_count = row
        ext = filename.split(".")[-1].lower() if "." in filename else "unknown"
        
        files.append({
            "id": str(doc_id),
            "name": filename,
            "type": ext,
            "category": category or "General",
            "size": size,
            "uploadedAt": uploaded_at.isoformat() if uploaded_at else "",
            "hasAutomobileImages": img_count > 0,
            "imageCount": img_count,
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
        result = indexer.index_document(file.filename, content, category)
        
        if result["success"]:
            return {
                "filename": file.filename, 
                "status": "Uploaded & Indexed Successfully",
                "image_stats": result.get("image_stats", {})
            }
        else:
             raise HTTPException(500, result.get("error", "Failed to index document"))
             
    except Exception as e:
        print(f"Upload error: {e}")
        raise HTTPException(500, f"Upload failed: {str(e)}")


@router.delete("/documents/{doc_id}")
def delete_document(doc_id: int):
    """Delete document from DB by ID (Cascades to chunks/summaries/images)"""
    if not db:
        raise HTTPException(500, "Database connection failed")
        
    # Check if exists and get filename for sync logic
    exists = db.execute_query_single("SELECT filename FROM documents WHERE id = %s", (doc_id,))
    if not exists:
        raise HTTPException(404, "Document not found")
    
    filename = exists[0]
    print(f"🗑️ Deleting document ID {doc_id} ('{filename}')...")
        
    try:
        # --- SYNC: If this is a generated RFQ, delete its record from generated_rfqs too ---
        import re
        # Pattern: Generated_RFQ_123_Title.md
        match = re.search(r"^Generated_RFQ_(\d+)_", filename)
        if match:
            rfq_id = int(match.group(1))
            print(f"   🔄 Syncing: Deleting related generated_rfq ID {rfq_id}...")
            db.execute_update("DELETE FROM generated_rfqs WHERE id = %s", (rfq_id,))
        # ---------------------------------------------------------------------------------

        # Delete from documents (Cascade handles summaries, embeddings, and images)
        success_count = db.execute_update("DELETE FROM documents WHERE id = %s", (doc_id,))
        
        if success_count > 0:
            print(f"✅ Document {doc_id} and all related embeddings/images deleted.")
            return {"status": "deleted", "filename": filename, "id": doc_id}
        else:
            raise HTTPException(500, "Failed to delete document from database")
    except Exception as e:
        print(f"❌ Error during document deletion (ID: {doc_id}): {e}")
        raise HTTPException(500, f"Database deletion error: {str(e)}")


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
    elif ext in ["md", "txt"]:
         media_type = "text/markdown; charset=utf-8"
         
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
    elif ext in ["md", "txt"]:
         media_type = "text/markdown; charset=utf-8"
         
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

@router.get("/images/{image_id}")
def get_image(image_id: int):
    """Serve binary image data from DB"""
    if not db:
        raise HTTPException(500, "Database connection failed")

    row = db.execute_query_single("SELECT image_data, metadata FROM document_images WHERE id = %s", (image_id,))
    if not row:
        raise HTTPException(404, "Image not found")
    
    image_bytes = bytes(row[0])
    metadata = row[1] or {}
    
    # Try to get mime type from metadata, default to image/png
    mime_type = metadata.get("mime_type", "image/png")
    
    return Response(content=image_bytes, media_type=mime_type)
