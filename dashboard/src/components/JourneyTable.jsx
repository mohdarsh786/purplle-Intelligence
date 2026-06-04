import React from 'react';

export default function JourneyTable({ journeys }) {
  const topPaths = Array.isArray(journeys) ? journeys : (journeys?.top_paths || []);

  return (
    <div className="glass-card" style={{gridColumn: 'span 3'}}>
      <h3>Top Customer Journey Paths</h3>
      <p className="color-text-muted" style={{fontSize: '13px', margin: '4px 0 20px 0'}}>Most common zone sequences derived from tracked visitor movement</p>
      
      <div className="journey-table-container">
        <table className="journey-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Zone Path</th>
              <th>Visitors</th>
            </tr>
          </thead>
          <tbody>
            {topPaths.length > 0 ? topPaths.map((j, idx) => (
              <tr key={idx}>
                <td style={{fontWeight: 'bold', color: 'var(--color-secondary)'}}>#{idx + 1}</td>
                <td>
                  {j.path.map((zone, zIdx) => (
                    <span key={zIdx} className="path-badge">
                      {zone}
                      {zIdx < j.path.length - 1 && " →"}
                    </span>
                  ))}
                </td>
                <td style={{fontWeight: 'bold'}}>{j.count}</td>
              </tr>
            )) : (
              <tr>
                <td colSpan="3" style={{textAlign: 'center', color: 'var(--color-text-muted)', padding: '24px'}}>
                  No journey data available yet. Waiting for tracked visitors.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      {journeys?.average_journey_duration_seconds && (
        <p className="color-text-muted" style={{fontSize: '12px', marginTop: '16px'}}>
          Average journey duration: {Math.round(journeys.average_journey_duration_seconds / 60)}m {Math.round(journeys.average_journey_duration_seconds % 60)}s
        </p>
      )}
    </div>
  );
}
