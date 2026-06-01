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
  // Time-domain (ESC/NASPE 1996)
  hrBpm: number;
  ibiMeanMs: number;
  sdnnMs: number;
  rmssdMs: number;
  sdsdMs: number;
  pnn50Pct: number;
  pnn20Pct: number;
  cvnnPct: number;
  hrvTriangularIndex: number;
  // Frequency-domain
  vlfPower: number;
  lfPower: number;
  hfPower: number;
  totalPower: number;
  lfHfRatio: number;
  lfNu: number;
  hfNu: number;
  // Non-linear
  sd1: number;
  sd2: number;
  sdRatio: number;
  ellipseArea: number;
  sampleEntropy: number;
  approximateEntropy: number;
  shannonEntropy: number;
  dfaAlpha1: number;
  higuchiFd: number;
}

export type BaevskyLevel = 'normal' | 'mild' | 'moderate' | 'high';
export type StressLevel = 'low' | 'mid' | 'high' | 'very_high';
export type ReliabilityGrade = 'low' | 'medium' | 'high';

export interface StressIndices {
  baevskySi: number;
  baevskyLevel: BaevskyLevel;
  baevskyMoS: number;
  baevskyAmoPct: number;
  baevskyMxdmnS: number;
  lfHfStress: number;
  compositeScore: number;
  compositeLevel: StressLevel;
  pnsIndex: number;
  snsIndex: number;
  coherenceScore: number;
  coherencePeakHz: number;
}

export interface HemodynamicMetrics {
  spo2Pct: number;
  spo2Confidence: number;
  pulseRiseTimeMs: number;
}

export interface RespirationMetrics {
  rateRpm: number;
  confidence: number;
}

export interface SignalQuality {
  pqi: number;
  spectralEntropy: number;
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
  respiration?: RespirationMetrics | null;
  hemodynamic?: HemodynamicMetrics | null;
  signalQuality?: SignalQuality | null;
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
