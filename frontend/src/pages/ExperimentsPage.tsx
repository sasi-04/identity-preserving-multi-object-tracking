import { useEffect, useState, type FC } from 'react';
import {
  FlaskConical,
  Play,
  Download,
  CheckCircle2,
  RefreshCw
} from 'lucide-react';
import { fetchExperiments, runAblationStudy, runExperiment } from '../services/api';
import type { ExperimentRun } from '../types/tracking';

export const ExperimentsPage: FC = () => {
  const [experiments, setExperiments] = useState<ExperimentRun[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [ablationResults, setAblationResults] = useState<any>(null);
  const [expName, setExpName] = useState<string>('Custom Occlusion Run');
  const [useOie, setUseOie] = useState<boolean>(true);

  const loadExperiments = () => {
    fetchExperiments().then(setExperiments).catch(console.error);
  };

  useEffect(() => {
    loadExperiments();
  }, []);

  const handleRunAblation = async () => {
    setLoading(true);
    try {
      const res = await runAblationStudy();
      setAblationResults(res.results);
      loadExperiments();
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleRunSingle = async () => {
    setLoading(true);
    try {
      await runExperiment(expName, { enable_oie: useOie });
      loadExperiments();
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleExportJson = (exp: ExperimentRun) => {
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(exp, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `zed_experiment_${exp.id}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Top Action Panel */}
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
            Ablation & Experiment Management
          </h2>
          <p style={{ fontSize: '12.5px', color: 'var(--text-secondary)' }}>
            Empirically validate tracking improvements across Baseline vs OIE components under dense crowd conditions.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <button className="btn-secondary" onClick={loadExperiments} disabled={loading}>
            <RefreshCw size={14} />
            <span>Refresh</span>
          </button>
          <button className="btn-primary" onClick={handleRunAblation} disabled={loading}>
            <FlaskConical size={15} />
            <span>{loading ? 'Executing Ablation...' : 'Run 5-Config Ablation Study'}</span>
          </button>
        </div>
      </div>

      {/* Latest Ablation Matrix Table (if available) */}
      {ablationResults && (
        <div className="zed-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
            <CheckCircle2 size={16} color="var(--color-confirmed)" />
            <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#fff' }}>
              Latest Ablation Study Results
            </h3>
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table className="zed-table">
              <thead>
                <tr>
                  <th>Configuration</th>
                  <th>IDF1 (%)</th>
                  <th>IDSW (Count)</th>
                  <th>MOTA (%)</th>
                  <th>HOTA (%)</th>
                  <th>DetA (%)</th>
                  <th>AssA (%)</th>
                  <th>FPS</th>
                  <th>Latency</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(ablationResults).map(([key, val]: [string, any]) => {
                  const isFullOie = key.includes('Full_OIE');
                  return (
                    <tr
                      key={key}
                      style={{
                        background: isFullOie ? 'rgba(239, 68, 68, 0.08)' : undefined,
                        fontWeight: isFullOie ? 600 : 400,
                      }}
                    >
                      <td style={{ color: isFullOie ? 'var(--zed-red)' : '#fff' }}>
                        {key.replace(/_/g, ' ')}
                      </td>
                      <td style={{ fontFamily: 'JetBrains Mono' }}>{val.idf1}%</td>
                      <td style={{ fontFamily: 'JetBrains Mono', color: val.idsw <= 5 ? 'var(--color-confirmed)' : 'var(--color-occluded)' }}>
                        {val.idsw}
                      </td>
                      <td style={{ fontFamily: 'JetBrains Mono' }}>{val.mota}%</td>
                      <td style={{ fontFamily: 'JetBrains Mono' }}>{val.hota}%</td>
                      <td style={{ fontFamily: 'JetBrains Mono' }}>{val.deta}%</td>
                      <td style={{ fontFamily: 'JetBrains Mono' }}>{val.assa}%</td>
                      <td style={{ fontFamily: 'JetBrains Mono' }}>{val.fps}</td>
                      <td style={{ fontFamily: 'JetBrains Mono' }}>{val.latency_ms}ms</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Run Single Experiment Panel */}
      <div className="zed-card">
        <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#fff', marginBottom: '0.75rem' }}>
          Execute Custom Benchmark Experiment
        </h3>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <input
            type="text"
            value={expName}
            onChange={(e) => setExpName(e.target.value)}
            placeholder="Experiment Name"
            style={{
              background: 'var(--bg-tertiary)',
              color: '#fff',
              border: '1px solid var(--border-subtle)',
              borderRadius: '6px',
              padding: '0.5rem 0.85rem',
              fontSize: '13px',
              minWidth: '240px',
            }}
          />
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '13px', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={useOie}
              onChange={(e) => setUseOie(e.target.checked)}
              style={{ accentColor: 'var(--zed-red)' }}
            />
            <span>Enable Occlusion Intelligence Engine (OIE)</span>
          </label>
          <button className="btn-secondary" onClick={handleRunSingle} disabled={loading}>
            <Play size={14} fill="currentColor" />
            <span>Run Benchmark</span>
          </button>
        </div>
      </div>

      {/* Persisted Experiment Runs Table */}
      <div className="zed-card">
        <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#fff', marginBottom: '1rem' }}>
          Persisted Experiment Runs (SQLite)
        </h3>
        <div style={{ overflowX: 'auto' }}>
          <table className="zed-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Engine</th>
                <th>IDF1</th>
                <th>IDSW</th>
                <th>MOTA</th>
                <th>HOTA</th>
                <th>FPS</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {experiments.length > 0 ? (
                experiments.map((exp) => (
                  <tr key={exp.id}>
                    <td style={{ fontFamily: 'JetBrains Mono', fontSize: '12px' }}>{exp.id.slice(0, 16)}</td>
                    <td style={{ fontWeight: 600 }}>{exp.name}</td>
                    <td>
                      <span className={`badge ${exp.is_oie ? 'badge-confirmed' : 'badge-tentative'}`}>
                        {exp.is_oie ? 'OIE ACTIVE' : 'BASELINE'}
                      </span>
                    </td>
                    <td style={{ fontFamily: 'JetBrains Mono' }}>{exp.metrics?.idf1 ?? 'N/A'}%</td>
                    <td style={{ fontFamily: 'JetBrains Mono' }}>{exp.metrics?.idsw ?? 'N/A'}</td>
                    <td style={{ fontFamily: 'JetBrains Mono' }}>{exp.metrics?.mota ?? 'N/A'}%</td>
                    <td style={{ fontFamily: 'JetBrains Mono' }}>{exp.metrics?.hota ?? 'N/A'}%</td>
                    <td style={{ fontFamily: 'JetBrains Mono' }}>{exp.metrics?.fps ?? 'N/A'}</td>
                    <td>
                      <button
                        className="btn-secondary"
                        style={{ padding: '0.3rem 0.6rem', fontSize: '12px' }}
                        onClick={() => handleExportJson(exp)}
                        title="Download JSON run results"
                      >
                        <Download size={12} />
                        <span>Export</span>
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={9} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '2.5rem' }}>
                    No persisted experiment runs found. Click "Run 5-Config Ablation Study" above.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
