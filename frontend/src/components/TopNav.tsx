import type { FC } from 'react';
import { Activity, Server } from 'lucide-react';
import type { PageId } from './Sidebar';

interface TopNavProps {
  activePage: PageId;
  backendHealthy: boolean;
  activeSessionId?: string | null;
  currentFps?: number;
}

export const TopNav: FC<TopNavProps> = ({
  activePage,
  backendHealthy,
  activeSessionId,
  currentFps = 0
}) => {
  const pageTitles: Record<PageId, { title: string; subtitle: string }> = {
    overview: {
      title: 'System Overview',
      subtitle: 'Real-time telemetry, model status, and empirical tracking performance'
    },
    live_tracking: {
      title: 'Live Tracking Studio',
      subtitle: 'Online multi-object tracking through dense transit gate occlusion'
    },
    occlusion_lab: {
      title: 'Occlusion Intelligence Lab',
      subtitle: 'Event explainability, candidate gating, and ambiguity rejection diagnostics'
    },
    analytics: {
      title: 'Crowd Flow & Performance Analytics',
      subtitle: 'Latency profiles, crowd pressure indexing, and comparative metrics'
    },
    experiments: {
      title: 'Experiment & Ablation Manager',
      subtitle: 'Quantitative benchmarking, baseline vs OIE ablation, and SQLite persistence'
    },
    datasets: {
      title: 'Datasets & MOT Evaluation Protocols',
      subtitle: 'MOTChallenge standards (IDF1, IDSW, MOTA, HOTA) and synthetic generator'
    },
    settings: {
      title: 'Tracking & Algorithmic Parameters',
      subtitle: 'Tune detector thresholds, Kalman gating, OIE weights, and privacy retention'
    }
  };

  const { title, subtitle } = pageTitles[activePage] || { title: 'ZED VISION', subtitle: '' };

  return (
    <header
      style={{
        height: '64px',
        background: 'var(--bg-secondary)',
        borderBottom: '1px solid var(--border-subtle)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 2rem',
        position: 'sticky',
        top: 0,
        zIndex: 10,
      }}
    >
      <div>
        <h1 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#ffffff' }}>
          {title}
        </h1>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
          {subtitle}
        </p>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        {/* Real-time FPS tag */}
        {currentFps > 0 && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              background: 'var(--bg-tertiary)',
              padding: '0.35rem 0.75rem',
              borderRadius: '6px',
              fontSize: '12px',
              fontFamily: 'JetBrains Mono',
              border: '1px solid var(--border-subtle)',
            }}
          >
            <Activity size={13} color="var(--color-confirmed)" />
            <span>{currentFps.toFixed(1)} FPS</span>
          </div>
        )}

        {/* Active Session Tag */}
        {activeSessionId && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              background: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid rgba(239, 68, 68, 0.25)',
              padding: '0.35rem 0.75rem',
              borderRadius: '6px',
              fontSize: '12px',
              color: 'var(--zed-red)',
              fontWeight: 500,
            }}
          >
            <span
              style={{
                width: '6px',
                height: '6px',
                borderRadius: '50%',
                background: 'var(--zed-red)',
              }}
            />
            <span>Session: #{activeSessionId}</span>
          </div>
        )}

        {/* Backend Health Badge */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            background: backendHealthy ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
            border: `1px solid ${backendHealthy ? 'rgba(16, 185, 129, 0.25)' : 'rgba(239, 68, 68, 0.25)'}`,
            padding: '0.35rem 0.75rem',
            borderRadius: '6px',
            fontSize: '12px',
            color: backendHealthy ? 'var(--color-confirmed)' : 'var(--zed-red)',
            fontWeight: 500,
          }}
        >
          <Server size={13} />
          <span>{backendHealthy ? 'API Online' : 'API Connecting...'}</span>
        </div>
      </div>
    </header>
  );
};
