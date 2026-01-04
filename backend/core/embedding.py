from sentence_transformers import SentenceTransformer
from settings import settings

model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)

def get_embedding(text: str):
    return model.encode(text).tolist()
