import React, { useState, useEffect } from 'react';
import Dashboard from './pages/Dashboard';
import Analytics from './pages/Analytics';
import { StoreApi } from './services/api';
import { LayoutDashboard, BarChart2, Store } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedStore, setSelectedStore] = useState('store_1');
  const [state, setState] = useState({
    metrics: null,
    funnel: null,
    journeys: null,
    anomalies: null,
    recommendations: null,
    health: null
  });

  const fetchData = async () => {
    const res = await StoreApi.getDashboard(selectedStore);
    if (res?.data) {
      setState(res.data);
    }
  };

  useEffect(() => {
    fetchData();
    // Poll data every 5 seconds for real-time reactivity
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, [selectedStore]);

  return (
    <div className="app-container">
      {/* Sidebar navigation */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <span style={{ fontSize: '22px' }}>💜</span>
          <span>Purplle Intelligence</span>
        </div>

        {/* Store Selector */}
        <div className="store-selector">
          <label className="store-selector-label">
            <Store size={14} />
            <span>Active Store</span>
          </label>
          <div className="store-selector-buttons" style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <button
              className={`store-btn ${selectedStore === 'shared' ? 'active' : ''}`}
              onClick={() => setSelectedStore('shared')}
              style={{ width: '100%' }}
            >
              Shared Analytics
            </button>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                className={`store-btn ${selectedStore === 'store_1' ? 'active' : ''}`}
                onClick={() => setSelectedStore('store_1')}
                style={{ flex: 1 }}
              >
                Store 1
              </button>
              <button
                className={`store-btn ${selectedStore === 'store_2' ? 'active' : ''}`}
                onClick={() => setSelectedStore('store_2')}
                style={{ flex: 1 }}
              >
                Store 2
              </button>
            </div>
          </div>
        </div>

        <ul className="sidebar-menu">
          <li
            className={`sidebar-item ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            <LayoutDashboard size={18} />
            <span>Dashboard</span>
          </li>
          <li
            className={`sidebar-item ${activeTab === 'analytics' ? 'active' : ''}`}
            onClick={() => setActiveTab('analytics')}
          >
            <BarChart2 size={18} />
            <span>Floor Analytics</span>
          </li>
        </ul>
      </aside>

      {/* Main viewport panels */}
      <div className="main-wrapper">
        {activeTab === 'dashboard' ? (
          <Dashboard data={state} selectedStore={selectedStore} />
        ) : (
          <Analytics data={state} selectedStore={selectedStore} />
        )}
      </div>
    </div>
  );
}
