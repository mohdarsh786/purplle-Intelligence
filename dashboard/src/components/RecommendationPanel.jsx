import React from 'react';
import { Lightbulb } from 'lucide-react';

export default function RecommendationPanel({ recommendations }) {
  const recs = recommendations || [];

  return (
    <div className="glass-card" style={{gridColumn: 'span 2'}}>
      <h3 style={{display: 'flex', alignItems: 'center', gap: '8px'}}>
        <Lightbulb className="trend-up" size={20} />
        Operations Recommendations
      </h3>
      <p className="color-text-muted" style={{fontSize: '13px', margin: '4px 0 20px 0'}}>Rule-based recommendations derived from real-time analytics thresholds</p>
      
      <div className="recs-container">
        {recs.length > 0 ? (
          recs.map((rec, idx) => (
            <div key={idx} className="rec-card">
              <div>
                <p style={{fontSize: '14px', fontWeight: '500'}}>{rec.insight || rec.message}</p>
                <p style={{fontSize: '13px', color: 'var(--color-text-muted)', marginTop: '4px'}}>{rec.action}</p>
                <div style={{display: 'flex', gap: '8px', marginTop: '8px'}}>
                  {rec.priority && (
                    <span className="rec-impact">{rec.priority}</span>
                  )}
                  {rec.zone && (
                    <span className="rec-impact" style={{background: 'var(--color-primary-glow)', color: 'var(--color-primary)'}}>{rec.zone}</span>
                  )}
                  {rec.confidence && (
                    <span className="color-text-muted" style={{fontSize: '11px', alignSelf: 'center'}}>
                      Confidence: {(rec.confidence * 100).toFixed(0)}%
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))
        ) : (
          <p className="color-text-muted" style={{textAlign: 'center', padding: '24px 0', fontSize: '13px'}}>
            All operational thresholds within limits. No recommendations generated.
          </p>
        )}
      </div>
    </div>
  );
}
