import os
import chromadb
from loaders import load_pdf
from Preprocessing import preprocess_text
from chunker import build_chunks
from embeddings import EmbeddingModel

# ---------- CONFIG ----------
PDF_PATH = r"C:\Users\Lenovo\OneDrive - Alexandria National University\Desktop\Revy_AI2\retrival\AI Agent Knowledge Base.pdf"
SOURCE_NAME = "AI Agent Knowledge Base"

CHROMA_DIR = "chroma_db"
COLLECTION_NAME = "ai_agent_kb"
# ----------------------------

def main():
    os.makedirs(CHROMA_DIR, exist_ok=True)

    # ✅ لو الـ DB اتبنت قبل كده، متعملش حاجة
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )

    if collection.count() > 0:
        print(f"✅ Chroma DB already exists with {collection.count()} chunks. Skipping rebuild.")
        return

    print("📄 Loading PDF...")
    raw_text = load_pdf(PDF_PATH)

    print("🧹 Preprocessing text...")
    clean_text = preprocess_text(raw_text)

    print("✂️ Chunking document...")
    chunks = build_chunks(clean_text, source=SOURCE_NAME)

    texts = [c["text"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]
    ids = [c["metadata"]["chunk_id"] for c in chunks]

    print("🧠 Embedding chunks (ONE TIME)...")
    embedder = EmbeddingModel()
    embeddings = embedder.embed_documents(texts)

    print("🗄️ Storing in Chroma DB...")
    collection.add(
        documents=texts,
        embeddings=[e.tolist() for e in embeddings],
        metadatas=metadatas,
        ids=ids
    )

    print(f"✅ Done. Stored {len(texts)} chunks in Chroma at '{CHROMA_DIR}'.")

if __name__ == "__main__":
    main()