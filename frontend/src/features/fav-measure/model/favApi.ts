// FAV 측정 체인 API — happywings_fav와 동일한 계약으로 호출한다.
// 로컬 스택 기본값: mock(:9300) + mentai-server(:5500)
// (mentai-server 레포 docs/LOCAL_DEV_STACK.md 참고)

const TOKEN_URL =
  (import.meta.env.VITE_FAV_TOKEN_URL as string | undefined) ??
  'http://localhost:9300/fav-v2-result/stk';
const ADMIN_BASE =
  (import.meta.env.VITE_FAV_ADMIN_BASE as string | undefined) ?? 'http://localhost:9300';
const MENTAI_BASE =
  (import.meta.env.VITE_FAV_MENTAI_BASE as string | undefined) ?? 'http://localhost:5500';
const RESULT_BASE =
  (import.meta.env.VITE_FAV_RESULT_BASE as string | undefined) ?? 'http://localhost:9300';

const COMPANY = 'skt_happywings';
const LEV = '1';

export interface FavResultItem {
  code: 'ANXIETY' | 'DEPRESSION' | 'STRESS' | string;
  score: number;
  label: string;
  comment: string;
}

export interface MentaiVoiceDetail {
  anxiety_score?: number;
  depression_score?: number;
}

export interface MentaiHrvDetail {
  stress_score?: number;
  stress_index?: number;
  average_heart_rate?: number;
  video_info?: { fps?: number; processed_frames?: number; duration_seconds?: number };
  hrv_analysis?: Record<string, number | string>;
}

export interface MentaiDetail {
  voice?: MentaiVoiceDetail | null;
  hrv?: MentaiHrvDetail | null;
}

export interface FavResultData {
  score: number;
  scoreLabel: string;
  scoreComment: string;
  items: FavResultItem[];
  mentaiDetail?: MentaiDetail | null;
}

interface PresignedFile {
  fileName: string;
  objectKey?: string;
  uploadURL: string;
}

async function jsonFetch<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) {
    const body = await res.text().catch(() => '');
    throw new Error(`${url} → HTTP ${res.status} ${body.slice(0, 200)}`);
  }
  return res.json() as Promise<T>;
}

/** 1. 토큰 발급 → user_id */
export async function issueUserId(): Promise<string> {
  const data = await jsonFetch<{ success: boolean; data: { user_id: string } }>(TOKEN_URL);
  if (!data.success || !data.data?.user_id) throw new Error('토큰 발급 실패');
  return data.data.user_id;
}

/** 2. presigned URL 발급 */
export async function getPresigned(
  sessionId: string,
  userId: string,
  files: Array<{ name: string; mimeType: string }>,
): Promise<PresignedFile[]> {
  const data = await jsonFetch<{ result: { files: PresignedFile[] } }>(
    `${ADMIN_BASE}/v1/admin/presigned-urls`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ companyName: COMPANY, sessionId, userId, files }),
    },
  );
  const out = data.result?.files;
  if (!Array.isArray(out) || out.length !== files.length) {
    throw new Error('presigned URL 응답 형식 오류');
  }
  return out;
}

/** 3. 파일 업로드 (S3 PUT 대체) */
export async function putFile(uploadURL: string, file: File): Promise<void> {
  const res = await fetch(uploadURL, {
    method: 'PUT',
    body: file,
    headers: { 'Content-Type': file.type },
  });
  if (!res.ok) throw new Error(`업로드 실패 (${file.name}): HTTP ${res.status}`);
}

/** presigned URL에서 object key 추출 — happywings와 동일하게 마지막 4세그먼트 */
export function extractObjectKey(presigned: PresignedFile): string {
  if (presigned.objectKey) return presigned.objectKey;
  const path = new URL(presigned.uploadURL).pathname;
  const parts = path.split('/').filter(Boolean);
  return parts.slice(-4).join('/');
}

/** 4. 얼굴(rPPG) 분석 요청 */
export async function requestFaceAnalysis(
  sessionId: string,
  userId: string,
  videoKey: string,
): Promise<void> {
  await jsonFetch(`${MENTAI_BASE}/face`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      user_id: userId,
      lev: LEV,
      files: videoKey,
      company: COMPANY,
      dev: false,
    }),
  });
}

/** 5. 음성 분석 요청 — 서버 계약상 정확히 4개 파일 (키 "3","4","7","8") */
export async function requestVoiceAnalysis(
  sessionId: string,
  userId: string,
  voiceKeys: string[],
): Promise<void> {
  if (voiceKeys.length !== 4) throw new Error(`음성 파일은 4개여야 합니다 (현재 ${voiceKeys.length}개)`);
  const keys = ['3', '4', '7', '8'];
  const filesDict: Record<string, string> = {};
  voiceKeys.forEach((k, i) => {
    filesDict[keys[i]] = k;
  });
  await jsonFetch(`${MENTAI_BASE}/mentai-analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      lev: LEV,
      user_id: userId,
      callback: `${MENTAI_BASE}/mentai-callback/`,
      files: filesDict,
      company: COMPANY,
      dev: false,
    }),
  });
}

interface PollResponse {
  is_completed: boolean;
  result: {
    success: boolean;
    status: string;
    data: FavResultData | null;
    error: { code?: string; message?: string } | null;
  };
}

/** 6. 결과 폴링 — voice/hrv 둘 다 도착하면 completed */
export async function pollResult(
  sessionId: string,
  opts: { intervalMs?: number; timeoutMs?: number; onTick?: (elapsedSec: number) => void } = {},
): Promise<FavResultData> {
  const { intervalMs = 3000, timeoutMs = 5 * 60 * 1000, onTick } = opts;
  const startedAt = Date.now();
  for (;;) {
    // 분석 결과는 빨라야 수 초 뒤에 나오므로 첫 조회 전에도 한 박자 쉰다
    // (happywings FE의 5초 인터벌 폴링과 동일한 타이밍 특성)
    await new Promise((r) => setTimeout(r, intervalMs));

    const elapsed = Date.now() - startedAt;
    if (elapsed > timeoutMs) throw new Error('분석 결과 대기 시간 초과 (5분)');
    onTick?.(Math.round(elapsed / 1000));

    const data = await jsonFetch<PollResponse>(`${RESULT_BASE}/fav-v2-result/${sessionId}`);
    if (data.is_completed) {
      if (data.result.success && data.result.data) return data.result.data;
      throw new Error(
        `분석 실패: ${data.result.error?.code ?? ''} ${data.result.error?.message ?? '알 수 없는 오류'}`,
      );
    }
    await new Promise((r) => setTimeout(r, intervalMs));
  }
}
