"""
routers/ai_agent.py — AI Agent & Indexing Endpoint

Endpoints:
- POST /ask → send a question to the AI ​​Agent
- POST /index → ​​run the indexer (admin only)
- GET /status → check the status of the vector DB
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.database import get_db
from backend.dependencies import get_current_active_mahasiswa, get_current_activate_admin
from backend.models.user import User
from backend.models.mahasiswa import Mahasiswa
from backend.services.ai_agent import process_question
from backend.rag.indexer import index_csv_files, get_chroma_client, get_collection

router = APIRouter()

class AskRequest(BaseModel):
    """Schema for request question to AI Agent."""
    question: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "Apakah UKT saya sudah lunas?"
            }
        }

@router.post(
    "/ask",
    summary="Ask a question to the AI ​​Academic Agent"
)
def ask_agent(
    payload: AskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_mahasiswa)
):
    """
    The AI ​​Agent's primary endpoint.

    Accepts natural language questions and
    returns accurate and personalized answers.

    Example questions:
    - "Have my tuition fees been paid in full?"
    - "What semester am I currently in?"
    - "What are the requirements for completing a thesis?"
    - "What is the procedure for requesting leave?"
    """
    if not payload.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question should not empty."
        )
    
    mahasiswa = db.query(Mahasiswa).filter(
        Mahasiswa.user_id == current_user.id
    ).first()
    
    if not mahasiswa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data student's not found, Call admin."
        )
    
    result = process_question(
        question=payload.question,
        mahasiswa=mahasiswa,
        db=db,
    )
    
    return {
        "question": payload.question,
        "answer": result["answer"],
        "intent": result["intent"],
        "sources": result["sources"],
    }

@router.post(
    "/index",
    summary="Running indexer CSV -> ChromaDB (Admin Only, Just Adin can run this uWu >.<)"
)
def run_indexer(
    current_user: User = Depends(get_current_activate_admin)
):
    """
    Runs the reindexing process for all CSV files into ChromaDB.
    Can only be run by an admin.

    When should this be done?
    - When setting up the system for the first time
    - After updating/additional CSV files
    """
    try:
        result = index_csv_files()
        return {
            "message": "Indexing succesfully.",
            "detail": result
        }
    
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Indexing failed: {str(e)}"
        )

@router.get(
    "/status",
    summary="Check status ChromaDB vector databases."
)
def check_rag_status(
    current_user: User = Depends(get_current_active_mahasiswa)
):
    """
    Checks whether the vector DB is populated and ready to use.
    Useful for debugging when RAG doesn't produce results.
    """
    try:
        client = get_chroma_client()
        collection = get_collection(client)
        count = collection.count()
        
        return {
            "status": "ready" if count > 0 else "empty",
            "total_chunks": count,
            "message": (
                f"Vector DB ready with {count} chunks"
                if count > 0
                else "Vector DB empty - run /index first"
            )
        }
    
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }