import { useState, type FC } from 'react';
import {
  Sliders,
  Shield,
  Save,
  RotateCcw,
  Check
} from 'lucide-react';
import type { TrackerSettings } from '../types/tracking';

interface SettingsPageProps {
  settings: TrackerSettings;
  onSaveSettings: (newSettings: TrackerSettings) => void;
}

export const SettingsPage: FC<SettingsPageProps> = ({
  settings: initialSettings,
  onSaveSettings
}) => {
  const [form, setForm] = useState<TrackerSettings>(initialSettings);
  const [savedSuccess, setSavedSuccess] = useState<boolean>(false);

  const defaultSettings: TrackerSettings = {
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

  const handleSave = () => {
    onSaveSettings(form);
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 2500);
  };

  const handleReset = () => {
    setForm(defaultSettings);
    onSaveSettings(defaultSettings);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', maxWidth: '1000px' }}>
      {/* Action Header */}
      <div
        className="zed-card"
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <div>
          <h2 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#fff', marginBottom: '0.25rem' }}>
            Algorithmic Hyperparameters & Privacy Policy
          </h2>
          <p style={{ fontSize: '12.5px', color: 'var(--text-secondary)' }}>
            Configure Kalman motion gating, cost matrix weights, and Occlusion Intelligence Engine policies.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button className="btn-secondary" onClick={handleReset}>
            <RotateCcw size={14} />
            <span>Reset Defaults</span>
          </button>
          <button className="btn-primary" onClick={handleSave}>
            {savedSuccess ? <Check size={15} /> : <Save size={15} />}
            <span>{savedSuccess ? 'Settings Saved' : 'Save Parameters'}</span>
          </button>
        </div>
      </div>

      {/* Occlusion Intelligence Engine Section */}
      <div className="zed-card">
        <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#fff', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Sliders size={16} color="var(--zed-red)" />
          Occlusion Intelligence Engine (OIE) Configuration
        </h3>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.25rem' }}>
          <label style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={form.enable_oie}
              onChange={(e) => setForm({ ...form, enable_oie: e.target.checked })}
              style={{ accentColor: 'var(--zed-red)', marginTop: '0.2rem' }}
            />
            <div>
              <div style={{ fontWeight: 600, color: '#fff', fontSize: '13.5px' }}>Enable Master OIE Engine</div>
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Toggle OIE innovations vs raw ByteTrack baseline</div>
            </div>
          </label>

          <label style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={form.enable_uncertainty_recovery}
              onChange={(e) => setForm({ ...form, enable_uncertainty_recovery: e.target.checked })}
              style={{ accentColor: 'var(--zed-red)', marginTop: '0.2rem' }}
            />
            <div>
              <div style={{ fontWeight: 600, color: '#fff', fontSize: '13.5px' }}>Uncertainty-Aware Gating</div>
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Expand spatial search radius proportional to covariance &sigma;</div>
            </div>
          </label>

          <label style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={form.enable_adaptive_weights}
              onChange={(e) => setForm({ ...form, enable_adaptive_weights: e.target.checked })}
              style={{ accentColor: 'var(--zed-red)', marginTop: '0.2rem' }}
            />
            <div>
              <div style={{ fontWeight: 600, color: '#fff', fontSize: '13.5px' }}>Adaptive Visibility Weighting</div>
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Downweight appearance when crop has mutual overlap &gt; 30%</div>
            </div>
          </label>

          <label style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={form.enable_temporal_memory}
              onChange={(e) => setForm({ ...form, enable_temporal_memory: e.target.checked })}
              style={{ accentColor: 'var(--zed-red)', marginTop: '0.2rem' }}
            />
            <div>
              <div style={{ fontWeight: 600, color: '#fff', fontSize: '13.5px' }}>Anti-Pollution Temporal Memory</div>
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Store clean crops only to prevent corrupting gallery</div>
            </div>
          </label>

          <label style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={form.enable_ambiguity_rejection}
              onChange={(e) => setForm({ ...form, enable_ambiguity_rejection: e.target.checked })}
              style={{ accentColor: 'var(--zed-red)', marginTop: '0.2rem' }}
            />
            <div>
              <div style={{ fontWeight: 600, color: '#fff', fontSize: '13.5px' }}>Ambiguity-Aware Rejection</div>
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Reject assignment when 1st vs 2nd best margin &lt; &tau;</div>
            </div>
          </label>
        </div>

        {/* Ambiguity margin slider */}
        <div style={{ marginTop: '1.25rem', paddingTop: '1rem', borderTop: '1px solid var(--border-subtle)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
            <span style={{ fontSize: '13px', fontWeight: 600, color: '#fff' }}>Ambiguity Margin Threshold (&tau;):</span>
            <span style={{ fontFamily: 'JetBrains Mono', color: 'var(--zed-red)' }}>{form.ambiguity_margin_threshold.toFixed(2)}</span>
          </div>
          <input
            type="range"
            min="0.04"
            max="0.30"
            step="0.01"
            value={form.ambiguity_margin_threshold}
            onChange={(e) => setForm({ ...form, ambiguity_margin_threshold: parseFloat(e.target.value) })}
            style={{ width: '100%' }}
          />
        </div>
      </div>

      {/* Association Weights & Lifespans */}
      <div className="zed-card">
        <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#fff', marginBottom: '1rem' }}>
          Cost Matrix Weights & Lifecycle Timeouts
        </h3>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.25rem' }}>
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem', fontSize: '12.5px' }}>
              <span>Motion Weight (w_mot):</span>
              <span style={{ fontFamily: 'JetBrains Mono' }}>{form.weight_motion.toFixed(2)}</span>
            </div>
            <input
              type="range"
              min="0.0"
              max="1.0"
              step="0.05"
              value={form.weight_motion}
              onChange={(e) => setForm({ ...form, weight_motion: parseFloat(e.target.value) })}
              style={{ width: '100%' }}
            />
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem', fontSize: '12.5px' }}>
              <span>Appearance Weight (w_app):</span>
              <span style={{ fontFamily: 'JetBrains Mono' }}>{form.weight_appearance.toFixed(2)}</span>
            </div>
            <input
              type="range"
              min="0.0"
              max="1.0"
              step="0.05"
              value={form.weight_appearance}
              onChange={(e) => setForm({ ...form, weight_appearance: parseFloat(e.target.value) })}
              style={{ width: '100%' }}
            />
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem', fontSize: '12.5px' }}>
              <span>Geometry Weight (w_geom):</span>
              <span style={{ fontFamily: 'JetBrains Mono' }}>{form.weight_geometry.toFixed(2)}</span>
            </div>
            <input
              type="range"
              min="0.0"
              max="1.0"
              step="0.05"
              value={form.weight_geometry}
              onChange={(e) => setForm({ ...form, weight_geometry: parseFloat(e.target.value) })}
              style={{ width: '100%' }}
            />
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem', fontSize: '12.5px' }}>
              <span>Lost Timeout Frames:</span>
              <span style={{ fontFamily: 'JetBrains Mono' }}>{form.lost_timeout_frames} frames</span>
            </div>
            <input
              type="range"
              min="5"
              max="45"
              step="1"
              value={form.lost_timeout_frames}
              onChange={(e) => setForm({ ...form, lost_timeout_frames: parseInt(e.target.value) })}
              style={{ width: '100%' }}
            />
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem', fontSize: '12.5px' }}>
              <span>Max Occlusion Lifespan:</span>
              <span style={{ fontFamily: 'JetBrains Mono' }}>{form.max_lost_frames} frames</span>
            </div>
            <input
              type="range"
              min="20"
              max="150"
              step="5"
              value={form.max_lost_frames}
              onChange={(e) => setForm({ ...form, max_lost_frames: parseInt(e.target.value) })}
              style={{ width: '100%' }}
            />
          </div>
        </div>
      </div>

      {/* Privacy & Governance Notice */}
      <div
        className="zed-card"
        style={{
          borderLeft: '4px solid var(--color-confirmed)',
          display: 'flex',
          gap: '1rem',
          alignItems: 'flex-start',
        }}
      >
        <Shield size={22} color="var(--color-confirmed)" style={{ flexShrink: 0, marginTop: '2px' }} />
        <div>
          <div style={{ fontWeight: 700, color: '#fff', fontSize: '14px', marginBottom: '0.25rem' }}>
            Anonymous Tracking & Ephemeral Storage Compliance
          </div>
          <p style={{ fontSize: '12.5px', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
            ZED VISION strictly enforces anonymous track identifiers. Facial biometrics, demographic inference,
            and cross-camera persistence are permanently disabled. Video inputs and frame caches are stored strictly
            in local ephemeral session storage and expunged upon session reset.
          </p>
        </div>
      </div>
    </div>
  );
};
