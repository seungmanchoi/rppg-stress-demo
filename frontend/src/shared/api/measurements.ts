import type { AlgorithmMeta, MeasurementResponse } from '@entities/measurement';
import { api } from './client';

export interface UploadResponse {
  jobId: string;
  status: string;
}

export async function uploadVideo(file: File, algorithms?: string[]): Promise<UploadResponse> {
  const fd = new FormData();
  fd.append('video', file);
  const qs = algorithms?.length ? `?algorithms=${encodeURIComponent(algorithms.join(','))}` : '';
  return api<UploadResponse>(`/measurements${qs}`, { method: 'POST', body: fd });
}

export const getMeasurement = (jobId: string) =>
  api<MeasurementResponse>(`/measurements/${jobId}`);

export const listAlgorithms = () => api<AlgorithmMeta[]>('/algorithms');

export const health = () =>
  api<{ status: string; mpsAvailable: boolean; weightsLoaded: string[]; totalAlgorithms: number }>(
    '/health',
  );
