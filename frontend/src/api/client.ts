import {
  Experiment,
  SyntheticUser,
  ExperimentMetrics,
  FrictionFinding,
  ExperimentComparison,
  ExperimentDetailResponse
} from '../types';

const API_BASE = '/api';

export const apiClient = {
  async listExperiments(): Promise<Experiment[]> {
    const res = await fetch(`${API_BASE}/experiments`);
    if (!res.ok) throw new Error('Failed to fetch experiments');
    return res.json();
  },

  async getExperiment(id: string): Promise<ExperimentDetailResponse> {
    const res = await fetch(`${API_BASE}/experiments/${id}`);
    if (!res.ok) throw new Error(`Failed to fetch experiment ${id}`);
    return res.json();
  },

  async createExperiment(payload: Partial<Experiment>): Promise<Experiment> {
    const res = await fetch(`${API_BASE}/experiments`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to create experiment');
    }
    return res.json();
  },

  async runExperiment(id: string, concurrency?: number): Promise<{ status: string; experiment_id: string }> {
    const res = await fetch(`${API_BASE}/experiments/${id}/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ concurrency }),
    });
    if (!res.ok) throw new Error('Failed to run experiment');
    return res.json();
  },

  async cancelExperiment(id: string): Promise<{ status: string }> {
    const res = await fetch(`${API_BASE}/experiments/${id}/cancel`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to cancel experiment');
    return res.json();
  },

  async listUsers(
    experimentId: string,
    params?: { status?: string; technical_proficiency?: string }
  ): Promise<SyntheticUser[]> {
    const query = new URLSearchParams();
    if (params?.status) query.set('status', params.status);
    if (params?.technical_proficiency) query.set('technical_proficiency', params.technical_proficiency);

    const res = await fetch(`${API_BASE}/experiments/${experimentId}/users?${query.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch users');
    return res.json();
  },

  async getUser(experimentId: string, userId: string): Promise<SyntheticUser> {
    const res = await fetch(`${API_BASE}/experiments/${experimentId}/users/${userId}`);
    if (!res.ok) throw new Error('Failed to fetch user detail');
    return res.json();
  },

  async compareExperiments(baselineId: string, variantId: string): Promise<ExperimentComparison> {
    const res = await fetch(`${API_BASE}/experiments/${baselineId}/compare/${variantId}`);
    if (!res.ok) throw new Error('Failed to compare experiments');
    return res.json();
  },

  getStreamUrl(id: string): string {
    return `${API_BASE}/experiments/${id}/stream`;
  },

  getExportJsonUrl(id: string): string {
    return `${API_BASE}/experiments/${id}/export/json`;
  },

  getExportCsvUrl(id: string): string {
    return `${API_BASE}/experiments/${id}/export/csv`;
  },

  getExportReportUrl(id: string): string {
    return `${API_BASE}/experiments/${id}/export/report`;
  },
};
