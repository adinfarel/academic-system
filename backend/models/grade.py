"""
models/nilai.py — Student grade table per course

Table architecture:
- 'nilai' → one row = one student grade for one course
- 'ips_semester' → one row = student's GPA for one semester

Why is the GPA stored in a separate table, instead of being calculated on-the-fly?
→ If calculated on-the-fly for each request, the more students there are, the slower it becomes (must loop through all grades for each query)
→ Stored = calculated once when the lecturer inputs the grade, cached forever
→ Trade-off: more storage but much faster queries
→ GPA is still calculated on-the-fly from the ips_semester table (lighter)
"""

from sqlalchemy import (
    Column, Integer, String, Float,
    DateTime, ForeignKey, Enum, UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from backend.database import Base

class LetterGrade(str, enum.Enum):
    """
    Enum valid letter grades in the campus system.
    Using the intermediate grade system (AB, BC),
    common in Indonesian polytechnics.
    """
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"

# MAPPING
GRADE_VALUE = {
    "A": 4.0,
    "B": 3.0,
    "C": 2.0,
    "D": 1.0,
    "E": 0.0
}

class Grade(Base):
    """
    'Grade' table — student grades per course per semester.

    One row = one student received one grade
    for one course in one semester.

    The UniqueConstraint below ensures:
    A student cannot have two different grades
    for the same course in the same semester.
    """
    __tablename__ = "grade"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # FOREIGN KEY
    mahasiswa_id = Column(
        Integer,
        ForeignKey("mahasiswa.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dosen_id = Column(
        Integer,
        ForeignKey("dosen.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # INFORMATION SUBJECT
    kode_mk = Column(String(20), nullable=False, index=True)
    nama_mk = Column(String(100), nullable=False)
    sks = Column(Integer, nullable=False)
    
    # GRADE
    letter_grade = Column(
        Enum(LetterGrade),
        nullable=False,
    )
    weight = Column(
        Float,
        nullable=False,
    )
    
    semester_ke = Column(Integer, nullable=False)
    academic_year = Column(String(20), nullable=False)
    
    # TIMESTAMPS
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    
    # CONSTRAINT
    __table_args__ = (
        UniqueConstraint(
            'mahasiswa_id', 'kode_mk', 'semester_ke', 'academic_year',
            name='unique_grade_mk_per_semester'
        )
    )
    
    def __repr__(self):
        return (
            f"<Grade mahasiswa_id={self.mahasiswa_id}>"
            f"mk={self.kode_mk} grade={self.letter_grade}"
        )

class IpsSemester(Base):
    """
    'ips_semester' table — Student GPA per semester.

    Automatically updated every time a lecturer inputs or changes a grade.
    No need to recalculate from scratch with each request.

    One row = student GPA for a specific semester.
    """
    __tablename__ = "ips_semester"
    
    id = Column(Integer, primary_key=True, index=True)
    
    mahasiswa_id = Column(
        Integer,
        ForeignKey("mahasiswa.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    semester_ke = Column(Integer, nullable=False)
    academic_year = Column(String(10), nullable=False)
    
    # INDEX PER SEMESTER
    ips = Column(Float, nullable=False)
    
    total_sks = Column(Integer, nullable=False)
    
    total_sks_pass = Column(Integer, nullable=False, default=0)
    
    # TIMESTAMPS
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    
    # CONSTRAINT
    __table_args__ = (
        UniqueConstraint("mahasiswa_id", "semester_ke", "academic_year",
                         name="unique_ips_per_semester")
    )
    
    mahasiswa = relationship("Mahasiswa", back_populates="ips_list")
    
    def __repr__(self):
        return (
            f"<IpsSemester mahasiswa_id={self.mahasiswa_id} "
            f"semester={self.semester_ke} ips={self.ips}>"
        )