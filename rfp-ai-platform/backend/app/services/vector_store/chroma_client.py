import chromadb
from chromadb.config import Settings
from app.core.config import settings

class ChromaManager:
    def __init__(self):
        import os
        chroma_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "chroma_db")
        os.makedirs(chroma_path, exist_ok=True)
        # Fallback to local persistent ChromaDB so we don't require Docker
        self.client = chromadb.PersistentClient(path=chroma_path)
        
        # We use a single unified collection and rely on metadata filtering
        # (e.g., document_type="KNOWLEDGE_BASE" vs "RFP") for semantic separation
        self.collection = self.client.get_or_create_collection(
            name="rfp_knowledge_base_local_v2",
            metadata={"hnsw:space": "cosine"} # Cosine similarity is standard for OpenAI embeddings
        )

    def get_collection(self):
        return self.collection

# Singleton instance
chroma_manager = ChromaManager()
