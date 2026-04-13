"""
services/liveness.py — Detect whether a face is real or a photo/video

Liveness detection = anti-spoofing.
Prevents people from signing in with photos of friends.

Our approach: OpenCV-based texture analysis.
- Real faces -> Complex skin texture, natural noise.
- Photos -> Flat, too smooth, different reflection patterns.
"""

import cv2
import numpy as np
from typing import Tuple

from backend.config import get_settings

settings = get_settings()

def analyze_texture(gray_image: np.ndarray) -> float:
    """
    Image texture analysis using Laplacian variance.

    Laplacian = a mathematical operator that detects edges in images.
    - Real photos -> many natural edges (pores, hair, skin texture) -> high variance
    - Screen/printed photos -> blurry, few edges -> low variance

    Args:
        gray_image: grayscale image (numpy array)

    Returns:
        float: variance of the Laplacian value (higher = more "real")
    """
    laplacian = cv2.Laplacian(gray_image, cv2.CV_64F)
    
    variance = laplacian.var()
    return float(variance)

def analyze_reflection(image: np.ndarray) -> float:
    """
    Analyze the light reflection patterns in the image.

    Phone/monitor screens have different reflection patterns than real leather.
    Real leather absorbs light; screens reflect it with a uniform pattern.

    Args:
        image: BGR image (numpy array)

    Returns:
        float: reflection score (lower = more natural = more realistic)
    """
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    v_channel = hsv[:, :, 2]
    
    highlight_mask = v_channel > 220
    highlight_ratio = np.sum(highlight_mask) / highlight_mask.size
    
    return float(highlight_ratio)

def detect_liveness(image_bytes: bytes) -> Tuple[bool, float, dict]:
    """
    Main liveness detection function.

    Combines several signals to determine if a face is genuine:
    1. Texture analysis (Laplacian variance)
    2. Reflection analysis
    3. Blur detection

    Args:
        image_bytes: Face image in bytes

    Returns:
        Tuple[bool, float, dict]:
        - bool: True if liveness passed (real face)
        - float: Confidence score (0.0 - 1.0)
        - dict: Details of each metric for debugging
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        return False, 0.0, {"error": "Failed decode images"}
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Texture Score
    texture_variance = analyze_texture(gray)
    texture_score = min(1.0, texture_variance / 300.0)
    
    # Blur Score
    blur_variance = cv2.Laplacian(gray, cv2.CV_64F).var()
    blur_score = min(1.0, blur_variance / 200.0)
    
    # Reflection Score
    highlight_ratio = analyze_reflection(img)
    reflection_score = max(0.0, 1.0 - (highlight_ratio * 10))
    
    # Fusion All Score: Compute with how much important metrics for detection liveness
    final_score = (
        texture_score * 0.6 +
        blur_score * 0.3 +
        reflection_score * 0.1
    )
    final_score = round(float(final_score), 1)
    
    # Determined Results
    is_live = final_score >= settings.LIVENESS_THRESHOLD
    
    metrics = {
        "texture_variance": round(texture_variance, 2),
        "texture_score": round(texture_score, 4),
        "blur_score": round(blur_score, 4),
        "reflection_score": round(reflection_score, 4),
        "final_score": final_score,
        "threshold": settings.LIVENESS_THRESHOLD,
    }
    
    return is_live, final_score, metrics