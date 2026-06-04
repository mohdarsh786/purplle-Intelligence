import logging
from typing import Any
from fastapi import APIRouter, Query

from api.services.metrics_service import get_footfall_metrics
from api.services.pos_fusion import get_conversion_metrics
from api.services.health_score_service import get_health_score
from api.services.anomaly_service import get_anomalies
from api.services.recommendation_service import get_recommendations
from api.services.journey_service import get_top_paths
from api.services.queue_service import get_queue_analytics
from api.routes.feed import get_feed_status
from api.services.funnel_service import get_funnel_data

logger = logging.getLogger("dashboard_route")

router = APIRouter()

@router.get("/dashboard")
def get_dashboard(store_id: str = Query("shared")) -> dict[str, Any]:
    """
    Dashboard Aggregation Endpoint -- returns all dashboard data in a single request.
    Handles Store 1, Store 2, and Shared analytics.
    """
    
    # We pass store_id to all services if they support it.
    # Currently accommodating services that might not have been fully updated yet.
    
    # Footfall & Conversion
    try:
        footfall_data = get_footfall_metrics(store_id=store_id)
    except TypeError:
        footfall_data = get_footfall_metrics() # Fallback if store_id not supported yet
        
    unique_visitors = footfall_data.get("unique_visitors", 0)
    
    try:
        conversion = get_conversion_metrics(unique_visitors=unique_visitors, store_id=store_id)
    except TypeError:
        conversion = get_conversion_metrics(unique_visitors=unique_visitors)
        
    try:
        health = get_health_score(store_id=store_id)
    except TypeError:
        health = get_health_score()
        
    metrics_data = {
        "footfall": footfall_data,
        "conversion": {
            "buyers": conversion.get("buyers", 0),
            "unique_visitors": conversion.get("unique_visitors", unique_visitors),
            "conversion_rate": conversion.get("conversion_rate"),
            "methodology": conversion.get("methodology", ""),
        },
        "store_health_score": health.get("score", 100)
    }
    
    # Anomalies
    try:
        anomalies = get_anomalies(store_id=store_id)
    except TypeError:
        anomalies = get_anomalies()
        
    # Recommendations
    try:
        recommendations = get_recommendations(store_id=store_id)
    except TypeError:
        recommendations = get_recommendations()
        
    # Journeys
    try:
        journeys = get_top_paths(limit=5, store_id=store_id)
    except TypeError:
        journeys = get_top_paths(limit=5)
        
    # Funnel
    try:
        funnel = get_funnel_data(store_id=store_id)
    except TypeError:
        funnel = get_funnel_data()
        
    # Queue
    try:
        queue = get_queue_analytics(store_id=store_id)
    except TypeError:
        queue = get_queue_analytics()
        
    # Feed
    try:
        feed = get_feed_status(store_id=store_id)
    except TypeError:
        feed = get_feed_status()

    return {
        "success": True,
        "data": {
            "metrics": metrics_data,
            "anomalies": anomalies,
            "recommendations": recommendations,
            "journeys": journeys,
            "funnel": funnel,
            "queue": queue,
            "health": health,
            "feed": feed
        }
    }
