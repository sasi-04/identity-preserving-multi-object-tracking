import { useEffect, useState, type FC } from 'react';
import {
  EyeOff,
  ShieldAlert,
  CheckCircle2
} from 'lucide-react';
import { fetchSessionEvents } from '../services/api';
import type { DiagnosticRecord } from '../types/tracking';

interface OcclusionLabProps {
  activeSessionId: string | null;
}

export const OcclusionLab: FC<OcclusionLabProps> = ({ activeSessionId }) => {
  const [events, setEvents] = useState<DiagnosticRecord[]>([]);
  const [selectedEvent, setSelectedEvent] = useState<DiagnosticRecord | null>(null);
  const [filterType, setFilterType] = useState<string>('ALL');

  useEffect(() => {
    if (activeSessionId) {
      fetchSessionEvents(activeSessionId)
        .then((data) => {
          setEvents(data.events || []);
          if (data.events && data.events.length > 0) {
            setSelectedEvent(data.events[data.events.length - 1]);
          }
        })
        .catch(console.error);
    }
  }, [activeSessionId]);

  const filteredEvents = events.filter((e) => {
    if (filterType === 'ALL') return true;
    return e.event_type === filterType;
  });

  const recoveriesCount = events.filter((e) => e.event_type === 'RECOVERY_CONFIRMED').length;
  const ambiguousCount = events.filter((e) => e.event_type === 'AMBIGUOUS_REJECTED').length;
  const occludedCount = events.filter((e) => e.event_type === 'OCCLUSION_ENTER').length;

  return (
    <div>
      {/* Header Metric Cards */}
      <div className="kpi-grid">
        <div className="zed-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '12px', fontWeight: 600 }}>Confirmed Recoveries</span>
            <CheckCircle2 size={16} color="var(--color-confirmed)" />
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--color-confirmed)' }}>
            {recoveriesCount}
          </div>
          <div style={{ fontSize: '11.5px', color: 'var(--text-secondary)' }}>
            Re-associations supported by multi-cue evidence
          </div>
        </div>

        <div className="zed-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '12px', fontWeight: 600 }}>Ambiguous Rejections</span>
            <ShieldAlert size={16} color="var(--zed-red)" />
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--zed-red)' }}>
            {ambiguousCount}
          </div>
          <div style={{ fontSize: '11.5px', color: 'var(--text-secondary)' }}>
            Potential ID switches prevented by margin gating
          </div>
        </div>

        <div className="zed-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '12px', fontWeight: 600 }}>Occlusion Entries</span>
            <EyeOff size={16} color="var(--color-occluded)" />
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--color-occluded)' }}>
            {occludedCount}
          </div>
          <div style={{ fontSize: '11.5px', color: 'var(--text-secondary)' }}>
            Tracks entering temporary mutual occlusion
          </div>
        </div>
      </div>

      {/* Main Occlusion Event Inspection Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 420px', gap: '1.25rem' }}>
        {/* Events Table */}
        <div className="zed-card" style={{ display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#fff' }}>
              Occlusion & Recovery Diagnostics Feed
            </h3>
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              style={{
                background: 'var(--bg-tertiary)',
                color: '#fff',
                border: '1px solid var(--border-subtle)',
                borderRadius: '6px',
                padding: '0.35rem 0.65rem',
                fontSize: '12px',
              }}
            >
              <option value="ALL">All Diagnostic Events</option>
              <option value="RECOVERY_CONFIRMED">Recoveries Confirmed</option>
              <option value="AMBIGUOUS_REJECTED">Ambiguous Rejections</option>
              <option value="OCCLUSION_ENTER">Occlusion Entries</option>
              <option value="LOST_ENTER">Lost Entries</option>
            </select>
          </div>

          <div style={{ overflowX: 'auto', maxHeight: '520px', overflowY: 'auto' }}>
            <table className="zed-table">
              <thead>
                <tr>
                  <th>Frame</th>
                  <th>Track</th>
                  <th>Event Type</th>
                  <th>Cost Breakdown</th>
                  <th>Decision Summary</th>
                </tr>
              </thead>
              <tbody>
                {filteredEvents.length > 0 ? (
                  filteredEvents.map((ev, i) => {
                    let badgeClass = 'badge-confirmed';
                    if (ev.event_type === 'AMBIGUOUS_REJECTED') badgeClass = 'badge-recovered';
                    else if (ev.event_type === 'OCCLUSION_ENTER' || ev.event_type === 'LOST_ENTER') badgeClass = 'badge-occluded';

                    const isSelected = selectedEvent === ev;

                    return (
                      <tr
                        key={i}
                        onClick={() => setSelectedEvent(ev)}
                        style={{
                          cursor: 'pointer',
                          background: isSelected ? 'rgba(239, 68, 68, 0.08)' : undefined,
                        }}
                      >
                        <td style={{ fontFamily: 'JetBrains Mono' }}>#{ev.frame_idx}</td>
                        <td style={{ fontWeight: 700, fontFamily: 'JetBrains Mono' }}>#{ev.track_id}</td>
                        <td>
                          <span className={`badge ${badgeClass}`}>
                            {ev.event_type.replace('_', ' ')}
                          </span>
                        </td>
                        <td style={{ fontFamily: 'JetBrains Mono', fontSize: '11.5px' }}>
                          M:{ev.motion_cost.toFixed(2)} | A:{ev.appearance_cost.toFixed(2)} | G:{ev.geometry_cost.toFixed(2)}
                        </td>
                        <td style={{ maxWidth: '280px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {ev.decision_reason}
                        </td>
                      </tr>
                    );
                  })
                ) : (
                  <tr>
                    <td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '3rem' }}>
                      No diagnostic events logged yet. Advance the video session in Live Tracking Studio.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Selected Event Detail Inspector */}
        <div className="zed-card">
          <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#fff', marginBottom: '1rem' }}>
            Explainability Inspector
          </h3>

          {selectedEvent ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', fontSize: '13px' }}>
              <div
                style={{
                  background: 'var(--bg-tertiary)',
                  padding: '0.85rem',
                  borderRadius: '6px',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <div style={{ color: 'var(--text-muted)', fontSize: '11px', textTransform: 'uppercase', marginBottom: '0.25rem' }}>
                  Decision Policy Rationale
                </div>
                <div style={{ color: '#fff', fontWeight: 500, lineHeight: 1.4 }}>
                  {selectedEvent.decision_reason}
                </div>
              </div>

              <div>
                <div style={{ color: 'var(--text-muted)', fontSize: '11.5px', marginBottom: '0.5rem', fontWeight: 600 }}>
                  Association Cost Decomposition
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.2rem' }}>
                      <span style={{ color: 'var(--text-secondary)' }}>Motion Cost (Mahalanobis):</span>
                      <span style={{ fontFamily: 'JetBrains Mono' }}>{selectedEvent.motion_cost.toFixed(3)}</span>
                    </div>
                    <div style={{ height: '4px', background: 'var(--border-subtle)', borderRadius: '2px', overflow: 'hidden' }}>
                      <div style={{ width: `${Math.min(100, selectedEvent.motion_cost * 100)}%`, height: '100%', background: '#3b82f6' }} />
                    </div>
                  </div>

                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.2rem' }}>
                      <span style={{ color: 'var(--text-secondary)' }}>Appearance Cost (Cosine):</span>
                      <span style={{ fontFamily: 'JetBrains Mono' }}>{selectedEvent.appearance_cost.toFixed(3)}</span>
                    </div>
                    <div style={{ height: '4px', background: 'var(--border-subtle)', borderRadius: '2px', overflow: 'hidden' }}>
                      <div style={{ width: `${Math.min(100, selectedEvent.appearance_cost * 100)}%`, height: '100%', background: '#8b5cf6' }} />
                    </div>
                  </div>

                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.2rem' }}>
                      <span style={{ color: 'var(--text-secondary)' }}>Geometry Cost (1 - IoU):</span>
                      <span style={{ fontFamily: 'JetBrains Mono' }}>{selectedEvent.geometry_cost.toFixed(3)}</span>
                    </div>
                    <div style={{ height: '4px', background: 'var(--border-subtle)', borderRadius: '2px', overflow: 'hidden' }}>
                      <div style={{ width: `${Math.min(100, selectedEvent.geometry_cost * 100)}%`, height: '100%', background: '#10b981' }} />
                    </div>
                  </div>
                </div>
              </div>

              {selectedEvent.ambiguity_margin !== null && selectedEvent.ambiguity_margin !== undefined && (
                <div
                  style={{
                    background: 'rgba(239, 68, 68, 0.1)',
                    border: '1px solid rgba(239, 68, 68, 0.25)',
                    padding: '0.75rem',
                    borderRadius: '6px',
                  }}
                >
                  <div style={{ color: 'var(--zed-red)', fontWeight: 600, marginBottom: '0.25rem' }}>
                    Ambiguity Margin: &Delta;C = {selectedEvent.ambiguity_margin.toFixed(3)}
                  </div>
                  <div style={{ fontSize: '11.5px', color: 'var(--text-secondary)' }}>
                    Difference between top candidate and competing distractor. When below threshold (0.12), association is safely rejected.
                  </div>
                </div>
              )}

              <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '0.75rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Spatial Uncertainty:</span>
                  <span style={{ fontFamily: 'JetBrains Mono', color: '#fff' }}>&sigma; = {selectedEvent.spatial_uncertainty_px} px</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Event Timestamp:</span>
                  <span style={{ fontFamily: 'JetBrains Mono', color: '#fff' }}>
                    {new Date(selectedEvent.timestamp * 1000).toLocaleTimeString()}
                  </span>
                </div>
              </div>
            </div>
          ) : (
            <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '3rem 1rem' }}>
              Select an event from the feed to view explainability details
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
