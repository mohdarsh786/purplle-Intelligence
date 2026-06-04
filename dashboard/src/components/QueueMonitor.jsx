import React from 'react';
import { Users, Clock } from 'lucide-react';

export default function QueueMonitor({ metrics }) {
  const healthScore = metrics?.store_health_score || 0;

  return (
    <div className="glass-card">
      <h3>Store Health & Queue Monitor</h3>
      <p className="color-text-muted" style={{fontSize: '13px', margin: '4px 0 20px 0'}}>Composite store performance score from conversion, engagement, and queue metrics</p>
      
      <div className="queue-bars">
        <div className="queue-bar-item">
          <div className="queue-label">
            <span style={{display: 'flex', alignItems: 'center', gap: '6px'}}>
              <Users size={14} className="color-text-muted" />
              Store Health Score
            </span>
            <span style={{fontWeight: 'bold', fontSize: '24px', color: healthScore >= 70 ? 'var(--color-success)' : healthScore >= 40 ? 'var(--color-warning)' : 'var(--color-danger)'}}>{healthScore}/100</span>
          </div>
          <div className="queue-track-bg">
            <div className="queue-fill" style={{ width: `${Math.min(healthScore, 100)}%` }}></div>
          </div>
        </div>

        <div className="queue-bar-item" style={{marginTop: '12px'}}>
          <div className="queue-label">
            <span style={{display: 'flex', alignItems: 'center', gap: '6px'}}>
              <Clock size={14} className="color-text-muted" />
              Checkout Zone Queue
            </span>
            <span style={{fontWeight: 'bold'}}>
              {metrics?.conversion?.buyers || 0} buyers / {metrics?.footfall?.unique_visitors || 0} visitors
            </span>
          </div>
          <div className="queue-track-bg" title={metrics?.conversion?.conversion_status === 'insufficient_identity_mapping' ? 'POS and CCTV datasets are not temporally aligned.' : ''}>
            <div className="queue-fill" style={{ width: `${metrics?.conversion?.conversion_status === 'insufficient_identity_mapping' ? 0 : (metrics?.conversion?.conversion_rate ? Math.min(metrics.conversion.conversion_rate, 100) : 0)}%` }}></div>
          </div>
          <p className="color-text-muted" style={{fontSize: '11px', display: 'flex', alignItems: 'center', gap: '4px'}}>
            Conversion rate: {metrics?.conversion?.conversion_status === 'insufficient_identity_mapping' ? 'N/A' : (metrics?.conversion?.conversion_rate ? metrics.conversion.conversion_rate.toFixed(1) + '%' : '0.0%')}
          </p>
        </div>
      </div>
    </div>
  );
}
