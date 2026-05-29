import { useMutation } from '@tanstack/react-query';

import { uploadVideo } from '@shared/api/measurements';
import { useMeasurementStore } from '@features/run-measurement/model/measurementStore';

export function useUpload() {
  const setJobId = useMeasurementStore((s) => s.setJobId);
  return useMutation({
    mutationFn: (file: File) => uploadVideo(file),
    onSuccess: (data) => setJobId(data.jobId),
  });
}
