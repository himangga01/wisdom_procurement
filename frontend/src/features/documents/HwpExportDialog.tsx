import { FormEvent, useEffect, useRef, useState } from "react";
import { api } from "../../app/api";
import type { DocumentRecord } from "../../app/types";

export function HwpExportDialog({ document: source, onClose }: { document: DocumentRecord; onClose: () => void }) {
  const [format, setFormat] = useState<"hwp" | "hwpx">(/\.hwpx$/i.test(source.original_file_name) ? "hwpx" : "hwp");
  const [find, setFind] = useState("");
  const [replace, setReplace] = useState("");
  const [busy, setBusy] = useState(false);
  const [available, setAvailable] = useState<boolean | null>(null);
  const [error, setError] = useState("");
  const panel = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let active = true;
    api.getHwpEngineStatus().then((status) => { if (active) setAvailable(status.available); })
      .catch(() => { if (active) { setAvailable(false); setError("한글 문서 기능 상태를 확인하지 못했습니다."); } });
    const previouslyFocused = window.document.activeElement as HTMLElement | null;
    panel.current?.focus();
    return () => { active = false; previouslyFocused?.focus(); };
  }, []);

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (busy || !available) return;
    setBusy(true);
    setError("");
    try {
      const blob = await api.exportHwpDocument(source.id, { format, ...(find ? { find, replace } : {}) });
      const url = URL.createObjectURL(blob);
      const link = window.document.createElement("a");
      link.href = url;
      link.download = `${source.original_file_name.split(/[\\/]/).pop()?.replace(/\.[^.]+$/, "") || "document"}_export.${format}`;
      window.document.body.appendChild(link);
      link.click();
      link.remove();
      window.setTimeout(() => URL.revokeObjectURL(url), 1000);
      onClose();
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : "한글 문서를 내보내지 못했습니다.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="app-modal-backdrop">
      <div className="app-modal-dialog" role="dialog" aria-modal="true" aria-labelledby="hwp-export-title"
        ref={panel} tabIndex={-1} onKeyDown={(event) => {
          if (event.key === "Escape" && !busy) onClose();
          if (event.key === "Tab") {
            const items = panel.current?.querySelectorAll<HTMLElement>("button:not(:disabled), input, select, textarea");
            if (!items?.length) return;
            const first = items[0], last = items[items.length - 1];
            if (event.shiftKey && (window.document.activeElement === first || window.document.activeElement === panel.current)) {
              event.preventDefault(); last.focus();
            } else if (!event.shiftKey && window.document.activeElement === last) {
              event.preventDefault(); first.focus();
            }
          }
        }}>
        <header className="app-modal-header">
          <div><h3 id="hwp-export-title">한글 문서 내보내기</h3><p>{source.original_file_name}</p></div>
          <button type="button" className="button-secondary" disabled={busy} onClick={onClose}>닫기</button>
        </header>
        <form className="app-modal-body" onSubmit={onSubmit}>
          <p>원본을 보존하고 새 파일로 내려받습니다. 내용 치환이 필요 없으면 치환 항목을 비워 두세요.</p>
          <label className="field"><span>출력 형식</span>
            <select value={format} disabled={busy} onChange={(event) => setFormat(event.target.value as "hwp" | "hwpx")}>
              <option value="hwp">HWP</option><option value="hwpx">HWPX</option>
            </select>
          </label>
          <label className="field"><span>치환할 내용 (선택)</span>
            <textarea value={find} maxLength={10000} rows={2} disabled={busy} onChange={(event) => setFind(event.target.value)} />
          </label>
          <label className="field"><span>바꿀 내용</span>
            <textarea value={replace} maxLength={10000} rows={2} disabled={busy || !find} onChange={(event) => setReplace(event.target.value)} />
          </label>
          {available === null && <p role="status">한글 문서 기능을 확인하고 있습니다.</p>}
          {available === false && <p role="alert">한글 문서 기능의 설치·설정을 확인하세요.</p>}
          {error && <p role="alert">{error}</p>}
          <div className="form-actions"><button type="submit" disabled={busy || available !== true}>
            {busy ? "저장본 검증 중…" : "새 파일 다운로드"}
          </button></div>
        </form>
      </div>
    </div>
  );
}
