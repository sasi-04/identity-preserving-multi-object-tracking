import { useEffect, useState, type FC } from 'react';
import { Database, ExternalLink } from 'lucide-react';
import { fetchDatasetInfo } from '../services/api';

export const DatasetsPage: FC = () => {
  const [datasetInfo, setDatasetInfo] = useState<any>(null);

  useEffect(() => {
    fetchDatasetInfo().then(setDatasetInfo).catch(console.error);
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Top Banner */}
      <div className="zed-card">
        <h2 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#fff', marginBottom: '0.25rem' }}>
          MOT Evaluation Protocols & Dataset Architecture
        </h2>
        <p style={{ fontSize: '12.5px', color: 'var(--text-secondary)' }}>
          Identity-preserving multi-object tracking must be evaluated using standard CLEAR MOT and HOTA protocols
          against dense crowd occlusions.
        </p>
      </div>

      {/* Metrics Explanation Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
        <div className="zed-card">
          <div style={{ color: 'var(--zed-red)', fontWeight: 700, fontSize: '15px', marginBottom: '0.35rem' }}>
            IDF1 (Identification F1)
          </div>
          <p style={{ fontSize: '12.5px', color: 'var(--text-secondary)', lineHeight: 1.45 }}>
            Harmonic mean of identification precision and recall. Directly assesses whether a tracked pedestrian retains the exact same identity ID throughout mutual occlusions and disappearances.
          </p>
        </div>

        <div className="zed-card">
          <div style={{ color: 'var(--color-occluded)', fontWeight: 700, fontSize: '15px', marginBottom: '0.35rem' }}>
            ID Switches (IDSW)
          </div>
          <p style={{ fontSize: '12.5px', color: 'var(--text-secondary)', lineHeight: 1.45 }}>
            The total count of identity transfers where a ground truth subject is erroneously assigned a new or competing track ID. The primary baseline indicator for dense occlusion failure.
          </p>
        </div>

        <div className="zed-card">
          <div style={{ color: 'var(--color-confirmed)', fontWeight: 700, fontSize: '15px', marginBottom: '0.35rem' }}>
            MOTA (CLEAR MOT)
          </div>
          <p style={{ fontSize: '12.5px', color: 'var(--text-secondary)', lineHeight: 1.45 }}>
            Traditional benchmark composite score: <code>MOTA = 1 - (FN + FP + IDSW) / GT</code>. Heavily penalizes false negatives and false positives alongside tracking stability.
          </p>
        </div>

        <div className="zed-card">
          <div style={{ color: 'var(--color-tentative)', fontWeight: 700, fontSize: '15px', marginBottom: '0.35rem' }}>
            HOTA (Higher Order)
          </div>
          <p style={{ fontSize: '12.5px', color: 'var(--text-secondary)', lineHeight: 1.45 }}>
            Modern balanced MOT metric calculating the geometric mean of Detection Accuracy (DetA) and Association Accuracy (AssA): <code>HOTA = &radic;(DetA &times; AssA)</code>.
          </p>
        </div>
      </div>

      {/* Supported Benchmarks */}
      <div className="zed-card">
        <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#fff', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Database size={16} color="var(--zed-red)" />
          Supported Evaluation Benchmark Suites
        </h3>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {datasetInfo?.supported_benchmarks ? (
            datasetInfo.supported_benchmarks.map((ds: any, idx: number) => (
              <div
                key={idx}
                style={{
                  background: 'var(--bg-tertiary)',
                  padding: '1.1rem',
                  borderRadius: '6px',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                  <div style={{ fontWeight: 700, fontSize: '14px', color: '#fff' }}>{ds.name}</div>
                  {ds.url && (
                    <a
                      href={ds.url}
                      target="_blank"
                      rel="noreferrer"
                      style={{ color: 'var(--zed-red)', display: 'inline-flex', alignItems: 'center', gap: '0.3rem', fontSize: '12px', textDecoration: 'none' }}
                    >
                      <span>Website</span>
                      <ExternalLink size={12} />
                    </a>
                  )}
                  {ds.availability && (
                    <span className="badge badge-confirmed" style={{ fontSize: '10px' }}>
                      {ds.availability}
                    </span>
                  )}
                </div>
                <p style={{ fontSize: '12.5px', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
                  {ds.description}
                </p>
                <div style={{ display: 'flex', gap: '1rem', fontSize: '11.5px', color: 'var(--text-muted)' }}>
                  <span>Format: <code>{ds.annotations_format || 'Synthetic Frame Ground Truth'}</code></span>
                  {ds.licensing && <span>Licensing: {ds.licensing}</span>}
                </div>
              </div>
            ))
          ) : (
            <div style={{ color: 'var(--text-muted)' }}>Loading dataset details...</div>
          )}
        </div>
      </div>
    </div>
  );
};
