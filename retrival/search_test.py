import os
import sys
import chromadb
from chromadb.config import Settings
from embeddings import EmbeddingModel

# Add retrival folder to Python path so we can import build_vectordb.py
sys.path.append("retrival")
from build_vectordb import main as build_db  # Import the build function

# ---------- CONFIG ----------
CHROMA_DIR = "chroma_db"
COLLECTION_NAME = "ai_agent_kb"
TOP_K = 5
# ----------------------------

def main():
    print("📦 Loading Chroma DB...")

    client = chromadb.Client(
        Settings(persist_directory=CHROMA_DIR, anonymized_telemetry=False)
    )

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )

    count = collection.count()
    print(f"📊 Collection has {count} chunks")

    # Auto-build DB if empty
    if count == 0:
        print("❌ No data found. Building Chroma DB automatically...")
        build_db()  # Call the build function directly
        # Reload collection
        client = chromadb.Client(
            Settings(persist_directory=CHROMA_DIR, anonymized_telemetry=False)
        )
        collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
        count = collection.count()
        print(f"📊 Collection now has {count} chunks")
        if count == 0:
            print("❌ Failed to build DB. Check your build_vectordb.py script.")
            return

    embedder = EmbeddingModel()

    while True:
        query = input("\n🔎 Enter query (or 'exit'): ").strip()
        if query.lower() == "exit":
            break

        # Embed the query
        q_embedding = embedder.embed_query(query)

        # Search top K results
        results = collection.query(
            query_embeddings=[q_embedding.tolist()],
            n_results=TOP_K
        )

        if not results["documents"][0]:
            print("⚠️ No results found.")
            continue

        print("\n📄 Results:")
        for i in range(len(results["documents"][0])):
            print(f"\n#{i + 1}")
            print("Score:", results["distances"][0][i])
            print("Metadata:", results["metadatas"][0][i])
            print("Chunk:\n", results["documents"][0][i])

if __name__ == "__main__":
    main()
