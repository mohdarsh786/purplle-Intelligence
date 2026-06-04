import React from 'react';
import { AlertCircle } from 'lucide-react';

const severityColor = (severity) => {
  switch (severity) {
    case 'critical': return 'var(--color-danger)';
    case 'warn': return 'var(--color-warning)';
    case 'info': return 'var(--color-secondary)';
    default: return 'var(--color-text-muted)';
  }
};

const severityClass = (severity) => {
  switch (severity) {
    case 'critical': return 'critical';
    case 'warn': return 'warn';
    case 'info': return 'info';
    default: return 'info';
  }
};

export default function AnomalyFeed({ anomalies }) {
  return (
    <div className="glass-card">
      <h3>Live Anomaly Feed</h3>
      <p className="color-text-muted" style={{fontSize: '13px', margin: '4px 0 20px 0'}}>Real-time alerts triggered by operational threshold breaches</p>
      
      <div className="anomaly-list">
        {anomalies.length > 0 ? anomalies.map((item, idx) => (
          <div key={item.id || idx} className={`anomaly-item ${severityClass(item.severity)}`}>
            <AlertCircle size={18} style={{
              color: severityColor(item.severity),
              flexShrink: 0
            }} />
            <div className="anomaly-content">
              <p style={{fontSize: '13px', fontWeight: '500'}}>{item.description || item.message}</p>
              <div className="anomaly-meta">
                <span style={{textTransform: 'uppercase', fontSize: '10px', fontWeight: 'bold'}}>{item.severity}</span>
                <span> • </span>
                <span>{item.zone}</span>
                {item.timestamp && (
                  <>
                    <span> • </span>
                    <span>{new Date(item.timestamp).toLocaleTimeString()}</span>
                  </>
                )}
              </div>
            </div>
          </div>
        )) : (
          <p className="color-text-muted" style={{textAlign: 'center', padding: '24px 0', fontSize: '13px'}}>
            No anomalies detected. All operational thresholds within limits.
          </p>
        )}
      </div>
    </div>
  );
}
