import React, { useState } from 'react';

export default function ZoneHeatmap() {
  const [activeZone, setActiveZone] = useState(null);

  // Real Purplle Store 1 zone layout based on store layout audit
  const zoneMetrics = {
    entry: { name: "Entry Zone", avgDwell: "0.8 min", color: "rgba(6, 182, 212, 0.4)", stroke: "#06b6d4" },
    jc: { name: "JC Section", avgDwell: "8.2 min", color: "rgba(139, 92, 246, 0.5)", stroke: "#8b5cf6" },
    foxtal: { name: "Foxtal Section", avgDwell: "6.4 min", color: "rgba(168, 85, 247, 0.45)", stroke: "#a855f7" },
    minimalist: { name: "Minimalist Section", avgDwell: "12.1 min", color: "rgba(236, 72, 153, 0.5)", stroke: "#ec4899" },
    tfs: { name: "TFS Section", avgDwell: "7.5 min", color: "rgba(244, 114, 182, 0.45)", stroke: "#f472b6" },
    loreal: { name: "L'Oréal Section", avgDwell: "9.8 min", color: "rgba(239, 68, 68, 0.45)", stroke: "#ef4444" },
    beauty: { name: "Beauty Section", avgDwell: "11.3 min", color: "rgba(251, 146, 60, 0.45)", stroke: "#fb923c" },
    checkout: { name: "Checkout Zone", avgDwell: "4.2 min", color: "rgba(16, 185, 129, 0.55)", stroke: "#10b981" }
  };

  return (
    <div className="glass-card" style={{gridColumn: 'span 2'}}>
      <h3>Store Floor Heatmap — Purplle Layout</h3>
      <p className="color-text-muted" style={{fontSize: '13px', margin: '4px 0 20px 0'}}>Hover over zones to inspect average dwell times</p>
      
      <div style={{display: 'flex', gap: '24px', flexWrap: 'wrap'}}>
        <div style={{flex: 1.5, minWidth: '320px'}}>
          <svg viewBox="0 0 1000 550" className="heatmap-svg" style={{background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border-glass)', borderRadius: '12px'}}>
            <defs>
              <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
                <path d="M 20 0 L 0 0 0 20" fill="none" stroke="rgba(255,255,255,0.02)" strokeWidth="1"/>
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid)" />
            
            {/* Entry Zone */}
            <g className="heatmap-zone" 
               onMouseEnter={() => setActiveZone("entry")}
               onMouseLeave={() => setActiveZone(null)}>
              <rect x="50" y="50" width="200" height="180" rx="10" 
                    fill={zoneMetrics.entry.color} 
                    stroke={activeZone === 'entry' ? "#ffffff" : zoneMetrics.entry.stroke}
                    strokeWidth={activeZone === 'entry' ? 2 : 1} />
              <text x="150" y="145" fill="#ffffff" textAnchor="middle" fontWeight="bold" fontSize="13">ENTRY</text>
            </g>

            {/* JC Section */}
            <g className="heatmap-zone" 
               onMouseEnter={() => setActiveZone("jc")}
               onMouseLeave={() => setActiveZone(null)}>
              <rect x="300" y="50" width="200" height="180" rx="10" 
                    fill={zoneMetrics.jc.color} 
                    stroke={activeZone === 'jc' ? "#ffffff" : zoneMetrics.jc.stroke}
                    strokeWidth={activeZone === 'jc' ? 2 : 1} />
              <text x="400" y="145" fill="#ffffff" textAnchor="middle" fontWeight="bold" fontSize="13">JC</text>
            </g>

            {/* Foxtal Section */}
            <g className="heatmap-zone" 
               onMouseEnter={() => setActiveZone("foxtal")}
               onMouseLeave={() => setActiveZone(null)}>
              <rect x="550" y="50" width="200" height="180" rx="10" 
                    fill={zoneMetrics.foxtal.color} 
                    stroke={activeZone === 'foxtal' ? "#ffffff" : zoneMetrics.foxtal.stroke}
                    strokeWidth={activeZone === 'foxtal' ? 2 : 1} />
              <text x="650" y="145" fill="#ffffff" textAnchor="middle" fontWeight="bold" fontSize="13">FOXTAL</text>
            </g>

            {/* Minimalist Section */}
            <g className="heatmap-zone" 
               onMouseEnter={() => setActiveZone("minimalist")}
               onMouseLeave={() => setActiveZone(null)}>
              <rect x="800" y="50" width="150" height="180" rx="10" 
                    fill={zoneMetrics.minimalist.color} 
                    stroke={activeZone === 'minimalist' ? "#ffffff" : zoneMetrics.minimalist.stroke}
                    strokeWidth={activeZone === 'minimalist' ? 2 : 1} />
              <text x="875" y="145" fill="#ffffff" textAnchor="middle" fontWeight="bold" fontSize="11">MINIMALIST</text>
            </g>

            {/* TFS Section */}
            <g className="heatmap-zone" 
               onMouseEnter={() => setActiveZone("tfs")}
               onMouseLeave={() => setActiveZone(null)}>
              <rect x="50" y="280" width="200" height="220" rx="10" 
                    fill={zoneMetrics.tfs.color} 
                    stroke={activeZone === 'tfs' ? "#ffffff" : zoneMetrics.tfs.stroke}
                    strokeWidth={activeZone === 'tfs' ? 2 : 1} />
              <text x="150" y="395" fill="#ffffff" textAnchor="middle" fontWeight="bold" fontSize="13">TFS</text>
            </g>

            {/* L'Oréal Section */}
            <g className="heatmap-zone" 
               onMouseEnter={() => setActiveZone("loreal")}
               onMouseLeave={() => setActiveZone(null)}>
              <rect x="300" y="280" width="200" height="220" rx="10" 
                    fill={zoneMetrics.loreal.color} 
                    stroke={activeZone === 'loreal' ? "#ffffff" : zoneMetrics.loreal.stroke}
                    strokeWidth={activeZone === 'loreal' ? 2 : 1} />
              <text x="400" y="395" fill="#ffffff" textAnchor="middle" fontWeight="bold" fontSize="13">L'ORÉAL</text>
            </g>

            {/* Beauty Section */}
            <g className="heatmap-zone" 
               onMouseEnter={() => setActiveZone("beauty")}
               onMouseLeave={() => setActiveZone(null)}>
              <rect x="550" y="280" width="200" height="220" rx="10" 
                    fill={zoneMetrics.beauty.color} 
                    stroke={activeZone === 'beauty' ? "#ffffff" : zoneMetrics.beauty.stroke}
                    strokeWidth={activeZone === 'beauty' ? 2 : 1} />
              <text x="650" y="395" fill="#ffffff" textAnchor="middle" fontWeight="bold" fontSize="13">BEAUTY</text>
            </g>

            {/* Checkout Zone */}
            <g className="heatmap-zone" 
               onMouseEnter={() => setActiveZone("checkout")}
               onMouseLeave={() => setActiveZone(null)}>
              <rect x="800" y="280" width="150" height="220" rx="10" 
                    fill={zoneMetrics.checkout.color} 
                    stroke={activeZone === 'checkout' ? "#ffffff" : zoneMetrics.checkout.stroke}
                    strokeWidth={activeZone === 'checkout' ? 2 : 1} />
              <text x="875" y="395" fill="#ffffff" textAnchor="middle" fontWeight="bold" fontSize="13">CHECKOUT</text>
            </g>
          </svg>
        </div>
        
        {/* Dynamic Zone Legend Detail */}
        <div style={{flex: 1, minWidth: '240px', display: 'flex', flexDirection: 'column', justifyContent: 'center'}}>
          <div className="glass-card" style={{background: 'rgba(255,255,255,0.03)', borderColor: activeZone ? zoneMetrics[activeZone].stroke : 'var(--border-glass)'}}>
            <h4 style={{fontSize: '18px', display: 'flex', alignItems: 'center', gap: '8px'}}>
              <span style={{width: '12px', height: '12px', borderRadius: '50%', background: activeZone ? zoneMetrics[activeZone].stroke : '#8b5cf6'}}></span>
              {activeZone ? zoneMetrics[activeZone].name : "Select a Zone"}
            </h4>
            
            {activeZone ? (
              <div style={{marginTop: '20px', display: 'flex', flexDirection: 'column', gap: '12px'}}>
                <div style={{display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '8px'}}>
                  <span className="color-text-muted">Average Dwell</span>
                  <span style={{fontWeight: 'bold'}}>{zoneMetrics[activeZone].avgDwell}</span>
                </div>
                <div style={{display: 'flex', justifyContent: 'space-between'}}>
                  <span className="color-text-muted">Zone Type</span>
                  <span style={{fontWeight: 'bold', color: 'var(--color-secondary)'}}>{activeZone === 'entry' ? 'Entry' : activeZone === 'checkout' ? 'Billing' : 'Product'}</span>
                </div>
              </div>
            ) : (
              <p className="color-text-muted" style={{fontSize: '13px', marginTop: '12px'}}>
                Hover over Purplle store zones to inspect customer dwell performance.
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
