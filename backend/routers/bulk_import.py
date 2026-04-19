"""
routers/bulk_import.py — Student bulk import endpoint

POST /bulk/mahasiswa — admin uploads CSV → bulk import process
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Request
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.dependencies import get_current_activate_admin
from backend.models.user import User
from backend.services.bulk_import import process_bulk_import
from backend.middleware.rate_limit import limiter

router = APIRouter()

@router.post(
    "/lecturer",
    summary="[ADMIN] Bulk import lecturer from file CSV."
)
async def bulk_import_student(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_activate_admin)
):
    """
    Upload a CSV file containing lecturer data → create bulk accounts.
    All lecturer accounts will be immediately active — no approval required.

    CSV format:
    NIDN, full name, email, study program, department, position (optional)

    Example:
    0201234567, Dr. Budi Santoso, budi@polsri.ac.id, Informatics Engineering, Computer Engineering, Lecturer
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File have to format CSV (.csv)"
        )
    
    content = await file.read()
    
    if len(content) > 2 * 1024 ** 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Size file max 2MB."
        )
    
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File CSV empty."
        )
    
    result = process_bulk_import(content, db)
    
    if result['success'] == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result
        )
    
    return result