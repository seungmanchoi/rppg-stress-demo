import type { AlgorithmId, AlgorithmMeta } from '@entities/measurement';

export interface AlgorithmDetails {
  /** "이 알고리즘이 분석하는 것은 무엇인가" 한 단락 설명 */
  analyzes: string;
  /** "어떻게 동작하는가" 한 단락 설명 (전처리 + 핵심 아이디어) */
  methodology: string;
  /** 원본 논문/연도 표시용 */
  citation?: string;
}

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

export const ALGORITHM_DETAILS: Record<AlgorithmId, AlgorithmDetails> = {
  POS: {
    analyzes:
      '얼굴 ROI(이마·양 볼)의 프레임별 평균 RGB 변화를 분석해서, 혈관의 부피 변동(BVP)을 추정합니다. 추정된 BVP의 주파수 피크가 곧 심박수입니다.',
    methodology:
      'RGB 신호를 "피부 톤 표준 색"에 직교하는 평면(plane-orthogonal-to-skin)에 사영해, 조명 변화는 줄이고 혈류로 인한 미세 색 변동만 남깁니다. 1.6초 슬라이딩 윈도우로 신호를 안정화합니다.',
    citation: 'Wang et al., IEEE TBME 2017',
  },
  CHROM: {
    analyzes:
      'POS와 마찬가지로 ROI 평균 RGB의 색 변동을 분석합니다. 다만 두 chrominance(색차) 채널을 정의해 그 차이에서 BVP를 추출합니다.',
    methodology:
      '피부 톤 표준화 후 X = 3R − 2G, Y = 1.5R + G − 1.5B 두 chrominance 신호를 만들고, 두 채널의 표준편차 비율을 사용해 움직임 잡음을 상쇄합니다.',
    citation: 'de Haan & Jeanne, IEEE TBME 2013',
  },
  OMIT: {
    analyzes:
      'ROI RGB 시계열에서 BVP를 추출합니다. 조명 변화·움직임에 가장 강건한 unsupervised 방법입니다.',
    methodology:
      'RGB 행렬을 QR 분해하여 직교 기저(orthogonal matrix)를 얻고, 첫 번째 기저(skin tone direction)를 제외한 두 번째 기저를 BVP 신호로 사용합니다.',
    citation: 'Álvarez Casado & Bordallo López, JBHI 2023',
  },
  'TS-CAN': {
    analyzes:
      '얼굴 영상을 직접 입력으로 받아 BVP 파형을 예측합니다. UBFC-rPPG에서 학습되어 일반 실내 셀카 영상에 잘 맞습니다.',
    methodology:
      '두 stream CNN — motion stream(DiffNormalized 프레임 차분)과 appearance stream(Standardized raw 프레임). Temporal Shift Module(TSM)이 시간축 정보를 채널 축으로 섞어 2D conv만으로 시계열 처리. attention mask로 얼굴 영역에 집중.',
    citation: 'Liu et al., NeurIPS 2020',
  },
  EfficientPhys: {
    analyzes:
      '얼굴 영상 → BVP. TS-CAN보다 적은 파라미터로 같은 작업을 수행하는 경량 모델입니다.',
    methodology:
      '단일 stream 경량 CNN. 모델 내부에서 torch.diff(dim=0)로 frame difference + BatchNorm을 자동 적용해 별도 motion 전처리가 필요 없습니다. TSM과 self-attention mask 결합.',
    citation: 'Liu et al., WACV 2023',
  },
  PhysFormer: {
    analyzes:
      '얼굴 영상을 비디오 단위(160프레임 ≈ 5.3초)로 받아 BVP 시퀀스 전체를 한 번에 예측합니다.',
    methodology:
      'Conv3D patch embedding(4×4×4 토큰화)으로 시공간 큐브를 토큰화한 뒤, Temporal Difference Convolution + 12-layer Transformer로 attention. gradient sharpening(γ=2.0)으로 안정 학습.',
    citation: 'Yu et al., CVPR 2022',
  },
  RhythmFormer: {
    analyzes:
      '얼굴 영상에서 BVP를 추출하되, 특히 주기적 변동(맥파 리듬) 패턴에 강하도록 설계되었습니다.',
    methodology:
      'Fusion Stem(다중 conv + 시간 stem)으로 초기 특징을 추출한 뒤, 주파수 영역 attention(BiFormer 변형)을 사용해 주기성을 강조합니다. HRV 산출 안정성이 좋습니다.',
    citation: 'Zou et al., 2024',
  },
  BigSmall: {
    analyzes:
      'BVP 외에 호흡수(respiration)와 안면 액션 유닛(AU)을 동시에 추정하는 멀티태스크 모델입니다.',
    methodology:
      '두 해상도 branch — Big(144×144 Standardized: 얼굴 디테일)와 Small(9×9 DiffNormalized: 큰 움직임). 두 stream을 합치고 BVP·Resp·AU 세 출력 head로 분기. BP4D 데이터셋(스트레스 유발 표정)으로 학습.',
    citation: 'Narayanswamy et al., WACV 2024',
  },
};
