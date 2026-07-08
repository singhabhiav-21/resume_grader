from sentence_transformers import SentenceTransformer
from jd_extracter import ready_to_embed
from pdf_extractor import pdf_extractor
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


cv = pdf_extractor("sampleq.pdf")
jd = ready_to_embed("jd_test.txt")

cv_collection = create_collection(client, "resume")
jd_collection = create_collection(client, "job_description")

chunk_embedder(cv, cv_collection)
chunk_embedder(jd, jd_collection)

