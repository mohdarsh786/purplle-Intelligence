import React, { useState, useEffect } from 'react';
import { Video, Camera, Wifi, WifiOff, LayoutGrid } from 'lucide-react';

export default function LiveCameraPanel({ health, feed, selectedStore }) {
  const [selectedCamera, setSelectedCamera] = useState(null);

  const cameras = feed?.data?.cameras || [];
  const feedAvailable = feed?.data?.status === 'available' && cameras.length > 0;
  const isLive = health?.status === 'ok';

  useEffect(() => {
    if (cameras.length > 0) {
      if (!selectedCamera || !cameras.find(c => c.id === selectedCamera)) {
        setSelectedCamera(cameras[0].id);
      }
    } else {
      setSelectedCamera(null);
    }
  }, [cameras, selectedStore]);

  const activeCam = cameras.find(c => c.id === selectedCamera) || cameras[0];

  return (
    <div className="glass-card">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
        <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
          Live Store Feed
          {selectedStore !== 'shared' && cameras.length > 1 && (
            <select 
              value={selectedCamera || ''} 
              onChange={(e) => setSelectedCamera(e.target.value)}
              style={{
                marginLeft: '12px',
                background: 'rgba(255,255,255,0.1)',
                border: '1px solid rgba(255,255,255,0.2)',
                color: 'white',
                borderRadius: '6px',
                padding: '4px 8px',
                fontSize: '13px'
              }}
            >
              {cameras.map(cam => (
                <option key={cam.id} value={cam.id} style={{ background: '#111' }}>
                  {cam.name}
                </option>
              ))}
            </select>
          )}
        </h3>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {isLive ? (
            <span className="health-badge live" style={{ fontSize: '11px', padding: '3px 10px', borderRadius: '12px' }}>
              <Wifi size={12} /> LIVE
            </span>
          ) : (
            <span className="health-badge stale" style={{ fontSize: '11px', padding: '3px 10px', borderRadius: '12px' }}>
              <WifiOff size={12} /> OFFLINE
            </span>
          )}
        </div>
      </div>

      {selectedStore === 'shared' && feedAvailable ? (
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '12px'
        }}>
          {cameras.slice(0, 4).map((cam) => (
            <div key={cam.id} style={{ position: 'relative', borderRadius: '8px', overflow: 'hidden', background: '#0a0a0a', aspectRatio: '16/9' }}>
              <video
                src={`/api/v1/feed/video?store_id=${cam.store_id}&camera_id=${cam.id}`}
                autoPlay muted loop playsInline
                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
              />
              <div style={{
                position: 'absolute', top: '8px', left: '8px',
                background: 'rgba(0,0,0,0.7)', color: '#fff',
                padding: '2px 8px', borderRadius: '4px', fontSize: '10px',
                backdropFilter: 'blur(4px)',
              }}>
                {cam.store_id} - {cam.name}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div style={{
          borderRadius: '12px',
          overflow: 'hidden',
          background: '#0a0a0a',
          aspectRatio: '16/9',
          position: 'relative',
        }}>
          {feedAvailable && activeCam ? (
            <video
              key={`${selectedStore}-${activeCam.id}`}
              src={`/api/v1/feed/video?store_id=${selectedStore}&camera_id=${activeCam.id}`}
              autoPlay
              muted
              loop
              playsInline
              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            />
          ) : (
            <div style={{
              display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
              height: '100%', color: 'var(--color-text-muted)', gap: '12px',
            }}>
              <Video size={48} style={{ opacity: 0.3 }} />
              <span>No camera feed available</span>
            </div>
          )}

          {feedAvailable && activeCam && (
            <div style={{
              position: 'absolute', top: '12px', left: '12px',
              background: 'rgba(0,0,0,0.7)', color: '#fff',
              padding: '4px 12px', borderRadius: '8px', fontSize: '11px',
              display: 'flex', alignItems: 'center', gap: '6px',
              backdropFilter: 'blur(4px)',
            }}>
              <div style={{
                width: '8px', height: '8px', borderRadius: '50%',
                background: isLive ? '#22c55e' : '#ef4444',
                animation: isLive ? 'pulse 2s infinite' : 'none',
              }} />
              REC — {activeCam.name}
            </div>
          )}
        </div>
      )}

      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)',
        gap: '12px', marginTop: '16px',
      }}>
        <div className="feed-meta-item">
          <span className="color-text-muted" style={{ fontSize: '11px' }}>Store</span>
          <span style={{ fontWeight: 600, fontSize: '13px' }}>{selectedStore === 'shared' ? 'All Stores' : selectedStore}</span>
        </div>
        <div className="feed-meta-item">
          <span className="color-text-muted" style={{ fontSize: '11px' }}>Cameras</span>
          <span style={{ fontWeight: 600, fontSize: '13px' }}>{cameras.length} Active</span>
        </div>
        <div className="feed-meta-item">
          <span className="color-text-muted" style={{ fontSize: '11px' }}>Status</span>
          <span style={{ fontWeight: 600, fontSize: '13px', color: isLive ? 'var(--color-success)' : 'var(--color-danger)' }}>
            {isLive ? 'Online' : 'Offline'}
          </span>
        </div>
        <div className="feed-meta-item">
          <span className="color-text-muted" style={{ fontSize: '11px' }}>Primary Feed</span>
          <span style={{ fontWeight: 600, fontSize: '13px' }}>{activeCam?.name || 'N/A'}</span>
        </div>
      </div>
    </div>
  );
}
