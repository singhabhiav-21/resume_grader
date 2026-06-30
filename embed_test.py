import chromadb

from initial import embeddeings
from sentence_transformers import SentenceTransformer

from sentence_transformers import util

model = SentenceTransformer("all-MiniLM-L6-v2")


emb1= model.encode("Built and deployed Docker containers for a FastAPI application")
emb2 = model.encode("Implemented CI/CD pipeline with GitHub Actions")
client = chromadb.Client()

collection = client.create_collection("cv_test")

collection.add(
    documents=["Built and deployed Docker containers for a FastAPI application", "Implemented CI/CD pipeline with GitHub Actions"],
    embeddings=[emb1.tolist(), emb2.tolist()],
    ids=['chunk_1', 'chunk_2']
)

query = model.encode("Experience with Docker").tolist()
results = collection.query(
    query_embeddings=[query],
    n_results=2
)

print(results['documents'])
print(results['distances'])
print(results['ids'])
