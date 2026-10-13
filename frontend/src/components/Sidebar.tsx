import type { FC, ReactNode } from 'react';
import {
  LayoutDashboard,
  Video,
  EyeOff,
  BarChart3,
  FlaskConical,
  Database,
  Sliders,
  Cpu,
  ShieldCheck,
  FileText
} from 'lucide-react';


export type PageId =
  | 'overview'
  | 'live_tracking'
  | 'occlusion_lab'
  | 'analytics'
  | 'experiments'
  | 'datasets'
  | 'settings';

interface SidebarProps {
  activePage: PageId;
  onSelectPage: (page: PageId) => void;
  activeSessionId?: string | null;
}

export const Sidebar: FC<SidebarProps> = ({
  activePage,
  onSelectPage,
  activeSessionId
}) => {
  const navItems: { id: PageId; label: string; icon: ReactNode }[] = [
    { id: 'overview', label: 'Overview', icon: <LayoutDashboard size={18} /> },
    { id: 'live_tracking', label: 'Live Tracking', icon: <Video size={18} /> },
    { id: 'occlusion_lab', label: 'Occlusion Lab', icon: <EyeOff size={18} /> },
    { id: 'analytics', label: 'Analytics', icon: <BarChart3 size={18} /> },
    { id: 'experiments', label: 'Experiments', icon: <FlaskConical size={18} /> },
    { id: 'datasets', label: 'Datasets & Eval', icon: <Database size={18} /> },
    { id: 'settings', label: 'Settings', icon: <Sliders size={18} /> },
  ];

  return (
    <aside
      style={{
        width: '240px',
        background: 'var(--bg-secondary)',
        borderRight: '1px solid var(--border-subtle)',
        display: 'flex',
        flexDirection: 'column',
        flexShrink: 0,
        height: '100vh',
        position: 'sticky',
        top: 0,
      }}
    >
      {/* Brand Header */}
      <div
        style={{
          padding: '1.25rem 1.25rem',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
        }}
      >
        <div
          style={{
            width: '32px',
            height: '32px',
            borderRadius: '6px',
            background: 'var(--zed-red)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            fontWeight: 800,
            fontSize: '15px',
            letterSpacing: '-0.5px',
          }}
        >
          ZV
        </div>
        <div>
          <div style={{ fontWeight: 700, fontSize: '15px', letterSpacing: '0.02em', color: '#fff' }}>
            ZED VISION
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Occlusion MOT (PS-2)
          </div>
        </div>
      </div>

      {/* Navigation List */}
      <nav style={{ padding: '1rem 0.75rem', flex: 1, display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
        {navItems.map((item) => {
          const isActive = activePage === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectPage(item.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                width: '100%',
                padding: '0.6rem 0.85rem',
                borderRadius: '6px',
                border: 'none',
                background: isActive ? 'var(--bg-tertiary)' : 'transparent',
                color: isActive ? '#ffffff' : 'var(--text-secondary)',
                fontWeight: isActive ? 600 : 500,
                fontSize: '13.5px',
                cursor: 'pointer',
                textAlign: 'left',
                transition: 'all 0.15s ease',
                borderLeft: isActive ? '3px solid var(--zed-red)' : '3px solid transparent',
              }}
            >
              <span style={{ color: isActive ? 'var(--zed-red)' : 'var(--text-muted)' }}>
                {item.icon}
              </span>
              <span>{item.label}</span>
              {item.id === 'live_tracking' && activeSessionId && (
                <span
                  style={{
                    marginLeft: 'auto',
                    width: '7px',
                    height: '7px',
                    borderRadius: '50%',
                    background: 'var(--color-confirmed)',
                    boxShadow: '0 0 6px var(--color-confirmed)',
                  }}
                />
              )}
            </button>
          );
        })}
      </nav>

      {/* System Status Footer */}
      <div
        style={{
          padding: '1rem 1.25rem',
          borderTop: '1px solid var(--border-subtle)',
          fontSize: '11.5px',
          color: 'var(--text-muted)',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.65rem',
        }}
      >
        <a
          href="http://127.0.0.1:8080/manual.pdf"
          target="_blank"
          rel="noreferrer"
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '0.5rem',
            padding: '0.55rem 0.75rem',
            borderRadius: '6px',
            background: 'rgba(230, 57, 70, 0.12)',
            border: '1px solid rgba(230, 57, 70, 0.35)',
            color: '#ff6b6b',
            textDecoration: 'none',
            fontSize: '12px',
            fontWeight: 600,
            transition: 'all 0.15s ease',
          }}
          title="Open Official User Manual (PDF)"
        >
          <FileText size={15} />
          <span>User Manual (PDF)</span>
        </a>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <ShieldCheck size={14} color="var(--color-confirmed)" />
          <span>OIE Engine: Active</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Cpu size={14} color="var(--text-secondary)" />
          <span>Mode: CPU Causal (Low Res)</span>
        </div>
      </div>

    </aside>
  );
};
