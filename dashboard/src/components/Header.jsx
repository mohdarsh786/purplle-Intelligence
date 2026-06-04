import React from 'react';
import { Shield } from 'lucide-react';

export default function Header({ subtitle, health }) {
  const isLive = health && health.status === 'ok' && health.events_processed > 0;
  const lastEvent = health?.last_event_timestamp;

  return (
    <header className="header-container">
      <div className="header-title">
        <h1>Purplle Store Intelligence</h1>
        <p>{subtitle || "Real-time edge visual analysis & customer analytics"}</p>
      </div>
      <div className="header-status">
        <div className="status-indicator">
          <Shield size={14} className="trend-up" />
          <span>GDPR Compliant Edge</span>
        </div>
        <div className="status-indicator">
          <div className={`status-dot ${isLive ? 'active' : 'stale'}`}></div>
          <span>Feed: {isLive ? 'LIVE' : 'STALE'}</span>
        </div>
        {lastEvent && (
          <div className="status-indicator last-event-badge">
            <span>Last Event: {new Date(lastEvent).toLocaleTimeString()}</span>
          </div>
        )}
      </div>
    </header>
  );
}
