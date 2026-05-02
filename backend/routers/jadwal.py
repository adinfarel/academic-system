"""
routers/jadwal.py — Class schedule and announcement endpoint

Schedule:
- POST /jadwal/ → admin/lecturer creates a schedule
- GET /jadwal/today-today → students view today's schedule
- GET /jadwal/this-week → students view the weekly schedule
- GET /jadwal/mengajar → lecturers view their teaching schedule

Announcements:
- POST /jadwal/announcement → admin/lecturer creates an announcement
- GET /jadwal/announcement → all users view active announcements
- DELETE /jadwal/announcement/{id} → admin deletes the announcement
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timezone
from typing import List, Optional

from backend.database import get_db
from backend.dependencies import (
    get_current_user,
    get_current_activate_admin,
    get_current_active_mahasiswa,
    get_current_activate_lecturer
)
from backend.models.user import User, UserRole
from backend.models.mahasiswa import Mahasiswa
from backend.models.dosen import Dosen
from backend.models.jadwal import HariKuliah, JadwalKuliah
from backend.models.announcement import Announcement, AnnouncementTarget
from backend.schemas.jadwal import (
    JadwalCreateRequest,
    JadwalResponse,
    AnnouncementResponse,
    AnnouncementCreateRequest,
)

router = APIRouter()

@router.post(
    "/",
    summary="[ADMIN/LECTURER] Make new schedule class."
)
def create_jadwal(
    payload: JadwalCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_activate_lecturer),
):
    """
    Admin or Lecturer input schedule school routine.
    """
    new_jadwal = JadwalKuliah(
        kode_mk=payload.kode_mk,
        nama_mk=payload.nama_mk,
        sks=payload.sks,
        hari=payload.hari,
        jam_mulai=payload.jam_mulai,
        jam_selesai=payload.jam_selesai,
        ruangan=payload.ruangan,
        program_studi=payload.program_studi,
        semester_ke=payload.semester_ke,
        tahun_akademik=payload.tahun_akademik,
        dosen_id=payload.dosen_id,
        is_active=True,
    )
    
    db.add(new_jadwal)
    db.commit()
    db.refresh(new_jadwal)
    
    return {
        "messages": "Jadwal successfully added.",
        "jadwal_id": new_jadwal.id,
        "detail": f"{new_jadwal.nama_mk} - {new_jadwal.hari} {new_jadwal.jam_mulai}"
    }

@router.get(
    "/hari-ini",
    summary="[STUDENT] Class schedule today."
)
def get_jadwal_hari_ini(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_mahasiswa),
):
    """
    Take class schedule for student this today.
    """
    mahasiswa = db.query(Mahasiswa).filter(
        Mahasiswa.user_id == current_user.id
    ).first()
    
    if not mahasiswa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data student not found."
        )
    
    hari_map = {
        0: HariKuliah.SENIN,
        1: HariKuliah.SELASA,
        2: HariKuliah.RABU,
        3: HariKuliah.KAMIS,
        4: HariKuliah.JUMAT,
        5: HariKuliah.SABTU,
        6: None,
    }
    
    hari_sekarang = hari_map.get(datetime.now(timezone.utc).weekday())
    
    if hari_sekarang is None:
        return {
            "hari": "Minggu",
            "pesan": "Tidak ada kuliah hari ini",
            "jadwal": [],
        }
    
    jadwal_list = db.query(JadwalKuliah).filter(
        and_(
            JadwalKuliah.hari == hari_sekarang,
            JadwalKuliah.program_studi == mahasiswa.study_program,
            JadwalKuliah.semester_ke == mahasiswa.semester,
            JadwalKuliah.is_active == True,
        )
    ).order_by(JadwalKuliah.jam_mulai).all()
    
    return {
        "hari": hari_sekarang.value,
        "tanggal": datetime.now(timezone.utc).strftime("%d %B %Y"),
        "total_kuliah": len(jadwal_list),
        "jadwal": [
            {
                "id": j.id,
                "kode_mk": j.kode_mk,
                "nama_mk": j.nama_mk,
                "sks": j.sks,
                "jam_mulai": j.jam_mulai.strftime("%H:%M"),
                "jam_selesai": j.jam_selesai.strftime("%H:%M"),
                "ruangan": j.ruangan,
                "dosen": j.dosen.full_name if j.dosen else "TBA",
            }
            for j in jadwal_list
        ]
    }

@router.get(
    "/minggu-ini",
    summary="[MAHASISWA] Class schedule full week."
)
def get_jadwal_minggu_ini(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_mahasiswa),
):
    """
    Get all student class schedules for the entire week.
    Grouped by day — perfect for a weekly view.
    """
    mahasiswa = db.query(Mahasiswa).filter(
        Mahasiswa.user_id == current_user.id
    ).first()
    
    if not mahasiswa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data student not found."
        )
    
    semua_jadwal = db.query(JadwalKuliah).filter(
        and_(
            JadwalKuliah.program_studi == mahasiswa.study_program,
            JadwalKuliah.semester_ke == mahasiswa.semester,
            JadwalKuliah.is_active == True,
        )
    ).order_by(JadwalKuliah.hari, JadwalKuliah.jam_mulai).all()
    
    jadwal_per_hari = {}
    for j in semua_jadwal:
        hari = j.hari.value
        if hari not in jadwal_per_hari:
            jadwal_per_hari[hari] = []
    
        jadwal_per_hari[hari].append({
            "id": j.id,
            "kode_mk": j.kode_mk,
            "nama_mk": j.nama_mk,
            "sks": j.sks,
            "jam_mulai": j.jam_mulai.strftime("%H:%M"),
            "jam_selesai": j.jam_selesai.strftime("%H:%M"),
            "ruangan": j.ruangan,
            "dosen": j.dosen.full_name if j.dosen else "TBA",
        })
    
    return {
        "mahasiswa": mahasiswa.full_name,
        "program_studi": mahasiswa.study_program,
        "semester": mahasiswa.semester,
        "total_mk": len(semua_jadwal),
        "jadwal_per_hari": jadwal_per_hari,
    }

@router.get(
    "/mengajar",
    summary="[LECTURER] Teaching schedule of logged-in lecturers"
)
def get_jadwal_mengajar(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_activate_lecturer),
):
    dosen = db.query(Dosen).filter(
        Dosen.user_id == current_user.id
    ).first()
    
    if not dosen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data lecturer not found."
        )
    
    jadwal_list = db.query(JadwalKuliah).filter(
        and_(
            JadwalKuliah.dosen_id == dosen.id,
            JadwalKuliah.is_active == True,
        )
    ).order_by(JadwalKuliah.hari, JadwalKuliah.jam_mulai).all()
    
    jadwal_per_hari = {}
    for j in jadwal_list:
        hari = j.hari.value
        if hari not in jadwal_per_hari:
            jadwal_per_hari[hari] = []
        jadwal_per_hari[hari].append({
            "id": j.id,
            "kode_mk": j.kode_mk,
            "nama_mk": j.nama_mk,
            "ruangan": j.ruangan,
            "jam_mulai": j.jam_mulai.strftime("%H:%M"),
            "jam_selesai": j.jam_selesai.strftime("%H:%M"),
            "program_studi": j.program_studi,
            "semester_ke": j.semester_ke,
        })
    
    return {
        "dosen": dosen.full_name,
        "total_kelas": len(jadwal_list),
        "jadwal_per_hari": jadwal_per_hari,
    }

@router.post(
    "/announcement",
    summary="[ADMIN/LECTURER] For new announcement."
)
def create_announcement(
    payload: AnnouncementCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_activate_lecturer)
):
    """
    Admins or lecturers make announcements.
    Announcements are immediately active and appear on the dashboard as targeted.
    """
    new_ann = Announcement(
        judul=payload.judul,
        konten=payload.konten,
        target=payload.target,
        priority=payload.priority,
        expiry_date=payload.expiry_date,
        created_by=current_user.id,
        is_active=True,
    )
    
    db.add(new_ann)
    db.commit()
    db.refresh(new_ann)
    
    return {
        "message": "Pengumuman successfully create.",
        "announcement_id": new_ann.id,
        "judul": new_ann.judul,
        "target": new_ann.target,
    }

@router.get(
    "/announcement",
    summary="See all announcement active."
)
def get_announcement(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    now = datetime.now(timezone.utc)
    
    role_target_map = {
        UserRole.MAHASISWA: [
            AnnouncementTarget.SEMUA,
            AnnouncementTarget.MAHASISWA
        ],
        UserRole.DOSEN: [
            AnnouncementTarget.SEMUA,
            AnnouncementTarget.DOSEN
        ],
        UserRole.ADMIN: [
            AnnouncementTarget.SEMUA,
            AnnouncementTarget.MAHASISWA,
            AnnouncementTarget.DOSEN
        ],
    }
    
    targets = role_target_map.get(current_user.role, [AnnouncementTarget.SEMUA])
    
    announcements = db.query(Announcement).filter(
        and_(
            Announcement.is_active == True,
            Announcement.target.in_(targets),
            (Announcement.expiry_date == None) |
            (Announcement.expiry_date > now)
        )
    ).order_by(
        Announcement.created_at.desc()
    ).all()
    
    return {
        "total": len(announcements),
        "announcements": [
            {
                "id": a.id,
                "judul": a.judul,
                "konten": a.konten,
                "priority": a.priority,
                "target": a.target,
                "expiry_date": a.expiry_date,
                "created_at": a.created_at,
                "creator": a.creator.username if a.creator else "System",
            }
            for a in announcements
        ]
    }

@router.delete(
    "/announcement/{announcement_id}",
    summary="[ADMIN] Delete or non-active announcement."
)
def delete_announcement(
    announcement_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_activate_admin),
):
    """
    Soft delete - Non-active announcement.
    but data keep on database to trace previous announcement.
    """
    ann = db.query(Announcement).filter(
        Announcement.id == announcement_id,
    ).first()
    
    if not ann:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Announcement not found."
        )
        
    ann.is_active = False
    db.commit()
    
    return {"messages": f"Pengumuman '{ann.judul}' berhasil dinonaktifkan"}