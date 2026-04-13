"""
rag/groq_client.py — Wrapper for the Groq API

Groq = a very fast LLM inference service.
The model we use is: llama-3.1-8b-instant
- 8b = 8 billion parameters (large model, good answers)
- 2048 = context window (can accept 2048 tokens per request)

This file is responsible for:
1. Initializing the connection to Groq
2. Sending prompts -> receiving answers
3. Handling errors if the API is down or the limit is reached
"""

from groq import Groq
from typing import Optional
from backend.config import get_settings
from backend.utils.logger import get_logger

# LOGGER
logger = get_logger(__name__)

settings = get_settings()

_client = Groq(api_key=settings.GROQ_API_KEY)


def chat_completion(
    user_message: str,
    system_prompt: str,
    temperature: float = 0.3,
    max_tokens: int = 1024,
) -> str:
    """
    Send message to Groq and accept answer.
    
    Args:
        user_message: Question or message from the student
        system_prompt: Character and context instructions for the model
        temperature: Answer creativity (0.0-1.0)
        max_tokens: Answer length limit

    Returns:
        str: Answer from Groq

    Raises:
        Exception: If API error or rate limit occurs
    """
    try:
        response = _client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        return response.choices[0].message.content

    except Exception as e:
        logger.error(f"[GROQ ERROR] {e}")
        return (
            "Maaf, saya sedang mengalami gangguan. "
            "Silahkan coba beberapa saat lagi."
        )

def build_rag_prompt(context: str, question: str) -> str:
    """
    Create prompt that fusion context document + question user.
    
    Args:
        context: relevant text found from ChromaDB
        question: original question from the user

    Returns:
        str: complete prompt ready to be sent to Groq
    """
    return f"""Kamu adalah Asisten Akademik System yang membantu mahasiswa \
Politeknik Sriwijaya mendapatkan informasi akademik dengan akurat dan ramah.

Gunakan HANYA informasi dari konteks berikut untuk menjawab pertanyaan.
Jika informasi tidak ada di konteks, katakan dengan jujur bahwa kamu \
tidak memiliki informasi tersebut dan sarankan mahasiswa untuk menghubungi \
bagian akademik langsung.

Jangan mengarang atau menambahkan informasi di luar konteks.
Jawab dalam Bahasa Indonesia yang ramah dan mudah dipahami.

=== KONTEKS DOKUMEN ===
{context}
=== AKHIR KONTEKS ===

Pertanyaan mahasiswa: {question}

Jawaban:"""

def build_db_prompt(db_data: dict, question: str) -> str:
    """
    Create a prompt for deterministic queries from database data.

    Different from a RAG prompt — the context is not a document but student-specific data retrieved from PostgreSQL.

    Args:
        db_data: dict containing student data from the database
        question: the original question from the user

    Returns:
        str: complete prompt for DB data-based answers
    """
    data_str = "\n".join([f"- {k}: {v}" for k, v in db_data.items()])
    
    return f"""Kamu adalah Asisten Akademik PolsriEduAI yang membantu mahasiswa \
Politeknik Sriwijaya mendapatkan informasi akademik dengan akurat dan ramah.

Berikut adalah data akademik mahasiswa yang sedang bertanya:

=== DATA MAHASISWA ===
{data_str}
=== AKHIR DATA ===

Berdasarkan data di atas, jawab pertanyaan berikut dengan ramah dan natural.
Gunakan nama mahasiswa jika tersedia untuk membuat jawaban lebih personal.
Jawab dalam Bahasa Indonesia.

Pertanyaan: {question}

Jawaban:"""