import React, { useEffect, useState, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Clock,
  Activity,
  Shield,
  Play,
  Pause,
  SkipBack,
  SkipForward,
  RotateCcw,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Target,
  Compass,
  FileText
} from 'lucide-react';
import { apiClient } from '../api/client';
import { SyntheticUser, TrajectoryStep } from '../types';

export const UserDetailPage: React.FC = () => {
  const { id, userId } = useParams<{ id: string; userId: string }>();
  const [user, setUser] = useState<SyntheticUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1);
  const playTimerRef = useRef<any>(null);

  useEffect(() => {
    if (!id || !userId) return;
    apiClient.getUser(id, userId)
      .then((data) => {
        setUser(data);
        setCurrentStepIndex(0);
      })
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, [id, userId]);

  const trajectories: TrajectoryStep[] = user?.trajectories || [];
  const currentStep: TrajectoryStep | undefined = trajectories[currentStepIndex];

  // Playback timer handling
  useEffect(() => {
    if (isPlaying) {
      const delay = Math.max(250, 1500 / playbackSpeed);
      playTimerRef.current = setInterval(() => {
        setCurrentStepIndex((prev) => {
          if (prev >= trajectories.length - 1) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, delay);
    } else {
      if (playTimerRef.current) clearInterval(playTimerRef.current);
    }

    return () => {
      if (playTimerRef.current) clearInterval(playTimerRef.current);
    };
  }, [isPlaying, playbackSpeed, trajectories.length]);

  const handlePlayPause = () => {
    if (currentStepIndex >= trajectories.length - 1 && !isPlaying) {
      setCurrentStepIndex(0);
    }
    setIsPlaying(!isPlaying);
  };

  const handlePrev = () => {
    setIsPlaying(false);
    setCurrentStepIndex((prev) => Math.max(0, prev - 1));
  };

  const handleNext = () => {
    setIsPlaying(false);
    setCurrentStepIndex((prev) => Math.min(trajectories.length - 1, prev + 1));
  };

  const handleReset = () => {
    setIsPlaying(false);
    setCurrentStepIndex(0);
  };

  if (loading) {
    return <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>Loading trajectory replay...</div>;
  }

  if (!user) {
    return <div className="card">User trajectory not found.</div>;
  }

  return (
    <div>
      {/* Top Header */}
      <div className="page-header">
        <div>
          <Link to={`/experiments/${id}/users`} className="nav-link" style={{ marginBottom: '0.5rem', display: 'inline-flex' }}>
            <ArrowLeft size={14} /> Back to Population Explorer
          </Link>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.25rem' }}>
            <span className={`badge badge-${user.status.toLowerCase()}`}>{user.status}</span>
            <span className={`badge badge-${user.technical_proficiency.toLowerCase()}`}>{user.technical_proficiency}</span>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              Agent: {user.id}
            </span>
          </div>
          <h1 className="page-title">Interactive Trajectory Player</h1>
          <p className="page-subtitle">
            Goal: "{user.current_goal}" | Completed in {user.duration_seconds}s across {trajectories.length} recorded steps
          </p>
        </div>
      </div>

      {/* Trajectory Player Deck */}
      {trajectories.length > 0 && (
        <div className="card" style={{ marginBottom: '1.5rem', padding: '1.25rem' }}>
          {/* Player Controls Bar */}
          <div
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '1rem',
              paddingBottom: '1rem',
              borderBottom: '1px solid var(--border-color)',
              marginBottom: '1rem',
            }}
          >
            {/* Playback Buttons */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <button
                className="btn btn-secondary"
                style={{ padding: '0.4rem 0.6rem' }}
                onClick={handleReset}
                title="Rewind to start"
              >
                <RotateCcw size={15} />
              </button>
              <button
                className="btn btn-secondary"
                style={{ padding: '0.4rem 0.6rem' }}
                onClick={handlePrev}
                disabled={currentStepIndex === 0}
                title="Previous Step"
              >
                <SkipBack size={15} />
              </button>
              <button
                className={isPlaying ? 'btn btn-danger' : 'btn btn-primary'}
                style={{ padding: '0.4rem 1rem', display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}
                onClick={handlePlayPause}
              >
                {isPlaying ? <Pause size={15} /> : <Play size={15} />}
                <span>{isPlaying ? 'Pause' : 'Play Replay'}</span>
              </button>
              <button
                className="btn btn-secondary"
                style={{ padding: '0.4rem 0.6rem' }}
                onClick={handleNext}
                disabled={currentStepIndex === trajectories.length - 1}
                title="Next Step"
              >
                <SkipForward size={15} />
              </button>
            </div>

            {/* Speed Selector */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem' }}>
              <span style={{ color: 'var(--text-muted)' }}>Speed:</span>
              {[0.5, 1, 2, 4].map((spd) => (
                <button
                  key={spd}
                  onClick={() => setPlaybackSpeed(spd)}
                  style={{
                    background: playbackSpeed === spd ? 'var(--accent-blue)' : '#0f172a',
                    color: playbackSpeed === spd ? '#fff' : 'var(--text-secondary)',
                    border: '1px solid var(--border-color)',
                    borderRadius: '4px',
                    padding: '0.2rem 0.5rem',
                    fontSize: '0.75rem',
                    cursor: 'pointer',
                    fontWeight: playbackSpeed === spd ? 700 : 400,
                  }}
                >
                  {spd}x
                </button>
              ))}
            </div>

            {/* Step Counter Indicator */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span
                style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.9rem',
                  fontWeight: 700,
                  color: 'var(--accent-blue)',
                  background: '#0f172a',
                  padding: '0.25rem 0.6rem',
                  borderRadius: '4px',
                  border: '1px solid var(--border-color)',
                }}
              >
                Step {currentStepIndex + 1} / {trajectories.length}
              </span>
            </div>
          </div>

          {/* Scrubber Slider Bar */}
          <div style={{ marginBottom: '1.25rem' }}>
            <input
              type="range"
              min={0}
              max={trajectories.length - 1}
              value={currentStepIndex}
              onChange={(e) => {
                setIsPlaying(false);
                setCurrentStepIndex(Number(e.target.value));
              }}
              style={{
                width: '100%',
                accentColor: 'var(--accent-blue)',
                cursor: 'pointer',
              }}
            />

            {/* Micro-Timeline Step Markers */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: `repeat(${trajectories.length}, 1fr)`,
                gap: '2px',
                marginTop: '0.4rem',
                height: '6px',
              }}
            >
              {trajectories.map((step, idx) => {
                const isCurrent = idx === currentStepIndex;
                const isOk = step.action_result === 'SUCCESS';
                const isHighFrust = step.frustration_after > 0.4;
                let bg = isOk ? '#10b981' : '#ef4444';
                if (isOk && isHighFrust) bg = '#f59e0b';
                return (
                  <div
                    key={step.id || idx}
                    onClick={() => {
                      setIsPlaying(false);
                      setCurrentStepIndex(idx);
                    }}
                    title={`Step #${step.step_number}: ${step.action_type} on ${step.action_target} (${step.action_result})`}
                    style={{
                      background: bg,
                      height: isCurrent ? '10px' : '5px',
                      borderRadius: '2px',
                      cursor: 'pointer',
                      transform: isCurrent ? 'scaleY(1.6)' : 'none',
                      transition: 'all 0.15s ease',
                      boxShadow: isCurrent ? '0 0 6px rgba(56, 189, 248, 0.8)' : 'none',
                    }}
                  />
                );
              })}
            </div>
          </div>

          {/* Main Visual Observation & State Inspector Viewport */}
          {currentStep && (
            <div style={{ display: 'grid', gridTemplateColumns: '1.3fr 1fr', gap: '1.5rem', alignItems: 'start' }}>
              {/* Left: Visual Stage with Coordinate / Target Projection Overlay */}
              <div>
                <div
                  style={{
                    background: '#090d16',
                    border: '1px solid var(--border-color)',
                    borderRadius: '8px',
                    overflow: 'hidden',
                    position: 'relative',
                  }}
                >
                  {/* Browser Mockup Chrome Header */}
                  <div
                    style={{
                      background: '#0f172a',
                      padding: '0.5rem 0.8rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.6rem',
                      borderBottom: '1px solid var(--border-color)',
                      fontSize: '0.78rem',
                    }}
                  >
                    <div style={{ display: 'flex', gap: '4px' }}>
                      <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#ef4444' }} />
                      <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#f59e0b' }} />
                      <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981' }} />
                    </div>
                    <div
                      style={{
                        flex: 1,
                        background: '#1e293b',
                        padding: '0.2rem 0.6rem',
                        borderRadius: '4px',
                        fontFamily: 'var(--font-mono)',
                        color: 'var(--text-secondary)',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {currentStep.url}
                    </div>
                    <span style={{ color: 'var(--text-muted)' }}>
                      {currentStep.page_title}
                    </span>
                  </div>

                  {/* Screenshot Canvas with Target Overlay */}
                  <div
                    style={{
                      position: 'relative',
                      minHeight: '360px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      background: '#020617',
                    }}
                  >
                    {currentStep.screenshot_path ? (
                      <div style={{ position: 'relative', width: '100%', textAlign: 'center' }}>
                        <img
                          src={currentStep.screenshot_path}
                          alt={`Step ${currentStep.step_number} Capture`}
                          style={{
                            maxWidth: '100%',
                            maxHeight: '480px',
                            display: 'block',
                            margin: '0 auto',
                          }}
                        />

                        {/* Interactive Click Target Ring Overlay */}
                        <div
                          style={{
                            position: 'absolute',
                            top: '45%',
                            left: '50%',
                            transform: 'translate(-50%, -50%)',
                            pointerEvents: 'none',
                          }}
                        >
                          {/* Animated Ripple Pulse */}
                          <div
                            style={{
                              width: '44px',
                              height: '44px',
                              borderRadius: '50%',
                              border: `2px solid ${currentStep.action_result === 'SUCCESS' ? '#38bdf8' : '#ef4444'}`,
                              background: currentStep.action_result === 'SUCCESS' ? 'rgba(56, 189, 248, 0.25)' : 'rgba(239, 68, 68, 0.25)',
                              boxShadow: '0 0 16px rgba(56, 189, 248, 0.6)',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              animation: 'pulse 1.5s infinite',
                            }}
                          >
                            <Target size={20} color={currentStep.action_result === 'SUCCESS' ? '#38bdf8' : '#ef4444'} />
                          </div>

                          {/* Floating Target HUD Pill */}
                          <div
                            style={{
                              position: 'absolute',
                              top: '-32px',
                              left: '50%',
                              transform: 'translateX(-50%)',
                              background: '#0f172a',
                              border: '1px solid var(--border-color)',
                              padding: '0.2rem 0.5rem',
                              borderRadius: '4px',
                              fontSize: '0.75rem',
                              whiteSpace: 'nowrap',
                              color: '#fff',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '0.3rem',
                              boxShadow: '0 4px 12px rgba(0,0,0,0.5)',
                            }}
                          >
                            <strong>{currentStep.action_type}</strong>
                            <code style={{ color: 'var(--accent-blue)', fontSize: '0.7rem' }}>
                              {currentStep.action_target}
                            </code>
                          </div>
                        </div>
                      </div>
                    ) : (
                      /* Fallback UI Wireframe Viewport */
                      <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                        <Compass size={32} style={{ marginBottom: '0.5rem', color: 'var(--accent-blue)' }} />
                        <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
                          Synthetic Navigation Step #{currentStep.step_number}
                        </div>
                        <div style={{ fontSize: '0.85rem', marginBottom: '1rem' }}>
                          Target: <code>{currentStep.action_target}</code>
                        </div>
                        <div
                          style={{
                            background: '#0f172a',
                            padding: '1rem',
                            borderRadius: '6px',
                            border: '1px solid var(--border-color)',
                            textAlign: 'left',
                            fontSize: '0.8rem',
                          }}
                        >
                          <div style={{ color: 'var(--text-muted)', marginBottom: '0.3rem' }}>VISIBLE PAGE TEXT PREVIEW:</div>
                          <div style={{ color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                            {currentStep.visible_text_summary}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Right: Cognitive State & Decision Reasoning Inspector */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {/* Decision Reasoning Card */}
                <div
                  style={{
                    background: '#0f172a',
                    border: '1px solid var(--border-color)',
                    borderRadius: '8px',
                    padding: '1rem',
                    borderLeft: `4px solid ${currentStep.action_result === 'SUCCESS' ? 'var(--accent-green)' : 'var(--accent-red)'}`,
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.6rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                      <span className="badge" style={{ background: '#1e293b', color: 'var(--accent-blue)', fontWeight: 700 }}>
                        {currentStep.action_type}
                      </span>
                      <span style={{ fontSize: '0.85rem', color: 'var(--text-primary)', fontWeight: 600 }}>
                        Target:
                      </span>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.8rem' }}>
                      {currentStep.action_result === 'SUCCESS' ? (
                        <span style={{ color: 'var(--accent-green)', display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
                          <CheckCircle size={14} /> EXECUTED
                        </span>
                      ) : (
                        <span style={{ color: 'var(--accent-red)', display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
                          <XCircle size={14} /> FAILED
                        </span>
                      )}
                    </div>
                  </div>

                  <div style={{ marginBottom: '0.75rem' }}>
                    <code style={{ fontSize: '0.82rem', color: 'var(--accent-blue)', wordBreak: 'break-all' }}>
                      {currentStep.action_target}
                    </code>
                  </div>

                  {currentStep.action_parameters && Object.keys(currentStep.action_parameters).length > 0 && (
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '0.6rem' }}>
                      <strong>Parameters:</strong> <code>{JSON.stringify(currentStep.action_parameters)}</code>
                    </div>
                  )}

                  <div
                    style={{
                      background: '#1e293b',
                      padding: '0.75rem',
                      borderRadius: '6px',
                      fontSize: '0.82rem',
                      color: 'var(--text-secondary)',
                      lineHeight: 1.5,
                      marginBottom: '0.5rem',
                    }}
                  >
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '0.2rem', fontWeight: 700 }}>
                      AGENT DECISION REASONING:
                    </div>
                    "{currentStep.action_reason}"
                  </div>

                  {currentStep.error_message && (
                    <div
                      style={{
                        background: '#7f1d1d',
                        color: '#fca5a5',
                        padding: '0.5rem 0.75rem',
                        borderRadius: '4px',
                        fontSize: '0.78rem',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.4rem',
                        marginTop: '0.5rem',
                      }}
                    >
                      <AlertTriangle size={14} />
                      <span>{currentStep.error_message}</span>
                    </div>
                  )}

                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.6rem' }}>
                    <span>Confidence: {Math.round(currentStep.action_confidence * 100)}%</span>
                    <span>Action Latency: {currentStep.latency_ms}ms</span>
                  </div>
                </div>

                {/* Cognitive Affect Meters */}
                <div
                  style={{
                    background: '#0f172a',
                    border: '1px solid var(--border-color)',
                    borderRadius: '8px',
                    padding: '1rem',
                  }}
                >
                  <h4 style={{ fontSize: '0.85rem', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <Activity size={14} color="var(--accent-blue)" /> Dynamic Cognitive State at Step #{currentStep.step_number}
                  </h4>

                  {/* Frustration Gauge */}
                  <div style={{ marginBottom: '0.75rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '0.2rem' }}>
                      <span style={{ color: 'var(--text-muted)' }}>FRUSTRATION LEVEL</span>
                      <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: currentStep.frustration_after > 0.4 ? 'var(--accent-red)' : 'var(--accent-green)' }}>
                        {currentStep.frustration_after}
                      </span>
                    </div>
                    <div style={{ height: '6px', background: '#1e293b', borderRadius: '3px', overflow: 'hidden' }}>
                      <div
                        style={{
                          width: `${Math.round(currentStep.frustration_after * 100)}%`,
                          height: '100%',
                          background: currentStep.frustration_after > 0.4 ? 'var(--accent-red)' : 'var(--accent-green)',
                          transition: 'width 0.2s ease',
                        }}
                      />
                    </div>
                  </div>

                  {/* Confidence Gauge */}
                  <div style={{ marginBottom: '0.75rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '0.2rem' }}>
                      <span style={{ color: 'var(--text-muted)' }}>CONFIDENCE LEVEL</span>
                      <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--accent-blue)' }}>
                        {currentStep.confidence_after}
                      </span>
                    </div>
                    <div style={{ height: '6px', background: '#1e293b', borderRadius: '3px', overflow: 'hidden' }}>
                      <div
                        style={{
                          width: `${Math.round(currentStep.confidence_after * 100)}%`,
                          height: '100%',
                          background: 'var(--accent-blue)',
                          transition: 'width 0.2s ease',
                        }}
                      />
                    </div>
                  </div>

                  {/* Subgoal */}
                  <div style={{ fontSize: '0.78rem' }}>
                    <span style={{ color: 'var(--text-muted)' }}>CURRENT SUBGOAL: </span>
                    <strong style={{ color: 'var(--accent-blue)' }}>
                      {user.current_subgoal || 'Complete task'}
                    </strong>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Two Column Layout: Persona Profile & Step Table */}
      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '1.5rem', alignItems: 'start' }}>
        {/* Left Column: Fixed Persona Traits */}
        <div>
          <div className="card">
            <h3 className="card-title" style={{ marginBottom: '1rem' }}>
              <Shield size={16} /> Persona Traits & Profile
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.85rem' }}>
              <div>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>TECHNICAL PROFICIENCY</div>
                <strong>{user.technical_proficiency}</strong>
              </div>
              <div>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>PATIENCE LEVEL</div>
                <strong>{user.patience}</strong> (0.0=impatient, 1.0=patient)
              </div>
              <div>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>RISK TOLERANCE</div>
                <strong>{user.risk_tolerance}</strong>
              </div>
              <div>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>READING BEHAVIOR</div>
                <strong>{user.reading_behavior}</strong>
              </div>
              <div>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>DEVICE PROFILE</div>
                <div>{(user.device_profile || {}).device_type} ({(user.device_profile || {}).viewport_width}x{(user.device_profile || {}).viewport_height})</div>
              </div>
              <div>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>NETWORK PROFILE</div>
                <div>{(user.network_profile || {}).network_type} ({(user.network_profile || {}).latency_ms}ms simulated latency)</div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Full Step Directory Table */}
        <div>
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">
                <FileText size={18} /> Step Directory ({trajectories.length} Steps)
              </h2>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Click any step to scrub playback directly
              </span>
            </div>

            <div className="table-responsive">
              <table>
                <thead>
                  <tr>
                    <th>Step #</th>
                    <th>Action</th>
                    <th>Target Selector</th>
                    <th>Result</th>
                    <th>Latency</th>
                    <th>Frustration</th>
                  </tr>
                </thead>
                <tbody>
                  {trajectories.map((step, idx) => {
                    const isSelected = idx === currentStepIndex;
                    const isOk = step.action_result === 'SUCCESS';
                    return (
                      <tr
                        key={step.id || idx}
                        onClick={() => {
                          setIsPlaying(false);
                          setCurrentStepIndex(idx);
                        }}
                        style={{
                          cursor: 'pointer',
                          background: isSelected ? 'rgba(56, 189, 248, 0.12)' : undefined,
                          borderLeft: isSelected ? '3px solid var(--accent-blue)' : undefined,
                        }}
                      >
                        <td style={{ fontFamily: 'var(--font-mono)', fontWeight: isSelected ? 700 : 400 }}>
                          #{step.step_number}
                        </td>
                        <td>
                          <span className="badge" style={{ background: '#1e293b', color: 'var(--accent-blue)', fontSize: '0.75rem' }}>
                            {step.action_type}
                          </span>
                        </td>
                        <td>
                          <code style={{ fontSize: '0.78rem', color: 'var(--text-primary)' }}>
                            {step.action_target}
                          </code>
                        </td>
                        <td>
                          {isOk ? (
                            <span style={{ color: 'var(--accent-green)', fontSize: '0.78rem', display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
                              <CheckCircle size={12} /> OK
                            </span>
                          ) : (
                            <span style={{ color: 'var(--accent-red)', fontSize: '0.78rem', display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
                              <XCircle size={12} /> {step.error_message || 'ERR'}
                            </span>
                          )}
                        </td>
                        <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
                          {step.latency_ms}ms
                        </td>
                        <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: step.frustration_after > 0.4 ? 'var(--accent-red)' : 'var(--text-secondary)' }}>
                          {step.frustration_after}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
