import React from 'react';
import MetricsCard from '../components/MetricsCard';
import QueueMonitor from '../components/QueueMonitor';
import AnomalyFeed from '../components/AnomalyFeed';
import RecommendationPanel from '../components/RecommendationPanel';
import LiveCameraPanel from '../components/LiveCameraPanel';
import Header from '../components/Header';
import { Users, Clock, ShoppingCart, Activity } from 'lucide-react';

export default function Dashboard({ data, selectedStore }) {
  const metrics = data?.metrics || {};
  const footfall = metrics?.footfall || {};
  const conversion = metrics?.conversion || {};
  const anomalyData = data?.anomalies || [];
  const anomalies = Array.isArray(anomalyData) ? anomalyData : (anomalyData?.anomalies || []);
  const recData = data?.recommendations || [];
  const recommendations = Array.isArray(recData) ? recData : (recData?.recommendations || []);
  const health = data?.health || null;

  return (
    <>
      <Header
        subtitle="Real-time physical store visual tracking and customer flow intelligence"
        health={health}
      />

      <div className="content-body">
        {/* Metrics Grid */}
        <div className="metrics-grid">
          <MetricsCard
            title="Total Footfall"
            value={footfall.total_entries || 0}
            icon={Users}
          />
          <MetricsCard
            title="Unique Visitors"
            value={footfall.unique_visitors || 0}
            icon={Users}
          />
          <MetricsCard
            title="Conversion Rate"
            value={conversion.conversion_status === 'insufficient_identity_mapping' ? 'N/A' : (conversion.conversion_rate ? conversion.conversion_rate.toFixed(1) : '0.0')}
            suffix={conversion.conversion_status === 'insufficient_identity_mapping' ? '' : '%'}
            icon={ShoppingCart}
            subtitle={conversion.conversion_status === 'insufficient_identity_mapping' ? `Buyers: ${conversion.buyers} | Visitors: ${conversion.unique_visitors}` : null}
            tooltip={conversion.conversion_status === 'insufficient_identity_mapping' ? 'POS and CCTV datasets are not temporally aligned.' : null}
          />
          <MetricsCard
            title="In Store Now"
            value={footfall.current_store_count || 0}
            icon={Activity}
          />
        </div>

        {/* Live Camera Feed */}
        <LiveCameraPanel health={health} feed={data?.feed} selectedStore={selectedStore} />

        {/* Central visual panel grids */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '32px' }}>
          <QueueMonitor metrics={metrics} />
          <AnomalyFeed anomalies={anomalies} />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '32px' }}>
          <RecommendationPanel recommendations={recommendations} />
        </div>
      </div>
    </>
  );
}
