from sentence_transformers import SentenceTransformer
from settings import settings

_embedding_model = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        print("⏳ Loading Embedding Model...")
        _embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
        print("✅ Embedding Model Loaded.")
    return _embedding_model
