"""
services/location.py — Validate students' real-time location

Ensures students are actually on campus during attendance.

Formula used: Haversine
-> Calculates the shortest distance between two points on the surface of a sphere (the Earth)
-> More accurate than the usual Euclidean because the Earth is spherical, not flat

Why is GPS from the frontend and not the backend?
-> The backend doesn't have access to GPS hardware
-> The browser has a Geolocation API that directly accesses the device's GPS
-> The backend only validates the coordinates sent by the frontend
"""

import math
from typing import Tuple
from fastapi import HTTPException, status
from backend.config import get_settings

settings = get_settings()

def haversine_distance(
    lat1: float, lon1: float,
    lat2: float, lon2: float,
):
    """
    Calculate the distance between two GPS points using the Haversine formula.

    How it works:
    1. Convert degrees -> radians (math.radians)
    Why? Python trigonometric functions (sin, cos) require radians.
    2. Calculate the latitude and longitude deltas.
    3. Haversine formula -> get the angle between two points.
    4. Multiply by the Earth's radius -> get the distance in meters.

    Args:
        lat1, lon1: coordinates of the first point (student)
        lat2, lon2: coordinates of the second point (campus)

    Returns:
        float: distance in meters
    """
    R = 6_371_000 # Radius earth on meter
    
    # Convert all coord from degree to rad
    lat1_r = math.radians(lat1)
    lat2_r = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    # Haversine Formula
    a = (
        math.sin(delta_lat / 2) ** 2 +
        math.cos(lat1_r) * 
        math.cos(lat2_r) *
        math.sin(delta_lon) ** 2
    )
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    # Range = range earth x angle
    distance = R * c
    return round(distance, 2)

def validate_location(
    latitude: float,
    longitude: float,
) -> Tuple[bool, float, dict]:
    """
    Validate whether the student's coordinates are within the campus radius.

    Args:
        latitude: Student's latitude (from browser GPS)
        longitude: Student's longitude (from browser GPS)

    Returns:
        Tuple[bool, float, dict]:
        - bool: True if within campus radius
        - float: Distance to campus in meters
        - dict: Details for debugging and response
    """
    distance = haversine_distance(
        lat1=latitude,
        lon1=longitude,
        lat2=settings.CAMPUS_LATITUDE,
        lon2=settings.CAMPUS_LONGITUDE,
    )
    
    is_valid = distance <= settings.CAMPUS_RADIUS_METER
    
    detail = {
        "student_lat": latitude,
        "student_lon": longitude,
        "campus_lat": settings.CAMPUS_LATITUDE,
        "campus_lon": settings.CAMPUS_LONGITUDE,
        "range_meter": distance,
        "radius_meter": settings.CAMPUS_RADIUS_METER,
        "in_radius": is_valid,
    }
    
    return is_valid, distance, detail

def check_location_or_raise(latitude: float, longitude: float) -> dict:
    """
    The validate_location wrapper immediately raises an HTTPException if it fails.

    Called on the router — if the location is invalid, the request is immediately rejected
    without the need for an if-else in the router.

    Args:
        latitude: student's latitude
        longitude: student's longitude

    Returns:
        dict: location details if valid

    Raises:
        HTTPException 403: if the student is outside the campus radius
    """
    is_valid, distance, detail = validate_location(latitude=latitude, longitude=longitude)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Location is invalid. You is at {distance:.2f}m from campus. "
                f"Maximal {settings.CAMPUS_RADIUS_METER}m from campus."
            )
        )
    
    
    return detail