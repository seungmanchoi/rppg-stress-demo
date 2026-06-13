import { Fragment, useCallback, useRef, useState } from 'react';

import { ALGORITHM_DEFAULTS } from '@entities/algorithm/model/registry';
import { useFaceTracker } from '@features/record-video/model/useFaceTracker';
import {
  TOTAL_STEPS,
  useFavMeasurement,
} from '@features/fav-measure/model/useFavMeasurement';
import type { FavResultData } from '@features/fav-measure/model/favApi';
import { AlgorithmCardsGrid } from '@widgets/algorithm-cards-grid/ui/AlgorithmCardsGrid';
import { ConsensusDashboard } from '@widgets/consensus-dashboard/ui/ConsensusDashboard';
import { MetricsGlossary } from '@widgets/metrics-glossary';
import { StressFormula } from '@widgets/stress-formula';
import { TierLegend } from '@widgets/tier-legend';

/**
 * FAV 동시 측정 — 얼굴(rPPG) 영상을 연속 녹화하면서 문장 4개를 소리 내어 읽는다.
 * 문장별로 음성을 끊어 녹음해 mentai-server의 기존 계약(음성 4파일 + 영상 1파일)을
 * 그대로 사용한다. 기존 happywings 플로우(음성 먼저 → 얼굴 나중)의 직렬 측정을
 * 한 번의 세션으로 합친 버전.
 */
export function FavMeasurePage() {
  const tracker = useFaceTracker();
  const fav = useFavMeasurement();
  const [permError, setPermError] = useState<string | null>(null);
  const [requesting, setRequesting] = useState(false);
  const hiddenVideoRef = useRef<HTMLVideoElement | null>(null);

  const attachHidden = useCallback(
    (el: HTMLVideoElement | null) => {
      hiddenVideoRef.current = el;
      tracker.attachVideo(el);
    },
    [tracker],
  );

  const handleEnableCamera = useCallback(async () => {
    setPermError(null);
    setRequesting(true);
    try {
      const stream = await fav.enableCamera();
      await tracker.start(stream);
    } catch (e) {
      setPermError((e as Error).message || '카메라/마이크 권한이 필요합니다');
    } finally {
      setRequesting(false);
    }
  }, [fav, tracker]);

  const handleReset = useCallback(() => {
    tracker.stop();
    fav.reset();
  }, [tracker, fav]);

  const isMeasuring = fav.phase === 'reading' || fav.phase === 'holding';
  const cameraOn = fav.phase !== 'idle';

  const renderSentence = () => {
    const sentence = fav.sentences[fav.step - 1];
    if (!sentence) return null;
    const lines = sentence.split('|');
    let idx = 0;
    return lines.map((line, li) => (
      <Fragment key={li}>
        {line.split('').map((ch, ci) => {
          const current = idx;
          idx += 1;
          return (
            <span
              key={ci}
              className="transition-colors duration-100"
              style={{ color: current < fav.charIndex ? '#0284c7' : '#1f2937' }}
            >
              {ch}
            </span>
          );
        })}
        {li < lines.length - 1 && <br />}
      </Fragment>
    ));
  };

  return (
    <main className="mx-auto max-w-5xl px-4 py-8 flex flex-col gap-6">
      <header>
        <h1 className="text-xl font-bold">FAV 동시 측정</h1>
        <p className="text-sm text-neutral-500 mt-1">
          카메라를 바라보며 문장 4개를 소리 내어 읽으세요. 얼굴(스트레스)과 음성(불안·우울)을{' '}
          <strong>동시에</strong> 측정한 뒤 mentai-server로 보내 분석합니다.
        </p>
      </header>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* ───── 카메라 패널 ───── */}
        <section className="rounded-2xl border bg-white p-5 shadow-sm flex flex-col gap-4">
          <header className="flex items-baseline justify-between">
            <h2 className="text-base font-semibold">카메라</h2>
            {isMeasuring && (
              <span className="text-xs text-neutral-500">
                녹화 {fav.elapsedSec}s {fav.elapsedSec < fav.minVideoSec && `(최소 ${fav.minVideoSec}s)`}
              </span>
            )}
          </header>

          <div className="relative bg-neutral-900 rounded-xl overflow-hidden aspect-square">
            <video
              ref={attachHidden}
              autoPlay
              playsInline
              muted
              className="absolute opacity-0 pointer-events-none w-px h-px -z-10"
            />
            <canvas
              ref={tracker.attachCanvas}
              className="w-full h-full object-cover transform -scale-x-100"
            />

            {!cameraOn && (
              <div className="absolute inset-0 flex flex-col items-center justify-center text-neutral-400 gap-3">
                <p className="text-sm">카메라와 마이크를 켜 주세요</p>
                <button
                  onClick={handleEnableCamera}
                  disabled={requesting}
                  className="px-4 py-2 bg-sky-500 text-white rounded-full text-sm font-medium hover:bg-sky-600 disabled:opacity-60"
                >
                  {requesting ? '권한 요청 중…' : '카메라·마이크 켜기'}
                </button>
              </div>
            )}

            {fav.phase === 'countdown' && (
              <div className="absolute inset-0 bg-black/60 flex items-center justify-center">
                <span className="text-white text-7xl font-bold">{fav.countdown}</span>
              </div>
            )}

            {cameraOn && tracker.loading && (
              <div className="absolute top-3 left-1/2 -translate-x-1/2 bg-black/70 text-white text-xs px-2 py-1 rounded-full">
                얼굴 검출기 로드 중…
              </div>
            )}
            {fav.phase === 'camera' && !tracker.loading && !tracker.faceDetected && (
              <div className="absolute top-3 left-1/2 -translate-x-1/2 bg-amber-500/90 text-white text-xs px-2 py-1 rounded-full">
                얼굴을 화면 안에 두세요
              </div>
            )}
            {isMeasuring && (
              <div className="absolute top-3 left-3 bg-rose-600 text-white text-xs px-2 py-1 rounded-full flex items-center gap-1.5">
                <span className="block w-2 h-2 bg-white rounded-full animate-pulse" /> REC
              </div>
            )}
            {fav.phase === 'holding' && (
              <div className="absolute bottom-3 left-1/2 -translate-x-1/2 bg-black/70 text-white text-xs px-3 py-1.5 rounded-full whitespace-nowrap">
                문장 끝! 카메라를 {fav.minVideoSec - fav.elapsedSec}초만 더 바라봐 주세요
              </div>
            )}
            {fav.phase === 'processing' && (
              <div className="absolute inset-0 bg-black/60 flex flex-col items-center justify-center gap-3 text-white text-sm">
                <Spinner />
                {fav.stage}
              </div>
            )}
          </div>

          {fav.phase === 'camera' && (
            <button
              onClick={fav.start}
              disabled={!tracker.faceDetected}
              className="px-5 py-2.5 bg-rose-500 text-white rounded-full text-sm font-semibold hover:bg-rose-600 disabled:opacity-50 disabled:cursor-not-allowed"
              title={tracker.faceDetected ? '' : '얼굴이 잡혀야 시작할 수 있습니다'}
            >
              동시 측정 시작
            </button>
          )}
        </section>

        {/* ───── 읽기 패널 ───── */}
        <section className="rounded-2xl border bg-white p-5 shadow-sm flex flex-col gap-4">
          <header className="flex items-baseline justify-between">
            <h2 className="text-base font-semibold">소리 내어 읽기</h2>
            {isMeasuring && (
              <span className="text-xs font-medium text-sky-600">
                {fav.step} / {TOTAL_STEPS}
              </span>
            )}
          </header>

          {fav.phase === 'idle' || fav.phase === 'camera' || fav.phase === 'countdown' ? (
            <div className="flex-1 flex items-center justify-center text-sm text-neutral-400 text-center leading-relaxed py-10">
              측정을 시작하면 여기에 문장이 나타납니다.
              <br />
              파란색으로 칠해지는 속도에 맞춰 또박또박 읽어주세요.
            </div>
          ) : fav.phase === 'reading' ? (
            <>
              <div className="flex-1 rounded-xl bg-neutral-50 border p-5 text-lg leading-relaxed flex items-center">
                <p>{renderSentence()}</p>
              </div>
              <p
                className={`text-center text-sm font-medium transition-colors ${
                  fav.readingDone ? 'text-sky-600' : 'text-neutral-500'
                }`}
              >
                {fav.readingDone
                  ? fav.step < TOTAL_STEPS
                    ? '잘하셨어요! 곧 다음 문장으로 넘어갑니다…'
                    : '잘하셨어요! 곧 측정을 마칩니다…'
                  : '파란색 속도에 맞춰 소리 내어 읽어주세요'}
              </p>
            </>
          ) : fav.phase === 'holding' ? (
            <div className="flex-1 flex items-center justify-center text-sm text-neutral-500 text-center py-10">
              네 문장을 모두 읽었습니다. 🎉
              <br />
              얼굴 측정을 위해 잠시 카메라를 바라봐 주세요.
            </div>
          ) : fav.phase === 'processing' ? (
            <div className="flex-1 flex flex-col items-center justify-center gap-2 text-sm text-neutral-500 py-10">
              <Spinner dark />
              <p>{fav.stage}</p>
              {fav.sessionId && (
                <p className="text-[11px] text-neutral-400">session: {fav.sessionId}</p>
              )}
            </div>
          ) : null}

          {fav.phase === 'done' && fav.result && (
            <div className="flex flex-col gap-4 items-center text-center">
              <div className="rounded-xl bg-sky-50 border border-sky-100 p-5 w-full">
                <p className="text-xs text-neutral-500">마음 건강 종합 점수</p>
                <p className="text-4xl font-bold text-sky-700 mt-1">{fav.result.score}</p>
                <p className="text-sm font-medium text-sky-600 mt-1">{fav.result.scoreLabel}</p>
              </div>
              <p className="text-xs text-neutral-500">아래에서 mentai·rPPG 상세 수치를 확인하세요 ↓</p>
              <button
                onClick={handleReset}
                className="px-5 py-2.5 border border-neutral-300 rounded-full text-sm font-medium hover:bg-neutral-50"
              >
                다시 측정하기
              </button>
            </div>
          )}

          {fav.phase === 'error' && (
            <div className="flex flex-col gap-3">
              <p className="text-sm text-rose-600 whitespace-pre-wrap break-all">{fav.error}</p>
              <button
                onClick={handleReset}
                className="px-5 py-2.5 border border-neutral-300 rounded-full text-sm font-medium hover:bg-neutral-50 self-start"
              >
                처음부터 다시
              </button>
            </div>
          )}

          {permError && <p className="text-sm text-rose-600">{permError}</p>}
        </section>
      </div>

      {/* ───── demo rPPG 분석 (메인) — 12알고리즘 + v1~v4 종합지수 ───── */}
      {fav.demo.status !== 'idle' && (
        <section className="flex flex-col gap-4 border-t pt-6">
          <header className="flex items-baseline justify-between">
            <div>
              <h2 className="text-lg font-bold">rPPG 정밀 분석 (12개 알고리즘)</h2>
              <p className="text-xs text-neutral-500 mt-0.5">
                같은 얼굴 영상을 12개 rPPG 알고리즘에 태워 v1~v4 종합지수와 합의값을 산출합니다.
                mentai 결과와 별개로 계산되며, 더 오래 걸릴 수 있습니다.
              </p>
            </div>
            {fav.demo.result?.timing && (
              <span className="text-xs text-neutral-400 tabular-nums whitespace-nowrap">
                분석 {(fav.demo.result.timing.totalMs / 1000).toFixed(1)}초
              </span>
            )}
          </header>

          {(fav.demo.status === 'uploading' || fav.demo.status === 'processing') && (
            <div className="rounded-2xl border bg-white p-5 shadow-sm flex flex-col gap-2">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium text-neutral-700">{fav.demo.stage || '분석 중…'}</span>
                <span className="tabular-nums text-neutral-500">
                  {Math.round((fav.demo.progress || 0) * 100)}%
                </span>
              </div>
              <div className="h-2 bg-neutral-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-sky-500 transition-all"
                  style={{ width: `${Math.round((fav.demo.progress || 0) * 100)}%` }}
                />
              </div>
            </div>
          )}

          {fav.demo.status === 'failed' && (
            <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
              rPPG 정밀 분석 실패: {fav.demo.error ?? '알 수 없는 오류'}
            </div>
          )}

          {fav.demo.result?.consensus && (
            <ConsensusDashboard
              data={fav.demo.result.consensus}
              totalAlgorithms={ALGORITHM_DEFAULTS.length}
            />
          )}

          {fav.demo.status === 'done' && <TierLegend />}

          {fav.demo.result?.algorithms && fav.demo.result.algorithms.length > 0 && (
            <AlgorithmCardsGrid results={fav.demo.result.algorithms} />
          )}

          {fav.demo.result?.warnings && fav.demo.result.warnings.length > 0 && (
            <ul className="text-sm text-amber-700 list-disc list-inside bg-amber-50 border border-amber-200 rounded-2xl p-4">
              {fav.demo.result.warnings.map((w) => (
                <li key={w}>{w}</li>
              ))}
            </ul>
          )}

          {fav.demo.status === 'done' && <StressFormula />}
          {fav.demo.status === 'done' && <MetricsGlossary />}
        </section>
      )}

      {/* ───── triton(mentai) 데이터 — demo 결과에 추가로 표시 ───── */}
      {fav.phase === 'done' && fav.result && <MentaiResultSection result={fav.result} />}

      <p className="text-[11px] text-neutral-400 leading-relaxed">
        영상은 문장을 읽는 내내 녹화되고(최소 30초), 음성은 문장별로 4개 파일로 나뉘어
        mentai-server로 전송됩니다. 같은 영상이 demo backend(:8800)의 12개 rPPG 알고리즘에도
        전송됩니다. 로컬 스택 기준이며 분석 결과는 DB에 저장되지 않습니다.
      </p>
    </main>
  );
}

const HRV_LABELS: Record<string, string> = {
  rmssd_nk: 'RMSSD',
  sdnn_nk: 'SDNN',
  pnn50_nk: 'pNN50',
  pnn20_nk: 'pNN20',
  cvnn_nk: 'CVNN',
  rmssd_manual: 'RMSSD(수동)',
  sdnn_manual: 'SDNN(수동)',
  pnn50_manual: 'pNN50(수동)',
  mo: 'Mode (Mo)',
  amo: 'AMo',
  mxdmn: 'MxDMn',
  data_retention_rate: '데이터 보존율',
  original_peaks_count: '검출 피크',
  cleaned_intervals_count: '유효 간격',
  signal_quality: '신호 품질',
};

function fmtNum(v?: number | null): string {
  if (v == null || typeof v !== 'number' || !Number.isFinite(v)) return '-';
  return Number.isInteger(v) ? String(v) : v.toFixed(2);
}

function MentaiResultSection({ result }: { result: FavResultData }) {
  const d = result.mentaiDetail;
  const voice = d?.voice;
  const hrv = d?.hrv;
  const vi = hrv?.video_info;
  const ha = hrv?.hrv_analysis ?? {};

  return (
    <section className="flex flex-col gap-4 border-t pt-6">
      <header>
        <h2 className="text-lg font-bold">mentai-server 측정 결과 (Triton)</h2>
        <p className="text-xs text-neutral-500 mt-0.5">
          음성(불안·우울)과 얼굴(스트레스)을 mentai-server가 분석한 값입니다. 점수는 높을수록 좋음.
        </p>
      </header>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <ScoreBox label="종합" value={result.score} sub={result.scoreLabel} accent />
        {result.items.map((it) => (
          <ScoreBox
            key={it.code}
            label={it.code === 'ANXIETY' ? '불안' : it.code === 'DEPRESSION' ? '우울' : '스트레스'}
            value={it.score}
            sub={it.label}
          />
        ))}
      </div>

      {voice && (
        <div className="rounded-2xl border bg-white p-4 shadow-sm">
          <h3 className="text-sm font-semibold mb-2.5">음성 분석 raw (Triton NeMo)</h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-x-6 gap-y-2 text-sm">
            <MetricBox label="불안 raw" value={fmtNum(voice.anxiety_score)} />
            <MetricBox label="우울 raw" value={fmtNum(voice.depression_score)} />
          </div>
        </div>
      )}

      {hrv && (
        <div className="rounded-2xl border bg-white p-4 shadow-sm">
          <h3 className="text-sm font-semibold mb-2.5">얼굴 분석 (rPPG / HRV)</h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-x-6 gap-y-2 text-sm">
            <MetricBox label="Baevsky SI" value={fmtNum(hrv.stress_index)} />
            <MetricBox
              label="평균 심박"
              value={hrv.average_heart_rate != null ? `${hrv.average_heart_rate} BPM` : '-'}
            />
            {vi?.duration_seconds != null && (
              <MetricBox label="영상 길이" value={`${vi.duration_seconds}초`} />
            )}
            {vi?.processed_frames != null && (
              <MetricBox label="프레임" value={`${vi.processed_frames}`} />
            )}
            {Object.entries(ha).map(([k, v]) => (
              <MetricBox
                key={k}
                label={HRV_LABELS[k] ?? k}
                value={typeof v === 'number' ? fmtNum(v) : String(v)}
              />
            ))}
          </div>
        </div>
      )}
    </section>
  );
}

function ScoreBox({
  label,
  value,
  sub,
  accent = false,
}: {
  label: string;
  value: number;
  sub?: string;
  accent?: boolean;
}) {
  return (
    <div className={`rounded-xl border p-3 text-center ${accent ? 'bg-sky-50 border-sky-100' : ''}`}>
      <p className="text-[11px] text-neutral-500">{label}</p>
      <p className={`text-2xl font-bold mt-0.5 ${accent ? 'text-sky-700' : ''}`}>{value}</p>
      {sub && <p className="text-xs text-neutral-500">{sub}</p>}
    </div>
  );
}

function MetricBox({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-[11px] text-neutral-500 uppercase tracking-wider">{label}</div>
      <div className="text-base font-semibold">{value}</div>
    </div>
  );
}

function Spinner({ dark = false }: { dark?: boolean }) {
  return (
    <span
      className={`block w-6 h-6 rounded-full border-2 border-t-transparent animate-spin ${
        dark ? 'border-neutral-400' : 'border-white'
      }`}
    />
  );
}
