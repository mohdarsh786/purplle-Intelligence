import React from 'react';

export default function FunnelChart({ funnelData }) {
  return (
    <div className="glass-card">
      <h3>Purchase Conversion Funnel</h3>
      <p className="color-text-muted" style={{fontSize: '13px', margin: '4px 0 20px 0'}}>Visual shopper pathways mapped to sales conversion</p>
      
      <div className="funnel-container">
        {funnelData.map((item, idx) => (
          <div key={idx} className="funnel-row">
            <div className="funnel-label-block">
              {item.stage}
            </div>
            <div className="funnel-graphic-container">
              <div 
                className="funnel-fill-block" 
                style={{ width: `${item.percentage}%` }}
              ></div>
              <span className="funnel-value-label">
                {item.count} shoppers ({item.percentage}%)
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
