"""
rag/retriever.py — ChromaDB query to find relevant documents

Retriever = "search engine" that finds the most relevant documents
based on semantic proximity (meaning), not keyword matching.

The difference between semantic search and keyword search:
- Keyword: "thesis" only finds documents containing the word "thesis"
- Semantic: "final project" can also find documents about "thesis"
because their meanings are similar
"""

from typing import List, Dict
import chromadb

from backend.rag.indexer import get_chroma_client, get_collection

from backend.utils.logger import get_logger

logger = get_logger(__name__)

def retrieve_context(
    query: str,
    n_results: int = 3,
) -> List[Dict]:
    """
    Find the most relevant documents from ChromaDB based on the query.

    Internal process:
    1. The query is embedded as a vector (using the same model for indexing).
    2. ChromaDB calculates the cosine distance between the query vector and all vectors in the collection.
    3. Returns n_results of documents with the smallest distance.

    Args:
        query: The user's query
        n_results: The number of documents returned (default 3)
            3 = enough context without overwhelming the Groq context window.

    Returns:
        List[Dict]: A list of relevant documents, each item containing:
        {
            "text": str, the original chunk text
            "source": str, the source CSV file name
            "distance": float number of relevant documents (0=identical, 2=irrelevant)
        }
    """
    client = get_chroma_client()
    collection = get_collection(client=client)
    
    if collection.count() == 0:
        logger.info(f"[RETRIEVER] Collection empty - Running indexer first")
        
    
    try:
        results = collection.query(
            query_texts=[query],
            n_results=min(n_results, collection.count()),
            include=["documents", "metadatas", "distances"]
        )
        
        retrieved = []
        for i, doc in enumerate(results["documents"][0]):
            retrieved.append({
                "text": doc,
                "source": results["metadatas"][0][i].get("source", "unknown"),
                "distance": results["distances"][0][i],
            })
        return retrieved
    
    except Exception as e:
        logger.info(f"[RETRIEVER] Error: {e}")
        return []


def format_context_for_prompt(retrieved_docs: List[Dict]) -> str:
    """
    Combine the found documents into a single context string
    ready to be inserted into the Groq prompt.

    Output format:
    [Source: faq_academic.csv]
    Question: How to... Answer: Students can...

    [Source: panduan_academic.csv]
    Title: Thesis Requirements. Content: ...

    Args:
        retrieved_docs: Output from retrieve_context()

    Returns:
        str: Formatted context ready to be inserted into the prompt
    """
    if not retrieved_docs:
        return "There's not found document relevants."
    
    parts = []
    for doc in retrieved_docs:
        parts.append(
            f"Sumber: {doc['source']}\n{doc['text']}"
        )
    
    return "\n\n".join(parts)