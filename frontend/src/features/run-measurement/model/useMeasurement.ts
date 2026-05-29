import { useQuery } from '@tanstack/react-query';
import { useEffect } from 'react';

import { streamUrl } from '@shared/api/client';
import { getMeasurement } from '@shared/api/measurements';

import { useMeasurementStore } from './measurementStore';

export function useMeasurement() {
  const jobId = useMeasurementStore((s) => s.jobId);
  const q = useQuery({
    queryKey: ['measurement', jobId],
    queryFn: () => getMeasurement(jobId!),
    enabled: !!jobId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === 'done' || status === 'failed') return false;
      return 1500;
    },
  });

  useEffect(() => {
    if (!jobId) return;
    const es = new EventSource(streamUrl(`/measurements/${jobId}/stream`));
    const refetch = () => void q.refetch();
    es.addEventListener('done', refetch);
    es.addEventListener('failed', refetch);
    es.onerror = () => es.close();
    return () => es.close();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobId]);

  return q;
}
