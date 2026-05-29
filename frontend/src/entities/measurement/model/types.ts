export type AlgorithmId =
  | 'POS'
  | 'CHROM'
  | 'OMIT'
  | 'TS-CAN'
  | 'EfficientPhys'
  | 'PhysFormer'
  | 'RhythmFormer'
  | 'BigSmall';

export interface AlgorithmMeta {
  id: AlgorithmId;
  displayName: string;
  shortDescription: string;
  type: 'unsupervised' | 'supervised';
  backbone: string;
  pretrainedOn?: string | null;
  modelSizeMb?: number | null;
}

export interface HRVMetrics {
  hrBpm: number;
  ibiMeanMs: number;
  sdnnMs: number;
  rmssdMs: number;
  pnn50Pct: number;
  lfPower: number;
  hfPower: number;
  lfHfRatio: number;
  sd1: number;
  sd2: number;
}

export type BaevskyLevel = 'normal' | 'mild' | 'moderate' | 'high';
export type StressLevel = 'low' | 'mid' | 'high' | 'very_high';
export type ReliabilityGrade = 'low' | 'medium' | 'high';

export interface StressIndices {
  baevskySi: number;
  baevskyLevel: BaevskyLevel;
  lfHfStress: number;
  compositeScore: number;
  compositeLevel: StressLevel;
}

export interface ReliabilityComponents {
  snrDb: number;
  faceTrackingPct: number;
  deviationFromConsensus: number;
  motionPenalty: number;
}

export interface Reliability {
  score: number;
  grade: ReliabilityGrade;
  components: ReliabilityComponents;
}

export interface AlgorithmResult {
  meta: AlgorithmMeta;
  available: boolean;
  error?: string | null;
  hrv?: HRVMetrics | null;
  stress?: StressIndices | null;
  reliability?: Reliability | null;
  bvpSparkline: number[];
  extras?: Record<string, unknown> | null;
  computeMs: number;
}

export interface ConsensusResult {
  stressScore: number;
  stressLevel: StressLevel;
  hrBpm: number;
  rmssdMs: number;
  lfHfRatio: number;
  baevskySi: number;
  reliability: Reliability;
  contributingAlgorithms: number;
}

export interface VideoMeta {
  durationS: number;
  fps: number;
  resolution: [number, number];
}

export interface TimingInfo {
  totalMs: number;
  decodeMs: number;
  faceRoiMs: number;
  qualityMs: number;
  videoDurationS: number;
}

export type MeasurementStatus = 'queued' | 'processing' | 'done' | 'failed';

export interface MeasurementResponse {
  jobId: string;
  status: MeasurementStatus;
  progress: number;
  stage?: string;
  videoMeta?: VideoMeta | null;
  timing?: TimingInfo | null;
  consensus?: ConsensusResult | null;
  algorithms?: AlgorithmResult[] | null;
  warnings: string[];
  error?: string | null;
  disclaimer: string;
}
