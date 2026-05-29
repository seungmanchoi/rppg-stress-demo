import type { AlgorithmMeta } from '@entities/measurement';

export const ALGORITHM_DEFAULTS: AlgorithmMeta[] = [
  { id: 'POS', displayName: 'POS', shortDescription: '피부 톤 직교 평면 투영으로 혈류 분리 (de Haan 2014)', type: 'unsupervised', backbone: 'Signal processing' },
  { id: 'CHROM', displayName: 'CHROM', shortDescription: '피부 톤 표준화 후 색 차이 신호화 (de Haan 2013)', type: 'unsupervised', backbone: 'Signal processing' },
  { id: 'OMIT', displayName: 'OMIT', shortDescription: 'Orthogonal Matrix Image Transformation, 조명 강건', type: 'unsupervised', backbone: 'Signal processing' },
  { id: 'TS-CAN', displayName: 'TS-CAN', shortDescription: '2D-CNN + Temporal Shift, 모바일 실시간 친화', type: 'supervised', backbone: 'CNN+TSM', pretrainedOn: 'UBFC-rPPG', modelSizeMb: 30 },
  { id: 'EfficientPhys', displayName: 'EfficientPhys', shortDescription: '경량 CNN — 가장 빠른 supervised', type: 'supervised', backbone: 'Light CNN', pretrainedOn: 'UBFC-rPPG', modelSizeMb: 25 },
  { id: 'PhysFormer', displayName: 'PhysFormer', shortDescription: 'Video Transformer SOTA', type: 'supervised', backbone: 'Transformer', pretrainedOn: 'PURE', modelSizeMb: 200 },
  { id: 'RhythmFormer', displayName: 'RhythmFormer', shortDescription: 'Frequency-domain attention, HRV 안정', type: 'supervised', backbone: 'Freq-attention', pretrainedOn: 'PURE', modelSizeMb: 180 },
  { id: 'BigSmall', displayName: 'BigSmall', shortDescription: 'Multitask: BVP + 호흡수 + AU (BP4D 학습)', type: 'supervised', backbone: 'Multitask CNN', pretrainedOn: 'BP4D', modelSizeMb: 80 },
];
