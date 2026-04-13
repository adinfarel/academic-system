"""
services/face_recognition.py — Core facial recognition logic

Library used: DeepFace (OpenCV wrapper + deep learning model)
DeepFace supports many models: VGG-Face, Facenet, ArcFace, etc.
We use ArcFace because it has the best accuracy for Asian faces.

Workflow:
1. Receive image (bytes/path)
2. Detect faces in the image
3. Extract encoding (128 digits representing the face)
4. Compare encoding with database
5. Return identification result
"""

import pickle
import numpy as np
from pathlib import Path
from typing import Optional
from io import BytesIO

import cv2
from deepface import DeepFace
from sqlalchemy.orm import Session

from backend.config import get_settings
from backend.utils.logger import get_logger
from backend.models.mahasiswa import Mahasiswa

settings = get_settings()
logger = get_logger(__name__)

# INIT MODEL
FACE_MODEL = "ArcFace"
DETECTOR = "opencv"

def bytes_to_cv2(image_bytes: bytes) -> np.ndarray:
    """
    Convert image bytes to a numpy array that OpenCV can process.

    Why is the conversion necessary?
    FastAPI accepts images as bytes (raw binary).
    OpenCV and DeepFace require a numpy array (pixel matrix).

    Args:
        image_bytes: image in byte format

    Returns:
        np.ndarray: BGR pixel matrix (OpenCV format)
    """
    
    nparr = np.frombuffer(image_bytes, np.uint8)
    
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img

def extract_face_encoding(image_bytes: bytes) -> Optional[np.ndarray]:
    """
    Extract face encoding from an image.

    Encoding = mathematical representation of a face in 512 dimensions (ArcFace).
    Similar faces will have mathematically "close" encodings.

    DeepFace internal process:
    1. Detect face location in image
    2. Crop and align face (normalize, rotate, scale)
    3. Run neural network -> output 512-dimensional vector

    Args:
        image_bytes: image in byte format

    Returns:
        np.ndarray: face encoding (array of 512 floats)
        None: if no face is detected
    
    Raises:
        ValueError: if more than one face is detected in the image
    """
    try:
        img = bytes_to_cv2(image_bytes)
        
        result = DeepFace.represent(
            img_path=img,
            model_name=FACE_MODEL,
            detector_backend=DETECTOR,
            enforce_detection=True,
        )
        
        if len(result) == 0:
            return None
        
        if len(result) > 1:
            raise ValueError(
                f"Detected {len(result)} faces in the image. "
                 "Make sure there is only 1 face."
            )
        
        encoding = np.array(result[0]['embedding'])
        return encoding
    
    except ValueError as e:
        raise e
    
    except Exception as e:
        logger.error(f"[FACE] There's not face detecting: {e}")
        return None

def encoding_to_bytes(encoding: np.ndarray) -> bytes:
    """
    Serialize numpy array -> bytes to save to PostgreSQL (BYTEA).

    Args:
        encoding: numpy array face encoding

    Returns:
        bytes: serialized encoding
    """
    return pickle.dumps(encoding)

def bytes_to_encoding(encoding_bytes: bytes) -> np.ndarray:
    """
    Deserialize bytes from DB -> numpy array

    Args:
        bytes: bytes from column face_encoding at DB

    Returns:
        encoding: numpy array face encoding
    """
    return pickle.loads(encoding_bytes)

def calculate_distance(encoding1: np.ndarray, encoding2: np.ndarray) -> float:
    """
    Calculate the cosine distance between two face encodings.

    Cosine distance measures the angle between two vectors.
    - Distance = 0.0 -> identical faces
    - Distance < 0.4 -> most likely the same person
    - Distance > 0.6 -> most likely different people

    Args:
        encoding1: first face encoding
        encoding2: second face encoding

    Returns:
        float: distance between two encodings (0.0 - 2.0)
    """
    norm1 = encoding1 / (np.linalg.norm(encoding1) + 1e-10)
    norm2 = encoding2 / (np.linalg.norm(encoding2) + 1e-10)
    
    cosine_similarity = np.dot(norm1, norm2)
    
    cosine_distance = 1 - cosine_similarity
    return float(cosine_distance)

def identify_face(
    image_bytes: bytes,
    db: Session,
    tolerance: Optional[float] = None,
) -> dict:
    """
    Identify faces from images by matching them to all students in the database.

    Flow:
    1. Extract the encoding from the input image.
    2. Get all students with the same face_encoding from the database.
    3. Compare them one by one, finding the smallest distance.
    4. If the smallest distance < tolerance → the student is identified.

    Args:
        image_bytes: The face image to be identified.
        db: Database session.
        tolerance: Distance threshold (default from settings).
        Smaller = stricter.

    Returns:
        dict with structure:
        {
            "identified": bool,
            "mahasiswa": Student | None,
            "distance": float,
            "confidence": float # 0-1, the higher the more confident.
        }
    """
    tol = tolerance or settings.FACE_TOLERANCE
    
    try:
        input_encoding = extract_face_encoding(image_bytes=image_bytes)
    except ValueError as e:
        return {
            "identified": False,
            "mahasiswa": None,
            "distance": None,
            "confidence": 0.0,
            "error": str(e)
        }
    
    if input_encoding is None:
        return {
            "identified": False,
            "mahasiswa": None,
            "distance": None,
            "confidence": 0.0,
            "error": "There's not face detection at image"
        }
    
    mahasiswas = db.query(Mahasiswa).filter(
        Mahasiswa.face_encoding.isnot(None)
    ).all()
    
    if not mahasiswas:
        return {
            "identified": False,
            "mahasiswa": None,
            "distance": None,
            "confidence": 0.0,
            "error": "Student not yet registered face."
        }
    
    best_match = None
    best_distance = float("inf")
    
    for mhs in mahasiswas:
        db_encoding = bytes_to_encoding(mhs.face_encoding)
        
        distance = calculate_distance(input_encoding, db_encoding)
        
        if distance < best_distance:
            best_distance = distance
            best_match = mhs
    
    confidence = max(0.0, 1.0 - (best_distance / tol))
    
    if best_distance <= tol:
        return {
            "identified": True,
            "mahasiswa": best_match,
            "distance": best_distance,
            "confidence": round(confidence, 4),
            "error": None
        }
    else:
        return {
            "identified": False,
            "mahasiswa": None,
            "distance": best_distance,
            "confidence": 0.0,
            "error": "Face not recognition"
        }

def register_face(
    mahasiswa: Mahasiswa,
    image_bytes: bytes,
    db: Session,
) -> dict:
    """
    Register student faces — extract the encoding and save it to the database.

    Called when students first set up their faces.
    After this, students can take attendance using facial recognition.

    Args:
        student: Student object from the database
        image_bytes: Student face image
        db: Database session

    Returns:
        dict: {"success": bool, "message": str}
    """
    try:
        encoding = extract_face_encoding(image_bytes=image_bytes)
    except ValueError as e:
        return {"success": False, "message": str(e)}
    
    if encoding is None:
        return {
            "success": False,
            "message": "Detection face not found, Make sure see clearly."
        }
    
    from datetime import datetime, timezone
    mahasiswa.face_encoding = encoding_to_bytes(encoding=encoding)
    mahasiswa.face_registered_at = datetime.now(timezone.utc)
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Face successful registered {mahasiswa.full_name}"
    }