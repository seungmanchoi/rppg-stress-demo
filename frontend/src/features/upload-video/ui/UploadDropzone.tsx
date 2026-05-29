import { useDropzone } from 'react-dropzone';

import { useUpload } from '../model/useUpload';

export function UploadDropzone() {
  const { mutate, isPending, error, reset } = useUpload();
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: { 'video/mp4': ['.mp4'], 'video/webm': ['.webm'], 'video/quicktime': ['.mov'] },
    maxFiles: 1,
    multiple: false,
    onDrop: (files) => {
      reset();
      if (files[0]) mutate(files[0]);
    },
  });
  return (
    <div
      {...getRootProps()}
      className={`border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-colors ${
        isDragActive ? 'border-sky-500 bg-sky-50' : 'border-neutral-300 hover:border-neutral-400'
      }`}
    >
      <input {...getInputProps()} />
      {isPending ? (
        <p className="text-neutral-700">업로드 중…</p>
      ) : isDragActive ? (
        <p className="text-sky-700">여기에 놓으세요</p>
      ) : (
        <div className="space-y-1">
          <p className="font-medium">mp4 / webm / mov 영상을 끌어다 놓거나 클릭하세요</p>
          <p className="text-xs text-neutral-500">권장: 30~60초, 정면 얼굴, 균일 조명</p>
        </div>
      )}
      {error && <p className="text-rose-600 mt-3 text-sm">{(error as Error).message}</p>}
    </div>
  );
}
