from sentence_transformers import SentenceTransformer
from app.chroma_client import client

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


def chunk_embedder(chunks: list[dict], collection):
    texts = [chunk["text"] for chunk in chunks]
    ids = [chunk["id"] for chunk in chunks]
    metadata = [{"category": chunk["category"]} for chunk in chunks]
    embeddings = model.encode(texts, normalize_embeddings=True).tolist()
    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadata
    )


def create_collection(c, name):
    try:
        c.delete_collection(name)
    except:
        pass
    return c.create_collection(name, metadata={"hnsw:space": "cosine"})


def create_resume_collection(job_id: str, chunks: list[dict]):
    collection = create_collection(client, f"resume_{job_id}")
    chunk_embedder(chunks, collection)
    return collection


def create_jd_collection(job_id: str, chunks: list[dict]):
    collection = create_collection(client, f"jd_{job_id}")
    chunk_embedder(chunks, collection)
    return collection

