import { useState, useEffect, useCallback } from 'react';
import { apiClient } from '../api/client';
import { ExperimentDetailResponse } from '../types';

export function useExperiment(id?: string, pollIntervalMs = 4000) {
  const [data, setData] = useState<ExperimentDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDetail = useCallback(async () => {
    if (!id) return;
    try {
      const res = await apiClient.getExperiment(id);
      setData(res);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch experiment');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchDetail();
    if (!id) return;

    const interval = setInterval(() => {
      if (data?.experiment.status === 'RUNNING' || data?.experiment.status === 'CREATED') {
        fetchDetail();
      }
    }, pollIntervalMs);

    return () => clearInterval(interval);
  }, [id, fetchDetail, data?.experiment.status, pollIntervalMs]);

  const run = async (concurrency?: number) => {
    if (!id) return;
    await apiClient.runExperiment(id, concurrency);
    await fetchDetail();
  };

  const cancel = async () => {
    if (!id) return;
    await apiClient.cancelExperiment(id);
    await fetchDetail();
  };

  return {
    data,
    loading,
    error,
    refresh: fetchDetail,
    run,
    cancel,
  };
}
