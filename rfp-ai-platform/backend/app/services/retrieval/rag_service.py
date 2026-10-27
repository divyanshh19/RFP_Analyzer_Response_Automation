from app.services.vector_store.chroma_client import chroma_manager
from app.services.embeddings import embedding_service
from app.schemas.retrieval import SearchResult

def retrieve_relevant_chunks(query: str, top_k: int = 5, doc_type_filter: str = "KNOWLEDGE_BASE") -> list[SearchResult]:
    # 1. Query preprocessing and embedding (flagged as a query for Gemini optimization)
    query_embedding = embedding_service.get_embedding(query, is_query=True)
    
    # 2. Metadata filtering
    where_clause = {}
    if doc_type_filter:
        where_clause = {"document_type": doc_type_filter}
        
    # 3. Vector search against ChromaDB
    collection = chroma_manager.get_collection()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where_clause,
        include=["documents", "metadatas", "distances"]
    )
    
    # 4. Construct Context Payload
    search_results = []
    if results["ids"] and len(results["ids"][0]) > 0:
        for i in range(len(results["ids"][0])):
            meta = results["metadatas"][0][i]
            
            # Chroma distances for cosine space. Cosine Similarity = 1 - Distance
            distance = results["distances"][0][i]
            similarity = 1.0 - distance
            
            res = SearchResult(
                chunk_id=results["ids"][0][i],
                text=results["documents"][0][i],
                document_id=meta.get("document_id", ""),
                document_type=meta.get("document_type", ""),
                page_number=meta.get("page_number", 0),
                section_name=meta.get("section_name", ""),
                similarity_score=similarity
            )
            search_results.append(res)
            
    return search_results
