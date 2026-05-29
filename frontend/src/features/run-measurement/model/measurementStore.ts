import { create } from 'zustand';

interface State {
  jobId: string | null;
  setJobId: (id: string | null) => void;
  reset: () => void;
}

export const useMeasurementStore = create<State>((set) => ({
  jobId: null,
  setJobId: (id) => set({ jobId: id }),
  reset: () => set({ jobId: null }),
}));
