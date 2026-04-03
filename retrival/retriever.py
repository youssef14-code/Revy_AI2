import chromadb
from retrival.embeddings import EmbeddingModel
from functools import lru_cache

CHROMA_DIR = "chroma_db"        # ← فوق
COLLECTION_NAME = "ai_agent_kb"  # ← فوق

@lru_cache(maxsize=1)
def get_collection():
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    return client.get_collection(COLLECTION_NAME)

class RetrievalService:
    def __init__(self):
        self.collection = get_collection()  # ← من الـ cache
        self.embedder = EmbeddingModel()

    def search(self, query: str, top_k: int = 2) -> str:
        embedding = self.embedder.embed_query(query)
        results = self.collection.query(
            query_embeddings=[embedding.tolist()],
            n_results=top_k
        )
        docs = results["documents"][0]
        summarized = []
        for doc in docs:
            summarized.append(doc[:400])
        return "\n\n".join(summarized)  # ← summarized مش docs