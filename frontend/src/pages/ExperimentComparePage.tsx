import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, GitCompare, TrendingUp, TrendingDown, Clock, AlertCircle } from 'lucide-react';
import { apiClient } from '../api/client';
import { Experiment, ExperimentComparison } from '../types';

export const ExperimentComparePage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [selectedVariantId, setSelectedVariantId] = useState<string>('');
  const [comparison, setComparison] = useState<ExperimentComparison | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiClient.listExperiments().then((list) => {
      const candidates = list.filter((e) => e.id !== id && e.status === 'COMPLETED');
      setExperiments(candidates);
      if (candidates.length > 0) {
        setSelectedVariantId(candidates[0].id);
      }
    });
  }, [id]);

  const handleCompare = async () => {
    if (!id || !selectedVariantId) return;
    try {
      setLoading(true);
      setError(null);
      const res = await apiClient.compareExperiments(id, selectedVariantId);
      setComparison(res);
    } catch (err: any) {
      setError(err.message || 'Failed to compare experiments');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedVariantId) {
      handleCompare();
    }
  }, [selectedVariantId]);

  return (
    <div>
      <div className="page-header">
        <div>
          <Link to={`/experiments/${id}`} className="nav-link" style={{ marginBottom: '0.5rem', display: 'inline-flex' }}>
            <ArrowLeft size={14} /> Back to Dashboard
          </Link>
          <h1 className="page-title">Differential Experiment Comparison</h1>
          <p className="page-subtitle">
            Compare aggregate synthetic behavior between baseline and variant application versions.
          </p>
        </div>
      </div>

      <div className="card" style={{ padding: '1rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <div style={{ fontWeight: 600 }}>Compare Baseline against Variant:</div>
        <select
          className="form-select"
          style={{ width: 'auto', minWidth: '300px' }}
          value={selectedVariantId}
          onChange={(e) => setSelectedVariantId(e.target.value)}
        >
          {experiments.length === 0 && <option value="">No other completed experiments available</option>}
          {experiments.map((exp) => (
            <option key={exp.id} value={exp.id}>
              {exp.name} ({exp.id.substring(0, 8)}...)
            </option>
          ))}
        </select>
        <button className="btn btn-primary" onClick={handleCompare} disabled={loading || !selectedVariantId}>
          <GitCompare size={14} /> Calculate Deltas
        </button>
      </div>

      {error && (
        <div className="card" style={{ borderColor: 'var(--accent-red)', color: '#f87171' }}>
          {error}
        </div>
      )}

      {comparison && (
        <div>
          {/* Summary Box */}
          <div className="card" style={{ borderLeft: '4px solid var(--accent-blue)' }}>
            <div style={{ fontSize: '0.95rem', lineHeight: 1.6 }}>
              {comparison.summary}
            </div>
          </div>

          {/* Deltas Scorecard */}
          <div className="metrics-grid">
            <div className="metric-card">
              <div className="metric-label">Completion Rate Shift</div>
              <div
                className="metric-value"
                style={{
                  color: comparison.completion_rate_delta >= 0 ? 'var(--accent-green)' : 'var(--accent-red)',
                }}
              >
                {comparison.completion_rate_delta >= 0 ? '+' : ''}
                {Math.round(comparison.completion_rate_delta * 100)}%
              </div>
              <div className="metric-sub">Variant vs Baseline</div>
            </div>

            <div className="metric-card">
              <div className="metric-label">Duration Delta</div>
              <div
                className="metric-value"
                style={{
                  color: comparison.duration_delta <= 0 ? 'var(--accent-green)' : 'var(--accent-amber)',
                }}
              >
                {comparison.duration_delta > 0 ? '+' : ''}
                {comparison.duration_delta}s
              </div>
              <div className="metric-sub">Average task duration change</div>
            </div>

            <div className="metric-card">
              <div className="metric-label">Error Rate Delta</div>
              <div
                className="metric-value"
                style={{
                  color: comparison.error_delta <= 0 ? 'var(--accent-green)' : 'var(--accent-red)',
                }}
              >
                {comparison.error_delta > 0 ? '+' : ''}
                {comparison.error_delta}
              </div>
              <div className="metric-sub">Average error count change</div>
            </div>

            <div className="metric-card">
              <div className="metric-label">Abandonment Delta</div>
              <div
                className="metric-value"
                style={{
                  color: comparison.abandonment_delta <= 0 ? 'var(--accent-green)' : 'var(--accent-red)',
                }}
              >
                {comparison.abandonment_delta > 0 ? '+' : ''}
                {Math.round(comparison.abandonment_delta * 100)}%
              </div>
              <div className="metric-sub">Change in user drop-off rate</div>
            </div>
          </div>

          {/* Segment Comparison Breakdown */}
          {comparison.segment_deltas?.technical_proficiency && (
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">Technical Proficiency Segment Impact</h3>
              </div>
              <div className="table-responsive">
                <table>
                  <thead>
                    <tr>
                      <th>Segment</th>
                      <th>Baseline Completion</th>
                      <th>Variant Completion</th>
                      <th>Delta</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(comparison.segment_deltas.technical_proficiency).map(([seg, data]: [string, any]) => {
                      const deltaVal = data.delta || 0;
                      return (
                        <tr key={seg}>
                          <td><strong>{seg}</strong></td>
                          <td>{Math.round((data.baseline_completion || 0) * 100)}%</td>
                          <td>{Math.round((data.variant_completion || 0) * 100)}%</td>
                          <td>
                            <strong style={{ color: deltaVal >= 0 ? 'var(--accent-green)' : 'var(--accent-red)' }}>
                              {deltaVal >= 0 ? '+' : ''}{Math.round(deltaVal * 100)}%
                            </strong>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Scientific Disclaimer */}
          <div style={{ marginTop: '1.5rem', padding: '1rem', background: '#0f172a', borderRadius: '4px', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            <strong>Methodology Note:</strong> Simulation comparisons isolate changes in simulated completion, action counts, and abandonments based on persistent agent heuristics. These projections indicate areas of probable usability difference and do not replace human testing.
          </div>
        </div>
      )}
    </div>
  );
};
