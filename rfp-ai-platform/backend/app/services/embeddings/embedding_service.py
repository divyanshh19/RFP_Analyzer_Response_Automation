from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

# We use ChromaDB's highly optimized local embedding model (all-MiniLM-L6-v2 via ONNX)
# This completely bypasses all API key requirements, permissions, and network errors!
ef = DefaultEmbeddingFunction()

def get_embedding(text: str, model: str = "local", is_query: bool = False) -> list[float]:
    """Generates a single vector embedding locally."""
    clean_text = text.replace("\n", " ")
    return ef([clean_text])[0]

def get_embeddings_batch(texts: list[str], model: str = "local") -> list[list[float]]:
    """Generates embeddings for a batch of text chunks simultaneously locally."""
    cleaned_texts = [text.replace("\n", " ") for text in texts]
    return ef(cleaned_texts)
