"""
rag/indexer.py — Read CSV → embed → save to ChromaDB

The indexer is run ONCE during initial setup, or every time there is an update to the CSV document.

Indexer workflow:
1. Scan all CSV files in the academic_guidelines folder
2. Read each CSV line
3. Combine text columns into a single string (chunk)
4. Embed chunks using sentence-transformers
5. Save vector + original text to ChromaDB
"""

import csv
import os
from pathlib import Path
from typing import List, Dict

import chromadb
from chromadb.utils import embedding_functions

from backend.config import get_settings
from backend.utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)

COLLECTION_NAME = "academic_system"

def get_chroma_client() -> chromadb.PersistentClient:
    """
    Create or connect to a ChromaDB database stored on disk.

    PersistentClient → data stored in a folder (not lost on restart).
    This differs from InMemoryClient, which is lost when the program terminates.

    Returns:
        chromadb.PersistentClient: ChromaDB client
    """
    return chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)

def get_collection(client: chromadb.PersistentClient):
    """
    Get or create a collection in ChromaDB.

    Collection = "container" for vectors — analogous to a table in SQL.
    get_or_create → If it already exists, use it. If not, create a new one.

    The embedding function here uses SentenceTransformer:
    - Model: all-MiniLM-L6-v2
    - Lightweight (80MB), fast, good accuracy for short-medium text
    - Produces a 384-dimensional vector

    Args:
        client: ChromaDB client

    Returns:
        Collection: ChromaDB collection ready to use
    """
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=settings.EMBEDDING_MODEL
    )
    
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"}
    )
    
    return collection

def csv_row_to_chunk(row: Dict, filename: str) -> str:
    """
    Convert a single CSV line into a single text chunk for embedding.

    Concatenation strategy:
    - All text columns are concatenated into a single string
    - Format: "column1: value1. column2: value2...."
    - This provides complete context to the model during retrieval

    Example output:
    "title: Thesis Requirements. content: Students can take thesis...
    category: thesis. tags: thesis, requirements, GPA"

    Args:
        row: a single CSV line as a dict
        filename: CSV file name (for metadata)

    Returns:
        str: text chunk ready to embed
    """
    parts = []
    for key, value in row.items():
        if value and value.strip():
            parts.append(f"{key}: {value.strip()}")
    
    return ". ".join(parts)

def index_csv_files() -> Dict:
    """
    Main indexing function — read all CSV files and insert them into ChromaDB.

    Process:
    1. Scan the RAG_CSV_PATH folder for .csv files
    2. Per file: read all rows
    3. Per row: create a text chunk → generate a unique ID
    4. Batch insert into ChromaDB (more efficient than one at a time)

    Why batch insert?
    → ChromaDB is more efficient when data is inserted all at once
    → Reduces overhead per operation

    Returns:
        dict: indexing results report
        {
            "total_chunks": int,
            "files_processed": list,
            "errors": list
        }
    """
    csv_path = Path(settings.RAG_CSV_PATH)
    
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Folder csv not found: {csv_path}. "
            "Make sure at .env already correct."
        )
    
    csv_files = list(csv_path.glob("*.csv"))
    
    if not csv_files:
        raise FileNotFoundError(
            f"There's not files in folder: {csv_path}"
        )
    
    client = get_chroma_client()
    collection = get_collection(client=client)
    
    total_chunks = 0
    files_processed = []
    errors = []
    
    for csv_file in csv_files:
        logger.info(f"[INDEXER] Processing: {csv_file.name}")
        
        try:
            with open(csv_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            if not rows:
                logger.warning(f"[INDEXER] Files empty: {csv_file.name}")
            
            documents = []
            ids = []
            metadatas = []
            
            for i, row in enumerate(rows):
                chunk = csv_row_to_chunk(row=row, filename=csv_file.name)
                
                if not chunk.strip():
                    continue
                
                chunk_id = f"{csv_file.stem}_{i}"
                
                documents.append(chunk)
                ids.append(chunk_id)
                metadatas.append({
                    "source": csv_file.name,
                    "row_index": i,
                })
            
            if documents:
                collection.upsert(
                    documents=documents,
                    ids=ids,
                    metadatas=metadatas
                )
                total_chunks += len(documents)
                files_processed.append(csv_file.name)
                logger.info(
                    f"[INDEXER] {csv_file.name} successful. "
                    f"{len(documents)} chunks indexing"
                )
        
        except Exception as e:
            error_msg = f"Error at {csv_file.name}: {str(e)}"
            errors.append(error_msg)
            logger.error(f"[INDEXER] {error_msg}")
    
    result = {
        "total_chunks": total_chunks,
        "files_processed": files_processed,
        "errors": errors,
        "chroma_path": str(settings.CHROMA_DB_PATH)
    }
    
    logger.info(f"[INDEXER] Done! Total {total_chunks} chunks index.")
    return result