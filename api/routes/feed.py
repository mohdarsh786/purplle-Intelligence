"""
GET /feed/video -- Live Camera Feed Endpoint

Serves the actual store CCTV footage file for dashboard playback.
This provides visual proof that the system processes real footage,
not fabricated data.

The video is served as a streaming response to avoid loading
the entire file into memory.
"""

import logging
import os

from typing import Any
from fastapi import APIRouter
from fastapi.responses import FileResponse

logger = logging.getLogger("feed_route")

router = APIRouter()

def _find_videos(store_id: str) -> list[dict[str, Any]]:
    """Find all .mp4 files for a given store_id, or all stores if shared."""
    videos = []
    
    if store_id == "shared":
        store_dirs = ["store_1", "store_2"]
    else:
        store_dirs = [store_id]
        
    for s_id in store_dirs:
        video_dir = os.path.join("data", "stores", s_id, "videos")
        if not os.path.isdir(video_dir):
            continue
        for f in os.listdir(video_dir):
            if f.lower().endswith(".mp4"):
                path = os.path.join(video_dir, f)
                videos.append({
                    "id": f.replace(".mp4", ""),
                    "name": f,
                    "store_id": s_id,
                    "path": path,
                    "size_mb": round(os.path.getsize(path) / (1024 * 1024), 1)
                })
    return videos


@router.get("/feed/video")
def get_video_feed(store_id: str = "store_1", camera_id: str | None = None):
    """
    Serve the store CCTV video file for dashboard playback.
    """
    videos = _find_videos(store_id)
    if not videos:
        return {"success": False, "error": "No video file found"}
        
    video = None
    if camera_id:
        video = next((v for v in videos if v["id"] == camera_id), None)
    
    if not video:
        video = videos[0]
        
    logger.info("Serving video feed from: %s", video["path"])
    return FileResponse(
        video["path"],
        media_type="video/mp4",
        filename=video["name"],
    )


@router.get("/feed/status")
def get_feed_status(store_id: str = "shared"):
    """
    Return metadata about the available camera feeds.
    """
    videos = _find_videos(store_id)
    if videos:
        return {
            "success": True,
            "data": {
                "cameras": videos,
                "status": "available",
            }
        }

    return {
        "success": True,
        "data": {
            "cameras": [],
            "status": "unavailable",
        }
    }
