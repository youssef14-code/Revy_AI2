# embeddings.py
from sentence_transformers import SentenceTransformer
from functools import lru_cache

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

@lru_cache(maxsize=1)
def get_model():
    return SentenceTransformer(MODEL_NAME)
class EmbeddingModel:
    def __init__(self):
        self.model = get_model()

    def embed_documents(self, texts):
        texts = [f"passage: {t}" for t in texts]
        return self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=True
        )

    def embed_query(self, query: str):
        query = f"query: {query}"
        return self.model.encode(
            [query],
            normalize_embeddings=True
        )[0]
    
@lru_cache(maxsize=1)
def get_embedding_model():
    return EmbeddingModel()