import React, { useEffect, useState, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  Play,
  Square,
  Users,
  GitCompare,
  AlertTriangle,
  Download,
  FileText,
  Activity,
  Radio,
  Layers,
  Flame,
  CheckCircle,
  XCircle,
  HelpCircle
} from 'lucide-react';
import { apiClient } from '../api/client';
import { ExperimentDetailResponse, HeatmapItem } from '../types';

interface LiveStepEvent {
  type: string;
  user_id?: string;
  step_number?: number;
  action_type?: string;
  action_target?: string;
  action_reason?: string;
  action_result?: string;
  frustration?: number;
  timestamp?: string;
  url?: string;
  error_message?: string;
}

interface AgentTelemetry {
  id: string;
  proficiency?: string;
  status: string;
  step: number;
  frustration: number;
  lastAction: string;
  lastTarget: string;
}

export const ExperimentDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<ExperimentDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Live SSE Telemetry State
  const [liveEvents, setLiveEvents] = useState<LiveStepEvent[]>([]);
  const [activeRoster, setActiveRoster] = useState<Record<string, AgentTelemetry>>({});
  const [isLiveConnected, setIsLiveConnected] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);
  const terminalRef = useRef<HTMLDivElement | null>(null);

  const fetchDetail = async () => {
    if (!id) return;
    try {
      const res = await apiClient.getExperiment(id);
      setData(res);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch experiment details');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDetail();
    const interval = setInterval(fetchDetail, 5000);
    return () => clearInterval(interval);
  }, [id]);

  // Live SSE Connection
  useEffect(() => {
    if (!id || !data) return;
    const isRunning = data.experiment.status === 'RUNNING';

    if (isRunning && !eventSourceRef.current) {
      const sseUrl = apiClient.getStreamUrl(id);
      const es = new EventSource(sseUrl);
      eventSourceRef.current = es;

      es.onopen = () => {
        setIsLiveConnected(true);
      };

      const handleEvent = (e: MessageEvent) => {
        try {
          const payload = JSON.parse(e.data);
          const evtType = payload.type || e.type;

          if (evtType === 'step') {
            setLiveEvents((prev) => [...prev.slice(-49), payload]);
            setActiveRoster((prev) => ({
              ...prev,
              [payload.user_id]: {
                id: payload.user_id,
                status: 'RUNNING',
                step: payload.step_number || 1,
                frustration: payload.frustration || 0.0,
                lastAction: payload.action_type || 'WAIT',
                lastTarget: payload.action_target || '',
              },
            }));
          } else if (evtType === 'agent_start') {
            setActiveRoster((prev) => ({
              ...prev,
              [payload.user_id]: {
                id: payload.user_id,
                proficiency: payload.proficiency,
                status: 'RUNNING',
                step: 0,
                frustration: 0.0,
                lastAction: 'NAVIGATE',
                lastTarget: 'Target URL',
              },
            }));
          } else if (evtType === 'agent_finish') {
            setActiveRoster((prev) => ({
              ...prev,
              [payload.user_id]: {
                ...(prev[payload.user_id] || { id: payload.user_id, step: payload.steps_taken || 0, frustration: payload.frustration || 0.0, lastAction: 'FINISH', lastTarget: '' }),
                status: payload.status,
                step: payload.steps_taken || (prev[payload.user_id]?.step || 0),
                frustration: payload.frustration || 0.0,
              },
            }));
          } else if (evtType === 'experiment_finish') {
            fetchDetail();
          }
        } catch (err) {
          console.debug('Failed to parse SSE payload', err);
        }
      };

      es.onmessage = handleEvent;
      es.addEventListener('step', handleEvent as EventListener);
      es.addEventListener('agent_start', handleEvent as EventListener);
      es.addEventListener('agent_finish', handleEvent as EventListener);
      es.addEventListener('experiment_finish', handleEvent as EventListener);

      es.onerror = () => {
        setIsLiveConnected(false);
      };
    } else if (!isRunning && eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
      setIsLiveConnected(false);
    }

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
    };
  }, [id, data?.experiment?.status]);

  // Auto-scroll live terminal
  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [liveEvents]);

  const handleRun = async () => {
    if (!id) return;
    try {
      await apiClient.runExperiment(id);
      fetchDetail();
    } catch (err: any) {
      alert(`Error starting experiment: ${err.message}`);
    }
  };

  const handleCancel = async () => {
    if (!id) return;
    try {
      await apiClient.cancelExperiment(id);
      fetchDetail();
    } catch (err: any) {
      alert(`Error cancelling experiment: ${err.message}`);
    }
  };

  if (loading && !data) {
    return <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>Loading simulation metrics...</div>;
  }

  if (error || !data) {
    return (
      <div className="card" style={{ borderColor: 'var(--accent-red)' }}>
        <div style={{ color: 'var(--accent-red)' }}>{error || 'Experiment not found'}</div>
        <Link to="/experiments" className="btn btn-secondary" style={{ marginTop: '1rem' }}>Back to Experiments</Link>
      </div>
    );
  }

  const { experiment, metrics, findings } = data;
  const isRunning = experiment.status === 'RUNNING';
  const isCreated = experiment.status === 'CREATED';

  const completedCount = experiment.completed_users_count || 0;
  const totalCount = experiment.population_size || 1;
  const progressPercent = Math.min(100, Math.round((completedCount / totalCount) * 100));

  return (
    <div>
      {/* Page Header */}
      <div className="page-header">
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.4rem' }}>
            <span className={`badge badge-${experiment.status.toLowerCase()}`}>
              {experiment.status}
            </span>
            {isRunning && isLiveConnected && (
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.75rem', color: 'var(--accent-green)', fontWeight: 600 }}>
                <Radio size={14} className="animate-pulse" /> LIVE TELEMETRY STREAM
              </span>
            )}
            <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              ID: {experiment.id}
            </span>
          </div>
          <h1 className="page-title">{experiment.name}</h1>
          <p className="page-subtitle">
            Target: <code style={{ color: 'var(--text-primary)' }}>{experiment.target_url}</code> | Goal: "{experiment.task_definition.goal}"
          </p>
        </div>

        {/* Action Controls & Data Exports */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', alignItems: 'center' }}>
          {isCreated && (
            <button className="btn btn-primary" onClick={handleRun}>
              <Play size={14} /> Start Simulation
            </button>
          )}
          {isRunning && (
            <button className="btn btn-danger" onClick={handleCancel}>
              <Square size={14} /> Cancel
            </button>
          )}

          <Link to={`/experiments/${experiment.id}/users`} className="btn btn-secondary">
            <Users size={14} /> Population ({experiment.population_size})
          </Link>
          <Link to={`/experiments/${experiment.id}/compare`} className="btn btn-secondary">
            <GitCompare size={14} /> Compare
          </Link>

          {/* Export Buttons */}
          <a
            href={apiClient.getExportJsonUrl(experiment.id)}
            download={`experiment-${experiment.id}-export.json`}
            className="btn btn-secondary"
            title="Download complete structured JSON trajectory dump"
          >
            <Download size={13} /> JSON
          </a>
          <a
            href={apiClient.getExportCsvUrl(experiment.id)}
            download={`experiment-${experiment.id}-events.csv`}
            className="btn btn-secondary"
            title="Download granular step-by-step event log CSV"
          >
            <Download size={13} /> CSV
          </a>
          <a
            href={apiClient.getExportReportUrl(experiment.id)}
            download={`usability-report-${experiment.id}.md`}
            className="btn btn-secondary"
            title="Download executive usability audit report in Markdown"
          >
            <FileText size={13} /> Report
          </a>
        </div>
      </div>

      {/* Live Simulation Operations Deck HUD (Visible when RUNNING) */}
      {isRunning && (
        <div className="card" style={{ borderColor: 'var(--accent-blue)', background: '#090d16', marginBottom: '1.5rem' }}>
          <div className="card-header" style={{ borderBottom: '1px solid rgba(56, 189, 248, 0.2)' }}>
            <h2 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--accent-blue)' }}>
              <Activity size={18} /> Live Simulation Operations Deck
            </h2>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              Progress: <strong>{completedCount} / {totalCount}</strong> agents completed ({progressPercent}%)
            </div>
          </div>

          {/* Progress Bar */}
          <div style={{ height: '6px', background: '#1e293b', borderRadius: '3px', overflow: 'hidden', marginBottom: '1rem' }}>
            <div
              style={{
                width: `${progressPercent}%`,
                height: '100%',
                background: 'linear-gradient(90deg, #38bdf8, #818cf8)',
                transition: 'width 0.3s ease',
              }}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '1rem', alignItems: 'start' }}>
            {/* Live Scrolling Telemetry Log Feed */}
            <div>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '0.4rem' }}>
                LIVE BEHAVIORAL EVENT FEED:
              </div>
              <div
                ref={terminalRef}
                style={{
                  background: '#020617',
                  border: '1px solid var(--border-color)',
                  borderRadius: '6px',
                  padding: '0.75rem',
                  height: '200px',
                  overflowY: 'auto',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.78rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.35rem',
                }}
              >
                {liveEvents.length === 0 ? (
                  <div style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>
                    Awaiting browser interaction telemetry...
                  </div>
                ) : (
                  liveEvents.map((evt, idx) => (
                    <div key={idx} style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-start' }}>
                      <span style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>
                        {evt.timestamp ? new Date(evt.timestamp).toLocaleTimeString() : '--:--:--'}
                      </span>
                      <span style={{ color: 'var(--accent-blue)', fontWeight: 700 }}>
                        [Agent {evt.user_id?.slice(-4)}]
                      </span>
                      <span className="badge" style={{ background: '#1e293b', padding: '0.1rem 0.3rem', fontSize: '0.7rem' }}>
                        {evt.action_type}
                      </span>
                      <span style={{ color: 'var(--text-primary)', wordBreak: 'break-all' }}>
                        {evt.action_target}
                      </span>
                      {evt.frustration !== undefined && (
                        <span style={{ color: evt.frustration > 0.4 ? 'var(--accent-red)' : 'var(--text-muted)', fontSize: '0.7rem' }}>
                          (Frust: {evt.frustration})
                        </span>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Active Agent Worker Roster */}
            <div>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '0.4rem' }}>
                ACTIVE AGENT WORKER POOL ({Object.keys(activeRoster).length}):
              </div>
              <div
                style={{
                  maxHeight: '200px',
                  overflowY: 'auto',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.4rem',
                }}
              >
                {Object.values(activeRoster).map((ag) => (
                  <div
                    key={ag.id}
                    style={{
                      background: '#0f172a',
                      border: '1px solid var(--border-color)',
                      borderRadius: '4px',
                      padding: '0.5rem 0.6rem',
                      fontSize: '0.75rem',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                        Agent {ag.id.slice(-6)}
                      </div>
                      <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>
                        Step #{ag.step} | {ag.lastAction}
                      </div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <span
                        className="badge"
                        style={{
                          background: ag.status === 'COMPLETED' ? '#064e3b' : ag.status === 'ABANDONED' ? '#7f1d1d' : '#1e293b',
                          color: ag.status === 'COMPLETED' ? '#34d399' : ag.status === 'ABANDONED' ? '#f87171' : 'var(--accent-blue)',
                          fontSize: '0.68rem',
                        }}
                      >
                        {ag.status}
                      </span>
                      <div style={{ fontSize: '0.68rem', color: ag.frustration > 0.4 ? 'var(--accent-red)' : 'var(--text-muted)', marginTop: '2px' }}>
                        Frust: {ag.frustration}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Metrics KPI Scorecard */}
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-label">Task Completion Rate</div>
          <div className="metric-value" style={{ color: 'var(--accent-green)' }}>
            {metrics ? `${Math.round(metrics.task_completion_rate * 100)}%` : '--'}
          </div>
          <div className="metric-sub">
            {experiment.completed_users_count || 0} of {experiment.population_size} agents
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Abandonment Rate</div>
          <div className="metric-value" style={{ color: 'var(--accent-amber)' }}>
            {metrics ? `${Math.round(metrics.task_abandonment_rate * 100)}%` : '--'}
          </div>
          <div className="metric-sub">
            Exceeded frustration or stuck
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Avg Task Duration</div>
          <div className="metric-value">
            {metrics ? `${metrics.average_task_duration}s` : '--'}
          </div>
          <div className="metric-sub">
            Median: {metrics?.median_task_duration || 0}s | p95: {metrics?.p95_task_duration || 0}s
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Avg Actions / User</div>
          <div className="metric-value">
            {metrics ? metrics.average_actions : '--'}
          </div>
          <div className="metric-sub">
            Avg Errors: {metrics?.average_errors || 0}
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Confusion / Loop Rate</div>
          <div className="metric-value" style={{ color: 'var(--accent-blue)' }}>
            {metrics ? `${Math.round(metrics.confusion_rate * 100)}%` : '--'}
          </div>
          <div className="metric-sub">
            Retry Rate: {metrics ? `${Math.round(metrics.retry_rate * 100)}%` : '--'}
          </div>
        </div>
      </div>

      {/* Usability Friction Findings */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">
            <AlertTriangle size={18} color="#f59e0b" />
            Detected Usability Friction Points ({findings.length})
          </h2>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Empirical evidence synthesized from agent behavioral trajectories
          </span>
        </div>

        {findings.length === 0 ? (
          <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem', padding: '1rem 0' }}>
            {isRunning
              ? 'Simulation in progress. Friction findings will be synthesized upon completion.'
              : 'No significant friction anomalies detected.'}
          </div>
        ) : (
          <div>
            {findings.map((f) => (
              <div key={f.id} className={`finding-card severity-${f.severity.toLowerCase()}`}>
                <div className="finding-title">
                  <span>{f.title}</span>
                  <span className={`badge badge-${f.severity.toLowerCase()}`}>
                    {f.severity} IMPACT
                  </span>
                </div>
                <div className="finding-desc">{f.description}</div>
                <div className="finding-rec">
                  <strong>Recommendation:</strong> {f.recommendation}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Workflow Funnel */}
      {metrics && metrics.funnel_steps && metrics.funnel_steps.length > 0 && (
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">
              <Layers size={18} /> Workflow Conversion Funnel
            </h2>
          </div>
          <div className="funnel-bar-container">
            {metrics.funnel_steps.map((step) => {
              const widthPct = Math.round(step.conversion_rate * 100);
              return (
                <div key={step.stage} className="funnel-step">
                  <div className="funnel-label">{step.stage}</div>
                  <div className="funnel-bar-bg">
                    <div className="funnel-bar-fill" style={{ width: `${Math.max(4, widthPct)}%` }} />
                  </div>
                  <div className="funnel-stat">
                    <strong>{step.users_reached}</strong> users ({widthPct}%)
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Persona Segment Analysis */}
      {metrics && metrics.segment_metrics && (
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Technical Proficiency Breakdown</h2>
          </div>
          <div className="table-responsive">
            <table>
              <thead>
                <tr>
                  <th>Proficiency Level</th>
                  <th>Agents Tested</th>
                  <th>Completed</th>
                  <th>Completion Rate</th>
                  <th>Avg Duration</th>
                  <th>Avg Frustration</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(metrics.segment_metrics.technical_proficiency || {}).map(([prof, seg]: [string, any]) => (
                  <tr key={prof}>
                    <td>
                      <span className={`badge badge-${prof.toLowerCase()}`}>{prof}</span>
                    </td>
                    <td>{seg.total}</td>
                    <td>{seg.completed}</td>
                    <td>
                      <strong style={{ color: seg.completion_rate > 0.6 ? 'var(--accent-green)' : 'var(--accent-amber)' }}>
                        {Math.round(seg.completion_rate * 100)}%
                      </strong>
                    </td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>{seg.avg_duration}s</td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>{seg.avg_frustration}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* UI Element Interaction & Friction Heatmap */}
      {metrics && metrics.heatmap_data && metrics.heatmap_data.length > 0 && (
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">
              <Flame size={18} color="#ef4444" /> UI Element Interaction & Friction Heatmap
            </h2>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Top interacted DOM affordances ranked by friction severity
            </span>
          </div>

          <div className="table-responsive">
            <table>
              <thead>
                <tr>
                  <th>Target Selector</th>
                  <th>Screen URL</th>
                  <th>Interactions</th>
                  <th>Misclicks / Errors</th>
                  <th>Friction Score</th>
                </tr>
              </thead>
              <tbody>
                {metrics.heatmap_data.slice(0, 10).map((item, idx) => (
                  <tr key={idx}>
                    <td>
                      <code style={{ fontSize: '0.8rem', color: 'var(--accent-blue)' }}>{item.selector}</code>
                    </td>
                    <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{item.url}</td>
                    <td>{item.total_interactions}</td>
                    <td style={{ color: item.errors > 0 ? 'var(--accent-red)' : 'var(--text-muted)', fontWeight: item.errors > 0 ? 700 : 400 }}>
                      {item.errors}
                    </td>
                    <td>
                      <span
                        className="badge"
                        style={{
                          background: item.friction_score > 1.0 ? '#7f1d1d' : '#1e293b',
                          color: item.friction_score > 1.0 ? '#f87171' : 'var(--text-primary)',
                        }}
                      >
                        {item.friction_score}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
