"""
routers/absensi.py — Student Attendance Endpoint

Main Endpoints:
- POST /register-face → register student faces
- POST /check-in → attendance via facial recognition
- GET /history → student attendance history
- GET /session/{mk} → view attendance per course (lecturer)
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Form
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from backend.database import get_db
from backend.dependencies import (
    get_current_user,
    get_current_active_mahasiswa,
    get_current_activate_lecturer,
)
from backend.models.user import User
from backend.models.mahasiswa import Mahasiswa
from backend.models.absensi import Absensi, AbsensiMethods, AttendanceStatus
from backend.services.face_recognition import identify_face, register_face
from backend.services.liveness import detect_liveness
from backend.services.location import check_location_or_raise, validate_location

router = APIRouter()

@router.post(
    "/register-face",
    summary="Register student face for absensi"
)
async def register_face_endpoint(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Upload a face photo to be registered with the system.

    - Can only be called by logged-in students
    - Format: JPG or PNG
    - Ensure: 1 face, adequate lighting, not blurry

    Flow:
    1. Validate file (format, size)
    2. Search for student data based on the logged-in user
    3. Extract and save the face encoding
    """
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Format file must be JPG or PNG"
        )
    
    image_bytes = await file.read()
    if len(image_bytes) > 5 * 1024**2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Max size file 5MB."
        )
    
    mahasiswa = db.query(Mahasiswa).filter(
        Mahasiswa.user_id == current_user.id
    ).first()
    
    if not mahasiswa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data student not found. Calling admin.",
        )
    
    result = register_face(mahasiswa, image_bytes, db)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return {
        "message": result["message"],
        "face_registered_at": mahasiswa.face_registered_at
    }

@router.post(
    "/check-in",
    summary="Absence via face recognition."
)
async def check_in(
    mata_kuliah: str,
    kode_mk: str,
    pertemuan_ke: int = 1,
    ruangan: str = None,
    latitude: float = Form(...),
    longitude: float = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Complete attendance process:
    1. Liveness detection → verify the face is real
    2. Facial recognition → identify the person
    3. Save the attendance record to the database

    Anyone who has logged in can be called
    (the system will verify their face)
    """
    image_bytes = await file.read()
    
    # LOCATION DETECTION
    location_detail = check_location_or_raise(latitude, longitude)
    
    # LIVENESS DETECTION
    is_live, liveness_score, liveness_metrics = detect_liveness(image_bytes)
    
    if not is_live:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Liveness fail check (score: {liveness_score:.2f}) "
                "Make sure using live camera, not photo."
            )
        )
    
    # FACE RECOGNITION
    result = identify_face(image_bytes, db)
    
    if not result["identified"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result.get("error", "Face not recognize.")
        )
    
    mahasiswa = result["mahasiswa"]
    
    # CHECK DUPLICATE
    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0,
    )
    
    existing = db.query(Absensi).filter(
        Absensi.mahasiswa_id == mahasiswa.id,
        Absensi.kode_mk == kode_mk,
        Absensi.time_absence >= today_start,
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Already absence for {mata_kuliah} today."
        )
    
    # SAVED ABSENCE
    absence = Absensi(
        mahasiswa_id=mahasiswa.id,
        mata_kuliah=mata_kuliah,
        kode_mk=kode_mk,
        pertemuan_ke=pertemuan_ke,
        ruangan=ruangan,
        status=AttendanceStatus.HADIR,
        method=AbsensiMethods.FACE_RECOGNITION,
        confidence_score=result["confidence"],
        liveness_score=liveness_score,
        is_liveness_passed=True,
    )
    
    db.add(absence)
    db.commit()
    db.refresh(absence)
    
    return {
        "message": f"Absensi berhasil! Selamat datang, {mahasiswa.full_name}",
        "data": {
            "nama": mahasiswa.full_name,
            "nim": mahasiswa.nim,
            "mata_kuliah": mata_kuliah,
            "waktu": absence.time_absence,
            "confidence": result["confidence"],
            "liveness_score": liveness_score,
            "location": {
                "range_to_campus": f"{location_detail['range_meter']}m",
                "status": "in radius campus",
            }
        }
    }

@router.get(
    "/history",
    summary="Absence history student currently login."
)
def get_absensi_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_mahasiswa)
) -> dict:
    """
    Retrieve all attendance history of currently logged-in students.
    Sorted from most recent.
    """
    mahasiswa = db.query(Mahasiswa).filter(
        Mahasiswa.user_id == current_user.id
    ).first()
    
    if not mahasiswa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data student not found."
        )
    
    records = db.query(Absensi).filter(
        Absensi.mahasiswa_id == mahasiswa.id
    ).order_by(Absensi.time_absence.desc()).all()
    
    return {
        "mahasiswa": mahasiswa.full_name,
        "nim": mahasiswa.nim,
        "total_attendance": len(records),
        "records": [
            {
                "mata_kuliah": r.mata_kuliah,
                "kode_mk": r.kode_mk,
                "pertemuan_ke": r.pertemuan_ke,
                "status": r.status,
                "waktu": r.time_absence,
                "metode": r.method,
            }
            for r in records
        ]
    }

@router.get(
    "/session/{kode_mk}",
    summary="See absence per subject - specific lecturer"
)
def get_session_absensi(
    kode_mk: str,
    pertemuan_ke: int = 1,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_activate_lecturer)
):
    """
    Dosen can see anyone already absence.
    for subject and meeting certain.
    """
    records = db.query(Absensi).filter(
        Absensi.kode_mk == kode_mk,
        Absensi.pertemuan_ke == pertemuan_ke,
    ).order_by(Absensi.time_absence.asc()).all()
    
    return {
        "kode_mk": kode_mk,
        "pertemuan_ke": pertemuan_ke,
        "total_hadir": len(records),
        "records": [
            {
                "mahasiswa_id": r.mahasiswa_id,
                "status": r.status,
                "waktu": r.time_absence,
                "confidence_score": r.confidence_score,
                "liveness_score": r.liveness_score,
            }
            for r in records
        ]
    }