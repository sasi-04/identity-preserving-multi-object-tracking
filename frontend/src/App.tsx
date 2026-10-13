import { useEffect, useState } from 'react';
import { Sidebar, type PageId } from './components/Sidebar';
import { TopNav } from './components/TopNav';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { DatasetsPage } from './pages/DatasetsPage';
import { ExperimentsPage } from './pages/ExperimentsPage';
import { LiveTrackingStudio } from './pages/LiveTrackingStudio';
import { OcclusionLab } from './pages/OcclusionLab';
import { OverviewPage } from './pages/OverviewPage';
import { SettingsPage } from './pages/SettingsPage';
import { fetchHealth, fetchModelStatus, fetchSystemStatus } from './services/api';
import type { FrameTelemetry, TrackerSettings } from './types/tracking';

export function App() {
  const [activePage, setActivePage] = useState<PageId>('overview');
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [lastTelemetry, setLastTelemetry] = useState<FrameTelemetry | null>(null);

  // Backend state
  const [backendHealthy, setBackendHealthy] = useState<boolean>(false);
  const [modelStatus, setModelStatus] = useState<any>(null);
  const [systemStatus, setSystemStatus] = useState<any>(null);

  // Tracker settings state with local persistence
  const [settings, setSettings] = useState<TrackerSettings>(() => {
    try {
      const saved = localStorage.getItem('zed_tracker_settings');
      if (saved) return JSON.parse(saved);
    } catch (e) {
      // Fallback to default parameters
    }
    return {
      min_hits_to_confirm: 3,
      lost_timeout_frames: 15,
      max_lost_frames: 60,
      high_det_thresh: 0.50,
      low_det_thresh: 0.15,
      match_iou_thresh_stage1: 0.70,
      match_iou_thresh_stage2: 0.50,
      weight_motion: 0.30,
      weight_appearance: 0.40,
      weight_geometry: 0.30,
      enable_oie: true,
      enable_uncertainty_recovery: true,
      enable_adaptive_weights: true,
      enable_temporal_memory: true,
      enable_ambiguity_rejection: true,
      ambiguity_margin_threshold: 0.12,
      appearance_memory_size: 8,
      gap_penalty_factor: 0.15,
    };
  });

  const handleSaveSettings = (newSettings: TrackerSettings) => {
    setSettings(newSettings);
    localStorage.setItem('zed_tracker_settings', JSON.stringify(newSettings));
  };

  useEffect(() => {
    const checkBackend = () => {
      fetchHealth()
        .then(() => setBackendHealthy(true))
        .catch(() => setBackendHealthy(false));

      fetchModelStatus()
        .then(setModelStatus)
        .catch(console.error);

      fetchSystemStatus()
        .then(setSystemStatus)
        .catch(console.error);
    };

    checkBackend();
    const interval = setInterval(checkBackend, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="app-container">
      <Sidebar
        activePage={activePage}
        onSelectPage={setActivePage}
        activeSessionId={activeSessionId}
      />

      <div className="main-content">
        <TopNav
          activePage={activePage}
          backendHealthy={backendHealthy}
          activeSessionId={activeSessionId}
          currentFps={lastTelemetry?.fps ?? 0}
        />

        <main className="content-body">
          {activePage === 'overview' && (
            <OverviewPage
              onNavigate={setActivePage}
              modelStatus={modelStatus}
              systemStatus={systemStatus}
              activeSessionId={activeSessionId}
              lastTelemetry={lastTelemetry}
            />
          )}

          {activePage === 'live_tracking' && (
            <LiveTrackingStudio
              activeSessionId={activeSessionId}
              setActiveSessionId={setActiveSessionId}
              onTelemetryUpdate={setLastTelemetry}
              settings={settings}
            />
          )}

          {activePage === 'occlusion_lab' && (
            <OcclusionLab activeSessionId={activeSessionId} />
          )}

          {activePage === 'analytics' && (
            <AnalyticsPage lastTelemetry={lastTelemetry} />
          )}

          {activePage === 'experiments' && (
            <ExperimentsPage />
          )}

          {activePage === 'datasets' && (
            <DatasetsPage />
          )}

          {activePage === 'settings' && (
            <SettingsPage
              settings={settings}
              onSaveSettings={handleSaveSettings}
            />
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
