"""
services/ai_agent.py — AI Agent Routing Logic

The agent is responsible for deciding:
1. Can this question be answered from the database? (deterministic)
2. Or should it be searched in the document? (RAG)
3. Or a combination of both?

How the agent "thinks" (intent detection):
We use simple but effective keyword matching.
Why not use LLM to classify intents?
→ Increases latency (1 extra LLM call)
→ Keyword matching is sufficient for limited academic applications
→ More predictable and easier to debug
"""

from sqlalchemy.orm import Session
from typing import Optional

from backend.models.mahasiswa import Mahasiswa
from backend.models.absensi import Absensi, AttendanceStatus
from backend.rag.retriever import retrieve_context, format_context_for_prompt
from backend.rag.groq_client import chat_completion, build_db_prompt, build_rag_prompt
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# INTENT KEYWORDS
DB_INTENT_KEYWORDS = [
    "ukt", "bayar", "lunas", "tunggakan",
    "semester berapa", "semester saya",
    "ipk saya", "nilai saya", "transkrip saya",
    "absensi saya", "kehadiran saya", "berapa kali hadir",
    "data saya", "profil saya", "nim saya",
    "status saya", "aktif",
]

def detect_intent(question: str) -> str:
    """
    Detects whether a question requires DB data or a RAG document.

    How it works:
    - Lowercase the question
    - Check if the DB keyword is present
    - If so → intent = "database"
    - If not → intent = "rag"

    Args:
        question: The user's question

    Returns:
        str: "database" or "rag"
    """
    question_lower = question.lower()
    
    for keyword in DB_INTENT_KEYWORDS:
        if keyword in question_lower:
            return "database"
    
    return "rag"

def get_student_db_context(
    mahasiswa: Mahasiswa,
    db: Session,
    question: str,
) -> dict:
    """
    Fetch relevant student data from PostgreSQL based on the query.

    Not all student data is returned — only the relevant
    to the query. This is for:
    1. Efficiency (not sending excessive data to Groq)
    2. Privacy (not exposing unnecessary data)

    Args:
        student: Student object from DB
        db: database session
        question: user query (to determine what data is relevant)

    Returns:
        dict: relevant student data
    """
    question_lower = question.lower()
    
    context = {
        "nama": mahasiswa.full_name,
        "nim": mahasiswa.nim,
        "study_progam": mahasiswa.study_program,
        "semester": mahasiswa.semester,
    }
    
    if any(k in question_lower for k in ["ukt", "bayar", "lunas", "tunggakan"]):
        context["status_ukt"] = (
            "Sudah lunas" if mahasiswa.status_ukt else "Belum lunas"
        )
    
    if any(k in question_lower for k in ["absensi", "hadir", "kehadiran"]):
        total_hadir = db.query(Absensi).filter(
            Absensi.mahasiswa_id == mahasiswa.id,
            Absensi.status == AttendanceStatus.HADIR
        )
        
        context["total_kehadiran"] = f"{total_hadir} pertemuan"
    
    if any(k in question_lower for k in ["status", "aktif", "non-aktif"]):
        context["status_akademik"] = (
            "Aktif" if mahasiswa.activate_status else "Non-Aktif"
        )
    
    return context

def process_question(
    question: str,
    mahasiswa: Mahasiswa,
    db: Session,
):
    """
    The AI ​​Agent's main function is to process questions end-to-end.

    Flow:
    1. Detect intent (DB or RAG)
    2. Fetch appropriate context
    3. Send to Groq with appropriate prompt
    4. Return answer + metadata

    Arguments:
        question: question from student
        student: currently logged-in student data
        db: database session

    Returns:
        dict: {
            "answer": str, answer from Groq
            "intent": str, "database" or "rag"
            "sources": list, document source (for RAG only)
        }
    """
    intent = detect_intent(question=question)
    logger.info(f"[AGENT] Intent detected: {intent} | Question: {question}")
    
    if intent == "database":
        db_context = get_student_db_context(mahasiswa, db, question)
        
        prompt = build_db_prompt(db_context, question)
        
        answer = chat_completion(
            user_message=prompt,
            system_prompt=(
                "Kamu adalah asisten akademik system. "
                "Jawab dengan ramah, singkat, dan personal. "
                "Gunakan nama mahasiswa dalam jawaban."
            ),
            temperature=0.2,
        )
        
        return {
            "answer": answer,
            "intent": intent,
            "sources": [],
        }
    
    else: 
        retrieved_docs = retrieve_context(question, n_results=2)
        
        print(f"[DEBUGGING] This is needed for debugging")
        print("CONTEXT THAT RETRIEVED: ", retrieved_docs)
        if not retrieved_docs:
            return {
                "answer": (
                    "Maaf, saya tidak menemukan informasi terkait pertanyaan tersebut. "
                    "Silakan hubungi bagian akademik kampus untuk informasi lebih lanjut."
                ),
                "intent": "rag",
                "sources": [],
            }
        
    
        context = format_context_for_prompt(retrieved_docs)
        
        prompt = build_rag_prompt(context, question)
        answer = chat_completion(
            user_message=prompt,
            system_prompt=(
                "Kamu adalah asisten akademik system yang membantu mahasiswa. "
                "Jawab hanya berdasarkan konteks yang diberikan. "
                "Jika tidak ada informasinya, akui dengan jujur."
            ),
            temperature=0.3
        )
        
        sources = list(set(doc["source"] for doc in retrieved_docs))
        
        return {
            "answer": answer,
            "intent": intent,
            "sources": sources,
        }