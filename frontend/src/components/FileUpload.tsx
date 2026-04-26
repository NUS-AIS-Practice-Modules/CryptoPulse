interface FileUploadProps {
  file: File | null;
  onChange: (file: File | null) => void;
}

const ACCEPTED_TYPES = [".pdf", ".txt", ".docx"];

export function FileUpload({ file, onChange }: FileUploadProps) {
  return (
    <label className="flex cursor-pointer items-center gap-3 rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-4 py-3 transition hover:border-skyline hover:bg-white">
      <input
        type="file"
        accept={ACCEPTED_TYPES.join(",")}
        className="hidden"
        onChange={(event) => onChange(event.target.files?.[0] ?? null)}
      />
      <span className="rounded-full bg-white px-3 py-1 text-sm font-medium text-slate-700 shadow-sm">
        上传文件
      </span>
      <span className="truncate text-sm text-slate-500">
        {file ? file.name : "支持 PDF / TXT / DOCX（接口预留）"}
      </span>
    </label>
  );
}
