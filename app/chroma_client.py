import os
import chromadb
from dotenv import load_dotenv

load_dotenv()

client = chromadb.PersistentClient(path=os.getenv("CHROMA_PATH"))
