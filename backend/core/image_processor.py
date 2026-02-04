import io
import torch
import fitz  # PyMuPDF
from PIL import Image
from transformers import AutoModel, AutoProcessor
from database import db
from settings import settings
import json

# Global Load for Models (Lazy loading)
_active_model = None
_active_processor = None
_model_type = None # "jina" or "clip"

def get_model():
    global _active_model, _active_processor, _model_type
    if _active_model is not None:
        return _active_model, _active_processor, _model_type

    # Attempt 1: JinaCLIP
    try:
        print("🚀 Attempting to load JinaCLIP (jinaai/jina-clip-v1)...")
        from transformers import AutoModel, AutoProcessor
        # Forcing use_safetensors=True to bypass pickle security checks in newer torch
        _active_model = AutoModel.from_pretrained("jinaai/jina-clip-v1", trust_remote_code=True, use_safetensors=True, token=settings.HUGGINGFACE_TOKEN)
        _active_model = _active_model.float() # Force float32 for CPU compatibility
        _active_processor = AutoProcessor.from_pretrained("jinaai/jina-clip-v1", trust_remote_code=True, token=settings.HUGGINGFACE_TOKEN)
        _model_type = "jina"
        print("✅ JinaCLIP loaded successfully.")
        return _active_model, _active_processor, _model_type
    except Exception as e:
        print(f"⚠️ JinaCLIP load failed: {e}. Falling back to standard CLIP...")

    # Attempt 2: Standard CLIP (More likely to be cached or smaller)
    try:
        from transformers import CLIPModel, CLIPProcessor
        print("🚀 Loading fallback CLIP (openai/clip-vit-base-patch32)...")
        # Forcing use_safetensors=True to bypass pickle security checks
        _active_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32", use_safetensors=True)
        _active_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        _model_type = "clip"
        print("✅ Fallback CLIP loaded successfully.")
        return _active_model, _active_processor, _model_type
    except Exception as e:
        print(f"❌ All CLIP models failed to load: {e}")
        raise RuntimeError(f"No image classification model available. Error: {e}")

class ImageProcessor:
    def __init__(self):
        # Slightly more descriptive labels for better CLIP matching
        self.target_labels = [
            "a technical diagram of a car part", 
            "an automobile engine", 
            "a vehicle component", 
            "a car brake system", 
            "an automotive assembly",
            "a car interior",
            "a vehicle chassis"
        ]
        self.negative_labels = ["a person", "a landscape", "nature", "food", "text only", "a building", "an animal", "furniture"]

    def is_automobile_related(self, pil_image: Image.Image) -> tuple[bool, str, float]:
        """Verify if image is car-related using available model"""
        model, processor, mod_type = get_model()
        
        labels = self.target_labels + self.negative_labels
        try:
            inputs = processor(text=labels, images=pil_image, return_tensors="pt", padding=True)
            with torch.no_grad():
                outputs = model(**inputs)
            logits_per_image = outputs.logits_per_image
        except Exception as e:
            print(f"   ❌ JinaCLIP Inference Error: {e}")
            return False, "Error", 0.0
        probs = logits_per_image.softmax(dim=1)
        
        # Get highest probability label
        max_idx = torch.argmax(probs).item()
        best_label = labels[max_idx]
        confidence = probs[0][max_idx].item()

        # Higher sensitivity for technical diagrams which often have lower confidence
        threshold = 0.15 if mod_type == "jina" else 0.10
        is_related = best_label in self.target_labels and confidence > threshold
        return is_related, best_label, confidence

    def get_image_embedding(self, pil_image: Image.Image) -> list:
        """Get vector embedding for the image"""
        model, processor, mod_type = get_model()
        inputs = processor(images=pil_image, return_tensors="pt")
        with torch.no_grad():
            if mod_type == "jina":
                image_features = model.get_image_features(**inputs)
            else:
                image_features = model.get_image_features(**inputs)
        return image_features[0].tolist()

    def process_content(self, file_content: bytes, file_ext: str) -> list[dict]:
        """Generic processor for both PDF and DOCX that returns all images with status"""
        all_images = []
        
        if file_ext == 'pdf':
            doc = fitz.open(stream=file_content, filetype="pdf")
            print(f"DEBUG: Processing PDF with {len(doc)} pages")
            for page_index in range(len(doc)):
                page = doc[page_index]
                image_list = page.get_images(full=True)
                print(f"DEBUG: Page {page_index+1} found {len(image_list)} images")
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    all_images.append({
                        "data": base_image["image"],
                        "page": page_index + 1,
                        "format": base_image["ext"]
                    })
            doc.close()
        elif file_ext == 'docx':
            import docx
            doc = docx.Document(io.BytesIO(file_content))
            print("DEBUG: Processing DOCX")
            for rel in doc.part.rels.values():
                if "image" in rel.target_ref:
                    image_bytes = rel.target_part.blob
                    all_images.append({
                        "data": image_bytes,
                        "page": 0,
                        "format": "docx-img"
                    })

        print(f"DEBUG: Total raw images extracted: {len(all_images)}")
        results = []
        for i, img in enumerate(all_images):
            try:
                pil_img = Image.open(io.BytesIO(img["data"]))
                if pil_img.mode != 'RGB':
                    pil_img = pil_img.convert('RGB')

                is_related, label, conf = self.is_automobile_related(pil_img)
                print(f"DEBUG: Image {i+1} -> Label: {label}, Confidence: {conf:.4f}, Approved: {is_related}")
                
                res = {
                    "data": img["data"],
                    "description": label,
                    "is_automobile": is_related,
                    "confidence": conf,
                    "metadata": {
                        "page": img["page"],
                        "format": img["format"],
                        "size": pil_img.size
                    }
                }
                
                if is_related:
                    res["embedding"] = self.get_image_embedding(pil_img)
                
                results.append(res)
            except Exception as e:
                print(f"⚠️ Error processing image: {e}")
        
        return results

    def save_images_to_db(self, document_id: int, images: list[dict]):
        """Save ONLY filtered images and their embeddings to the database"""
        for img in images:
            if not img.get("is_automobile"):
                continue
                
            # 1. Insert Image
            row = db.execute_insert_returning(
                """
                INSERT INTO document_images (document_id, image_data, description, metadata)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (document_id, img["data"], img["description"], json.dumps(img["metadata"]))
            )
            
            if row:
                image_id = row[0]
                # 2. Insert Embedding
                print(f"   [DEBUG] Saving embedding for Image ID {image_id} (Vector Dim: {len(img['embedding'])})")
                success = db.execute_update(
                    """
                    INSERT INTO image_embeddings (image_id, embedding)
                    VALUES (%s, %s::vector)
                    """,
                    (image_id, str(img["embedding"]))
                )
                if not success:
                    print(f"   ❌ FAILED to save embedding for Image ID {image_id}")

# Global instance
image_processor = ImageProcessor()
