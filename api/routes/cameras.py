"""
GET /cameras -- Camera Management Endpoint

Returns available cameras filtered by store_id.
"""
import json
import logging
import os
from typing import Any

from fastapi import APIRouter, HTTPException

logger = logging.getLogger("cameras_route")

router = APIRouter()

# Path to camera mapping config
CAMERA_MAPPING_PATH = os.path.join("data", "camera_store_mapping.json")


def load_camera_mapping() -> dict[str, Any]:
    """Load camera-to-store mapping from JSON config."""
    if not os.path.exists(CAMERA_MAPPING_PATH):
        logger.error("Camera mapping file not found: %s", CAMERA_MAPPING_PATH)
        return {"stores": {}}
    
    try:
        with open(CAMERA_MAPPING_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error("Failed to load camera mapping: %s", e)
        return {"stores": {}}


@router.get("/cameras")
def get_cameras(store_id: str = "shared") -> dict[str, Any]:
    """
    Camera list endpoint -- returns available cameras for a store.
    
    Args:
        store_id: Store identifier (store_1, store_2, or shared)
    
    Returns:
        {
            "success": true,
            "data": {
                "cameras": [...]
            }
        }
    """
    mapping = load_camera_mapping()
    stores = mapping.get("stores", {})
    
    cameras = []
    
    if store_id == "shared":
        # Return all cameras from all stores
        for store_name, store_data in stores.items():
            for cam in store_data.get("cameras", []):
                cameras.append({
                    **cam,
                    "store_id": store_name,
                    "store_name": store_data.get("name", store_name)
                })
    else:
        # Return cameras for specific store
        if store_id not in stores:
            raise HTTPException(
                status_code=404,
                detail=f"Store '{store_id}' not found in camera mapping"
            )
        
        store_data = stores[store_id]
        cameras = store_data.get("cameras", [])
    
    logger.info("Cameras listed for store_id=%s: %d cameras", store_id, len(cameras))
    
    return {
        "success": True,
        "data": {
            "cameras": cameras
        }
    }


@router.get("/cameras/default")
def get_default_camera(store_id: str = "shared") -> dict[str, Any]:
    """
    Return the default camera for a given store.
    
    Default selection logic:
    - Store 1: CAM 3 (entry) for best customer traffic visibility
    - Store 2: entry1 (primary entrance)
    - Shared: First camera from store_1
    """
    mapping = load_camera_mapping()
    stores = mapping.get("stores", {})
    
    default_camera = None
    
    if store_id == "store_1":
        # Prefer CAM 3 (entry camera)
        store_cameras = stores.get("store_1", {}).get("cameras", [])
        default_camera = next((c for c in store_cameras if c["id"] == "cam3"), None)
        if not default_camera and store_cameras:
            default_camera = store_cameras[0]
    
    elif store_id == "store_2":
        # Prefer entry1
        store_cameras = stores.get("store_2", {}).get("cameras", [])
        default_camera = next((c for c in store_cameras if c["id"] == "entry1"), None)
        if not default_camera and store_cameras:
            default_camera = store_cameras[0]
    
    else:  # shared
        # Return first camera from store_1
        store_cameras = stores.get("store_1", {}).get("cameras", [])
        if store_cameras:
            default_camera = store_cameras[0]
    
    if not default_camera:
        raise HTTPException(status_code=404, detail="No cameras available")
    
    return {
        "success": True,
        "data": {
            "camera": default_camera
        }
    }
