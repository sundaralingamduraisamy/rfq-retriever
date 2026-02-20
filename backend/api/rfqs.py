import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response, FileResponse
from pydantic import BaseModel
from database import db
from core.text_utils import clean_rfq_text
from render import render_pdf, render_docx

router = APIRouter()

# Models
class SaveRFQModel(BaseModel):
    id: int | None = None
    title: str = "Untitled RFQ"
    content: str
    status: str = "draft"

class UpdateStatusModel(BaseModel):
    status: str

class ExportRequest(BaseModel):
    content: str

# Constants
EXPORT_DIR = "exports"
os.makedirs(EXPORT_DIR, exist_ok=True)

# ----------------------------------------------------------------
# RFQ Management & Export
# ----------------------------------------------------------------

@router.patch("/rfqs/{rfq_id}/status")
def update_rfq_status(rfq_id: int, data: UpdateStatusModel):
    """Update only the status of an RFQ"""
    if not db:
        raise HTTPException(500, "Database connection failed")
        
    rows_affected = db.execute_update(
        "UPDATE generated_rfqs SET status = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
        (data.status, rfq_id)
    )
    
    if rows_affected <= 0:
        raise HTTPException(404, "RFQ not found")
        
    return {"status": "updated", "id": rfq_id, "new_status": data.status}

@router.post("/rfqs/save")
def save_rfq(data: SaveRFQModel):
    """Save or Update RFQ in DB"""
    if not db:
        raise HTTPException(500, "Database connection failed")

    try:
        if data.id:
            # Update existing
            rows_affected = db.execute_update(
                """
                UPDATE generated_rfqs 
                SET filename = %s, content = %s, status = %s, updated_at = CURRENT_TIMESTAMP 
                WHERE id = %s
                """,
                (data.title, data.content, data.status, data.id)
            )
            
            if rows_affected > 0:
                return {"status": "updated", "id": data.id, "title": data.title}
            else:
                pass # Fall through to insert new if update failed because ID doesn't exist
        
        # Insert new
        row = db.execute_insert_returning(
            """
            INSERT INTO generated_rfqs (filename, content, status) 
            VALUES (%s, %s, %s) 
            RETURNING id
            """,
            (data.title, data.content, data.status)
        )
        if not row:
            raise HTTPException(500, "Failed to insert RFQ")
        rfq_id = row[0]
        
        # --- AUTO-INDEXING FOR RETRIEVAL ---
        # Make this RFQ valid for search immediately
        try:
            from core.ingestion import indexer
            # Create a virtual filename for the index
            virtual_filename = f"Generated_RFQ_{rfq_id}_{data.title}.md"
            
            # Index content (as bytes for consistency)
            indexer.index_document(virtual_filename, data.content.encode('utf-8'), category="Generated RFQ")
        except Exception as idx_err:
            pass
        # -----------------------------------

        return {"status": "created", "id": rfq_id, "title": data.title}

    except Exception as e:
        raise HTTPException(500, f"Save failed: {str(e)}")


@router.get("/rfqs")
def get_rfqs():
    """List all generated RFQs from DB"""
    if not db:
        raise HTTPException(500, "Database connection failed")
    
    rows = db.execute_query("SELECT id, filename, status, updated_at, created_at FROM generated_rfqs ORDER BY updated_at DESC")
    
    # Format for frontend
    results = []
    for r in rows:
        results.append({
            "id": r[0],
            "title": r[1],
            "status": r[2],
            "updated_at": r[3].isoformat() + "Z" if r[3] else None,
            "created_at": r[4].isoformat() + "Z" if r[4] else None
        })
        
    return {"rfqs": results}


@router.get("/rfqs/{rfq_id}")
def get_rfq_detail(rfq_id: int):
    """Get content of specific RFQ for editing"""
    if not db:
        raise HTTPException(500, "Database connection failed")
        
    row = db.execute_query_single("SELECT id, filename, content, status FROM generated_rfqs WHERE id = %s", (rfq_id,))
    
    if not row:
        raise HTTPException(404, "RFQ not found")
        
    return {
        "id": row[0], 
        "title": row[1], 
        "content": row[2], 
        "status": row[3]
    }
    
@router.delete("/rfqs/{rfq_id}")
def delete_rfq_db(rfq_id: int):
    """Delete RFQ from DB and its corresponding index in the document library"""
    if not db:
        raise HTTPException(500, "Database connection failed")

    try:
        # --- SYNC: Find and delete the indexed document version too ---
        # Pattern: Generated_RFQ_123_*.md
        doc_match = db.execute_query_single(
            "SELECT id, filename FROM documents WHERE filename LIKE %s", 
            (f"Generated_RFQ_{rfq_id}_%",)
        )
        if doc_match:
            doc_id, doc_name = doc_match
            db.execute_update("DELETE FROM documents WHERE id = %s", (doc_id,))
        # ---------------------------------------------------------------

        # Delete the main RFQ record
        success = db.execute_update("DELETE FROM generated_rfqs WHERE id = %s", (rfq_id,))
        if success:
            return {"status": "deleted", "id": rfq_id}
        else:
            raise HTTPException(404, "RFQ not found")
    except Exception as e:
        raise HTTPException(500, f"Deletion failed: {str(e)}")

@router.get("/rfqs/{rfq_id}/pdf")
def get_rfq_pdf(rfq_id: int):
    """Generate and Serve PDF for an RFQ"""
    if not db:
        raise HTTPException(500, "Database connection failed")
        
    row = db.execute_query_single("SELECT filename, content FROM generated_rfqs WHERE id = %s", (rfq_id,))
    
    if not row:
        raise HTTPException(404, "RFQ not found")
        
    title, content = row
    clean_content = clean_rfq_text(content)
    
    # Render PDF
    rfq_data = {"name": title, "domain": "Automobile", "body": clean_content}
    file_bytes = render_pdf(rfq_data, 1)
    
    filename = f"{title.replace(' ', '_')}.pdf"
    
    return Response(
        content=file_bytes, 
        media_type="application/pdf", 
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@router.post("/export/pdf")
async def export_pdf(data: ExportRequest):
    """Export RFQ as PDF"""
    clean = clean_rfq_text(data.content)
    
    rfq = {"name": "CUSTOM_RFQ", "domain": "Automobile", "body": clean}
    file_bytes = render_pdf(rfq, 1)
    
    path = os.path.join(EXPORT_DIR, "RFQ_Final.pdf")
    open(path, "wb").write(file_bytes)
    
    return FileResponse(path, media_type="application/pdf", filename="RFQ_Final.pdf")


@router.post("/export/docx")
async def export_docx(data: ExportRequest):
    """Export RFQ as DOCX"""
    clean = clean_rfq_text(data.content)
    
    rfq = {"name": "CUSTOM_RFQ", "domain": "Automobile", "body": clean}
    file_bytes = render_docx(rfq, 1)
    
    path = os.path.join(EXPORT_DIR, "RFQ_Final.docx")
    open(path, "wb").write(file_bytes)
    
    return FileResponse(path, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", filename="RFQ_Final.docx")
