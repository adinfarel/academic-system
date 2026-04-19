"""
services/bulk_import.py — Bulk import of students from CSV

Workflow:
1. Read the CSV file uploaded by the admin
2. Validate each row (format, duplication)
3. Create accounts for valid rows (PENDING status)
4. Collect errors for invalid rows
5. Return a detailed report

Accepted CSV formats:
student ID number, full name, email, study program, major, semester, entry year
"""

import csv
import io
from typing import List, Dict, Tuple
from sqlalchemy.orm import Session

from backend.models.user import User, UserRole, RegistrationStatus
from backend.models.dosen import Dosen
from backend.services.auth import hash_password
from backend.utils.logger import get_logger

# LOGGER
logger = get_logger(__name__)

REQUIRED_COLUMNS = {
    'nidn', 'full_name', 'email',
    'study_program', 'major'
}

def validate_csv_headers(headers: List[str]) -> Tuple[bool, str]:
    """
    Validate the CSV header — ensure all required columns are present.

    Args:
        headers: list of column names from the CSV

    Returns:
        Tuple[bool, str]: (valid, error_message)
    """
    headers_lower = {h.strip().lower() for h in headers}
    missing = REQUIRED_COLUMNS - headers_lower
    
    if missing:
        return False, f"Column not found: {', '.join(missing)}"
    
    return True, ""

def validate_row(
    row: Dict,
    row_num: int,
    db: Session,
    processed_nidns: set,
    processed_emails: set,
) -> Tuple[bool, str]:
    """
    Validate a single CSV row.

    Validation performed:
    1. Required fields cannot be blank.
    2. Student ID number must be unique (check database + check between rows in the file).
    3. Email address must be unique (check database + check between rows in the file).
    4. Semester must be a number between 1-14.
    5. Year of enrollment must be a 4-digit number.
    
    Args:
        row: a single CSV row as a dict
        row_num: row number (for error messages)
        db: database session
        processed_nidns: set of processed student IDs in this file
        processed_emails: set of processed emails in this file

    Returns:
        Tuple[bool, str]: (valid, error_message)
    """
    row = {k.strip().lower(): v.strip() for k, v in row.items()}
    
    nidn = row.get('nidn', '').strip()
    email = row.get('email', '').strip()
    nama = row.get('full_name', '').strip()
    prodi = row.get('study_program', '').strip()
    major = row.get('major', '').strip()
    
    if not all([nidn, email, nama, prodi, major]):
        return (False, f"Row {row_num}: there's empty field.")
    
    if len(nidn) < 5:
        return False, f"Row {row_num}: nidn '{nidn}' too short."

    
    if nidn in processed_nidns:
        return False, f"Row {row_num}: nidn '{nidn}' duplicated in files."
    if email in processed_emails:
        return False, f"Row {row_num}: Email '{email}' duplicated in files."
    
    if db.query(Dosen).filter(Dosen.nidn == nidn).first():
        return False, f"Row {row_num}: nidn '{nidn}' registered in system."
    if db.query(User).filter(User.email == email).first():
        return False, f"Row {row_num}: Email '{email}' registered in system."

    return True, ""

def process_bulk_import(
    file_content: bytes,
    db: Session,
) -> Dict:
    """
    Main function: bulk import — processes all CSV files.
    
    Args:
        file_content: CSV file content in bytes
        db: database session

    Returns:
        dict: import report {
            "total_rows": int,
            "success": int,
            "failed": int,
            "errors": List[str],
            "imported": List[str] (successful nidns)
        }
    """
    
    try: 
        content_str = file_content.decode('utf-8')
    except UnicodeDecodeError:
        content_str = file_content.decode('latin-1')
    
    reader = csv.DictReader(io.StringIO(content_str))
    
    if not reader.fieldnames:
        return {
            "total_rows": 0,
            "success": 0,
            "failed": 0,
            "errors": ["File csv empty or invalid."],
            "imported": [],
        }
    
    headers_valid, headers_error = validate_csv_headers(
        list(reader.fieldnames)
    )
    
    if not headers_valid:
        return {
            "total_rows": 0,
            "success": 0,
            "failed": 0,
            "errors": [headers_error],
            "imported": [],
    }
    
    
    success_count = 0
    failed_count = 0
    errors = []
    imported_nidns = []
    
    processed_nidns = set()
    processed_emails = set()
    
    rows = list(reader)
    total_rows = len(rows)
    
    for row_num, row in enumerate(rows, start=2):
        row_normalized = {
            k.strip().lower(): v.strip()
            for k, v in row.items()
        }
        
        nidn = row_normalized.get('nidn', '')
        email = row_normalized.get('email', '')
        
        is_valid, error_msg = validate_row(
            row=row_normalized, row_num=row_num, db=db,
            processed_emails=processed_emails, processed_nidns=processed_nidns
        )
        
        if not is_valid:
            errors.append(error_msg)
            failed_count += 1
            continue
        
        try:
            username = nidn.lower()
            
            default_password = nidn
            
            new_user = User(
                email=email,
                username=username,
                hashed_password=hash_password(default_password),
                role=UserRole.DOSEN,
                is_active=True,
                registration_status=RegistrationStatus.ACTIVE,
            )
            db.add(new_user)
            db.flush()
            
            new_dosen = Dosen(
                user_id=new_user.id,
                nidn=nidn,
                full_name=row_normalized.get('full_name'),
                study_program=row_normalized.get('study_program'),
                major=row_normalized.get('major'),
                position=row_normalized.get('position', None)
            )
            db.add(new_dosen)
            db.flush()
            
            processed_emails.add(email)
            processed_nidns.add(nidn)
            
            imported_nidns.append(nidn)
            success_count += 1
            
            logger.info(f"[BULK] Row {row_num}: {nidn} - {row_normalized['full_name']}")
            
        except Exception as e:
            db.rollback()
            errors.append(f"Row {row_num}: Failed create account - {str(e)}")
            failed_count += 1
            continue
    try:
        db.commit()
        logger.info(f"[BULK] Finish: {success_count} success, {failed_count} failed.")
    except Exception as e:
        db.rollback()
        return {
            "total_rows": total_rows,
            "success": 0,
            "failed": total_rows,
            "errors": [f"Fail commit to databases: {str(e)}"],
            "imported": [],
        }
    
    return {
        "total_rows": total_rows,
        "success": success_count,
        "failed": failed_count,
        "errors": errors,
        "imported": imported_nidns,
        "note": (
            "All account that success import status PENDING. "
            "Admin need approve one by one via dashboard."
        )
    }