import React from 'react';
import Header from '../components/Header';
import ZoneHeatmap from '../components/ZoneHeatmap';
import FunnelChart from '../components/FunnelChart';
import JourneyTable from '../components/JourneyTable';

export default function Analytics({ data, selectedStore }) {
  const funnelData = data?.funnel || {};
  const stages = funnelData?.stages || [];
  const journeys = data?.journeys || {};
  const health = data?.health || null;

  return (
    <>
      <Header 
        subtitle="Deep analytics mapping customer layout flows and conversion funnel" 
        health={health}
      />
      
      <div className="content-body">
        {/* Core Layout and Heatmaps */}
        <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '32px'}}>
          <ZoneHeatmap />
          <FunnelChart funnelData={stages} />
        </div>

        {/* Journey Table details */}
        <div style={{display: 'grid', gridTemplateColumns: '1fr', gap: '32px'}}>
          <JourneyTable journeys={journeys} />
        </div>
      </div>
    </>
  );
}
