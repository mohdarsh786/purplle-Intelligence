import React from 'react';

export default function MetricsCard({ title, value, suffix, icon: Icon, subtitle, tooltip }) {
  return (
    <div className="glass-card metric-card-container" title={tooltip}>
      <div className="metric-header">
        <span>{title}</span>
        {Icon && <Icon size={20} className="color-text-muted" style={{opacity: 0.7}} />}
      </div>
      <div className="metric-value">
        {value}{suffix}
      </div>
      {subtitle && (
        <div className="metric-footer color-text-muted" style={{fontWeight: 500}}>
          {subtitle}
        </div>
      )}
    </div>
  );
}
