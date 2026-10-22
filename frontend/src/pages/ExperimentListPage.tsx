import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Play, Eye, GitCompare, PlusCircle, RefreshCw, AlertCircle } from 'lucide-react';
import { apiClient } from '../api/client';
import { Experiment } from '../types';

export const ExperimentListPage: React.FC = () => {
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchExperiments = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiClient.listExperiments();
      setExperiments(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load experiments');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExperiments();
    const interval = setInterval(fetchExperiments, 6000);
    return () => clearInterval(interval);
  }, []);

  const handleRun = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    try {
      await apiClient.runExperiment(id);
      fetchExperiments();
    } catch (err: any) {
      alert(`Error starting experiment: ${err.message}`);
    }
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Simulation Experiments</h1>
          <p className="page-subtitle">
            Autonomous user population simulations, behavioral friction detection, and HCI trajectories
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button className="btn btn-secondary" onClick={fetchExperiments}>
            <RefreshCw size={14} /> Refresh
          </button>
          <Link to="/experiments/new" className="btn btn-primary">
            <PlusCircle size={14} /> New Experiment
          </Link>
        </div>
      </div>

      {error && (
        <div className="card" style={{ borderColor: 'var(--accent-red)', background: '#2d1515' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#f87171' }}>
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
        </div>
      )}

      <div className="card">
        <div className="table-responsive">
          <table>
            <thead>
              <tr>
                <th>Experiment</th>
                <th>Target URL</th>
                <th>Population</th>
                <th>Status</th>
                <th>Completion Rate</th>
                <th>Created</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {experiments.length === 0 && !loading && (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                    No simulation experiments found. Click "New Experiment" to create your first population test.
                  </td>
                </tr>
              )}
              {experiments.map((exp) => {
                const total = exp.population_size || 1;
                const completed = exp.completed_users_count || 0;
                const compPct = Math.round((completed / total) * 100);

                return (
                  <tr key={exp.id}>
                    <td>
                      <div style={{ fontWeight: 600 }}>
                        <Link to={`/experiments/${exp.id}`} style={{ color: 'var(--text-primary)' }}>
                          {exp.name}
                        </Link>
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                        {exp.id.substring(0, 13)}...
                      </div>
                    </td>
                    <td>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                        {exp.target_url}
                      </span>
                    </td>
                    <td>
                      <span style={{ fontWeight: 600 }}>{exp.population_size}</span> agents
                    </td>
                    <td>
                      <span className={`badge badge-${exp.status.toLowerCase()}`}>
                        {exp.status}
                      </span>
                    </td>
                    <td>
                      {exp.status === 'CREATED' ? (
                        <span style={{ color: 'var(--text-muted)' }}>Pending run</span>
                      ) : (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <div style={{ width: '60px', height: '6px', background: '#0f172a', borderRadius: '3px', overflow: 'hidden' }}>
                            <div style={{ width: `${compPct}%`, height: '100%', background: 'var(--accent-green)' }} />
                          </div>
                          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>{compPct}%</span>
                        </div>
                      )}
                    </td>
                    <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      {new Date(exp.created_at).toLocaleDateString()}
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <div style={{ display: 'inline-flex', gap: '0.4rem' }}>
                        {exp.status === 'CREATED' && (
                          <button
                            className="btn btn-primary"
                            style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }}
                            onClick={(e) => handleRun(e, exp.id)}
                            title="Run Experiment"
                          >
                            <Play size={12} /> Run
                          </button>
                        )}
                        <Link
                          to={`/experiments/${exp.id}`}
                          className="btn btn-secondary"
                          style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }}
                          title="View Dashboard"
                        >
                          <Eye size={12} /> View
                        </Link>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
