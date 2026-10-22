import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldAlert, Users, Sliders, Play } from 'lucide-react';
import { apiClient } from '../api/client';

export const NewExperimentPage: React.FC = () => {
  const navigate = useNavigate();

  const [name, setName] = useState('Checkout Usability Benchmark');
  const [targetUrl, setTargetUrl] = useState('http://localhost:5050/');
  const [description, setDescription] = useState('Simulated population evaluating checkout friction and conversion roadblocks.');
  const [populationSize, setPopulationSize] = useState(50);
  const [goal, setGoal] = useState('Purchase a laptop');
  const [successConditionValue, setSuccessConditionValue] = useState('order-placed');
  const [concurrency, setConcurrency] = useState(5);
  const [randomSeed, setRandomSeed] = useState(42);
  const [isAuthorized, setIsAuthorized] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Distribution settings
  const [beginnerPct, setBeginnerPct] = useState(40);
  const [intermediatePct, setIntermediatePct] = useState(45);
  const [expertPct, setExpertPct] = useState(15);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isAuthorized) {
      alert('You must confirm authorization before initiating testing.');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const totalDist = beginnerPct + intermediatePct + expertPct;
      const payload = {
        name,
        target_url: targetUrl,
        description,
        population_size: populationSize,
        task_definition: {
          goal,
          success_conditions: [
            { type: 'url_contains', value: successConditionValue }
          ],
          optional_conditions: [],
          failure_conditions: []
        },
        population_distributions: {
          technical_proficiency: {
            BEGINNER: beginnerPct / totalDist,
            INTERMEDIATE: intermediatePct / totalDist,
            EXPERT: expertPct / totalDist
          }
        },
        concurrency,
        random_seed: randomSeed,
        max_steps_per_user: 25,
        max_duration_seconds: 120,
        is_authorized: isAuthorized,
        model_configuration: { provider: 'mock' }
      };

      const created = await apiClient.createExperiment(payload);
      navigate(`/experiments/${created.id}`);
    } catch (err: any) {
      setError(err.message || 'Failed to create experiment');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      <div className="page-header">
        <div>
          <h1 className="page-title">Configure Simulation Experiment</h1>
          <p className="page-subtitle">
            Deploy persistent synthetic human populations against an authorized web application.
          </p>
        </div>
      </div>

      {error && (
        <div className="card" style={{ borderColor: 'var(--accent-red)', background: '#2d1515', color: '#f87171' }}>
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">General Specification</h2>
          </div>

          <div className="form-group">
            <label className="form-label">Experiment Name</label>
            <input
              type="text"
              className="form-input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Target Application URL</label>
            <input
              type="url"
              className="form-input"
              value={targetUrl}
              onChange={(e) => setTargetUrl(e.target.value)}
              required
            />
            <div className="form-help">
              Simulations run strictly within this origin. Navigation outside is blocked by security boundaries.
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Description / Hypothesis</label>
            <textarea
              className="form-textarea"
              rows={2}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Structured Task Definition</h2>
          </div>

          <div className="form-group">
            <label className="form-label">Primary User Goal</label>
            <input
              type="text"
              className="form-input"
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              required
            />
            <div className="form-help">Ex: "Purchase a laptop", "Complete inquiry checkout", "Sign up for beta"</div>
          </div>

          <div className="form-group">
            <label className="form-label">Success Condition (URL Contains)</label>
            <input
              type="text"
              className="form-input"
              value={successConditionValue}
              onChange={(e) => setSuccessConditionValue(e.target.value)}
              required
            />
            <div className="form-help">The destination page URL pattern proving task fulfillment.</div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h2 className="card-title">
              <Users size={18} /> Synthetic Population Distributions
            </h2>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem', marginBottom: '1.25rem' }}>
            <div className="form-group">
              <label className="form-label">Population Size</label>
              <input
                type="number"
                className="form-input"
                min={1}
                max={1000}
                value={populationSize}
                onChange={(e) => setPopulationSize(parseInt(e.target.value) || 10)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Concurrency (Workers)</label>
              <input
                type="number"
                className="form-input"
                min={1}
                max={20}
                value={concurrency}
                onChange={(e) => setConcurrency(parseInt(e.target.value) || 2)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Random Seed</label>
              <input
                type="number"
                className="form-input"
                value={randomSeed}
                onChange={(e) => setRandomSeed(parseInt(e.target.value) || 0)}
              />
              <div className="form-help">Guarantees deterministic trait generation.</div>
            </div>
          </div>

          <div className="card-header" style={{ marginBottom: '0.5rem' }}>
            <h3 style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Technical Proficiency Distribution</h3>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem' }}>
            <div>
              <label className="form-label">Beginner ({beginnerPct}%)</label>
              <input
                type="range"
                min={0}
                max={100}
                value={beginnerPct}
                onChange={(e) => setBeginnerPct(parseInt(e.target.value))}
                style={{ width: '100%' }}
              />
            </div>
            <div>
              <label className="form-label">Intermediate ({intermediatePct}%)</label>
              <input
                type="range"
                min={0}
                max={100}
                value={intermediatePct}
                onChange={(e) => setIntermediatePct(parseInt(e.target.value))}
                style={{ width: '100%' }}
              />
            </div>
            <div>
              <label className="form-label">Expert ({expertPct}%)</label>
              <input
                type="range"
                min={0}
                max={100}
                value={expertPct}
                onChange={(e) => setExpertPct(parseInt(e.target.value))}
                style={{ width: '100%' }}
              />
            </div>
          </div>
        </div>

        <div className="card" style={{ borderColor: 'var(--accent-amber)', background: 'rgba(245, 158, 11, 0.05)' }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
            <ShieldAlert size={22} color="#f59e0b" style={{ flexShrink: 0, marginTop: '2px' }} />
            <div>
              <div style={{ fontWeight: 600, color: 'var(--accent-amber)', marginBottom: '0.25rem' }}>
                Safety & Authorization Confirmation
              </div>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
                Synthetic Humans operates exclusively for usability testing and workflow validation on authorized targets.
                Payment submission, arbitrary shell code, and external domain excursions are strictly blocked.
              </p>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', fontSize: '0.875rem' }}>
                <input
                  type="checkbox"
                  checked={isAuthorized}
                  onChange={(e) => setIsAuthorized(e.target.checked)}
                  required
                />
                <span style={{ fontWeight: 500 }}>
                  I confirm I am explicitly authorized to run behavioral user simulations against this target application.
                </span>
              </label>
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => navigate('/experiments')}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading || !isAuthorized}
          >
            <Play size={14} /> Create & Generate Population
          </button>
        </div>
      </form>
    </div>
  );
};
