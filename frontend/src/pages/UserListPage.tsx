import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Filter, PlayCircle, Eye } from 'lucide-react';
import { apiClient } from '../api/client';
import { SyntheticUser } from '../types';

export const UserListPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [users, setUsers] = useState<SyntheticUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [proficiencyFilter, setProficiencyFilter] = useState('');

  const fetchUsers = async () => {
    if (!id) return;
    try {
      setLoading(true);
      const data = await apiClient.listUsers(id, {
        status: statusFilter || undefined,
        technical_proficiency: proficiencyFilter || undefined,
      });
      setUsers(data);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, [id, statusFilter, proficiencyFilter]);

  return (
    <div>
      <div className="page-header">
        <div>
          <Link to={`/experiments/${id}`} className="nav-link" style={{ marginBottom: '0.5rem', display: 'inline-flex' }}>
            <ArrowLeft size={14} /> Back to Dashboard
          </Link>
          <h1 className="page-title">Synthetic Population Explorer</h1>
          <p className="page-subtitle">
            Inspect individual cognitive trajectories, patience parameters, and task outcomes.
          </p>
        </div>
      </div>

      {/* Filter controls */}
      <div className="card" style={{ padding: '1rem', display: 'flex', gap: '1.5rem', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.875rem' }}>
          <Filter size={16} color="var(--text-muted)" />
          <span>Filters:</span>
        </div>

        <div>
          <select
            className="form-select"
            style={{ width: 'auto' }}
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">All Statuses</option>
            <option value="COMPLETED">Completed</option>
            <option value="ABANDONED">Abandoned</option>
            <option value="FAILED">Failed</option>
            <option value="PENDING">Pending</option>
          </select>
        </div>

        <div>
          <select
            className="form-select"
            style={{ width: 'auto' }}
            value={proficiencyFilter}
            onChange={(e) => setProficiencyFilter(e.target.value)}
          >
            <option value="">All Proficiencies</option>
            <option value="BEGINNER">Beginner</option>
            <option value="INTERMEDIATE">Intermediate</option>
            <option value="EXPERT">Expert</option>
          </select>
        </div>

        <div style={{ marginLeft: 'auto', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
          Showing {users.length} synthetic users
        </div>
      </div>

      <div className="card">
        <div className="table-responsive">
          <table>
            <thead>
              <tr>
                <th>Agent ID</th>
                <th>Proficiency</th>
                <th>Device</th>
                <th>Patience</th>
                <th>Frustration</th>
                <th>Status</th>
                <th>Steps</th>
                <th>Duration</th>
                <th style={{ textAlign: 'right' }}>Trajectory</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => {
                const frustPct = Math.round(u.frustration_level * 100);
                return (
                  <tr key={u.id}>
                    <td>
                      <Link
                        to={`/experiments/${id}/users/${u.id}`}
                        style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--accent-blue)' }}
                      >
                        {u.id.substring(0, 13)}...
                      </Link>
                    </td>
                    <td>
                      <span className={`badge badge-${u.technical_proficiency.toLowerCase()}`}>
                        {u.technical_proficiency}
                      </span>
                    </td>
                    <td style={{ fontSize: '0.85rem' }}>
                      {(u.device_profile || {}).device_type || 'DESKTOP'}
                    </td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>
                      {u.patience}
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                        <div style={{ width: '40px', height: '6px', background: '#0f172a', borderRadius: '3px', overflow: 'hidden' }}>
                          <div
                            style={{
                              width: `${frustPct}%`,
                              height: '100%',
                              background: frustPct > 60 ? 'var(--accent-red)' : 'var(--accent-green)',
                            }}
                          />
                        </div>
                        <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)' }}>{frustPct}%</span>
                      </div>
                    </td>
                    <td>
                      <span className={`badge badge-${u.status.toLowerCase()}`}>
                        {u.status}
                      </span>
                    </td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>{u.steps_taken}</td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>{u.duration_seconds}s</td>
                    <td style={{ textAlign: 'right' }}>
                      <Link
                        to={`/experiments/${id}/users/${u.id}`}
                        className="btn btn-secondary"
                        style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }}
                      >
                        <Eye size={12} /> Inspect Replay
                      </Link>
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
