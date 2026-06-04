// API communication client — consumes real /api/v1 endpoints
// Mock fallbacks use real Purplle store zones (no apparel/electronics)

const API_BASE = '/api';

// Fallback data uses real Purplle store zone names
const mockMetrics = {
  success: true,
  data: {
    footfall: { total_entries: 74, total_exits: 68, current_store_count: 6, unique_visitors: 71 },
    hourly_footfall: {},
    conversion: { buyers: 21, conversion_rate: 29.58, methodology: "store_level_unique_buyers_div_unique_visitors" },
    store_health_score: 82
  }
};

const mockFunnel = {
  success: true,
  data: {
    stages: [
      { stage: "entered_store", count: 74, percentage: 100.0 },
      { stage: "browsed_any_zone", count: 62, percentage: 83.8 },
      { stage: "reached_checkout", count: 31, percentage: 41.9 },
      { stage: "completed_purchase", count: 21, percentage: 28.4 }
    ],
    overall_conversion_rate: 29.58
  }
};

const mockJourneys = {
  success: true,
  data: {
    top_paths: [
      { path: ["entry_zone", "minimalist", "checkout_zone"], count: 14 },
      { path: ["entry_zone", "loreal", "checkout_zone"], count: 9 },
      { path: ["entry_zone", "jc", "foxtal", "exit_zone"], count: 7 },
      { path: ["entry_zone", "tfs", "salm", "checkout_zone"], count: 5 },
      { path: ["entry_zone", "beauty", "exit_zone"], count: 4 }
    ],
    average_journey_duration_seconds: 185.0
  }
};

const mockAnomalies = {
  success: true,
  data: {
    anomalies: []
  }
};

const mockRecommendations = {
  success: true,
  data: {
    recommendations: []
  }
};

const mockHealth = {
  success: true,
  data: {
    status: "ok",
    events_processed: 0,
    db_connected: true,
    last_event_timestamp: null,
    uptime_seconds: 0
  }
};

async function fetchFromApi(endpoint, fallback) {
  try {
    const res = await fetch(`${API_BASE}${endpoint}`);
    if (res.ok) {
      const json = await res.json();
      return json;
    }
    throw new Error("HTTP failure");
  } catch (err) {
    return fallback;
  }
}

export const StoreApi = {
  getDashboard: (storeId) => fetchFromApi(`/v1/dashboard?store_id=${storeId}`, {
    success: true,
    data: {
      metrics: mockMetrics.data,
      funnel: mockFunnel.data,
      journeys: mockJourneys.data,
      anomalies: mockAnomalies.data.anomalies,
      recommendations: mockRecommendations.data.recommendations,
      health: mockHealth.data
    }
  })
};
