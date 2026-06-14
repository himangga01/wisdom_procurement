import { useEffect, useMemo, useState } from "react";

import { api } from "../app/api";
import type { BackupRestorePlan, BackupRun, BackupValidation } from "../app/types";
import { useWorkOverlay } from "../app/workOverlay";

function statusTone(status: string) {
  if (status === "completed" || status === "ok") return "active";
  if (status === "failed" || status === "invalid") return "pending";
  return "muted";
}

function formatDate(value: string | null) {
  if (!value) return "-";
  return new Date(value).toLocaleString("ko-KR");
}

function formatBytes(value: number) {
  if (!value) return "0 B";
  if (value < 1024 * 1024) return `${Math.round(value / 1024)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

function normalizeBackupValidation(value: BackupRun["validation"] | null | undefined, fallbackError = ""): BackupValidation | null {
  if (!value || typeof value !== "object") {
    return fallbackError
      ? { valid: false, errors: [fallbackError], warnings: [], manifest: {}, file_path: "", file_size_bytes: 0 }
      : null;
  }
  const candidate = value as Partial<BackupValidation>;
  const errors = Array.isArray(candidate.errors) ? candidate.errors.map(String) : fallbackError ? [fallbackError] : [];
  const warnings = Array.isArray(candidate.warnings) ? candidate.warnings.map(String) : [];
  return {
    valid: typeof candidate.valid === "boolean" ? candidate.valid : false,
    errors,
    warnings,
    manifest: candidate.manifest && typeof candidate.manifest === "object" ? candidate.manifest : {},
    file_path: typeof candidate.file_path === "string" ? candidate.file_path : "",
    file_size_bytes: typeof candidate.file_size_bytes === "number" ? candidate.file_size_bytes : 0,
  };
}

export function BackupsPage() {
  const { runWithOverlay } = useWorkOverlay();
  const [backups, setBackups] = useState<BackupRun[]>([]);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [validation, setValidation] = useState<BackupValidation | null>(null);
  const [restorePlan, setRestorePlan] = useState<BackupRestorePlan | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const activeBackup = useMemo(() => backups.find((item) => item.id === activeId) ?? backups[0] ?? null, [backups, activeId]);

  const refresh = async (nextActiveId?: number | null) => {
    setLoading(true);
    try {
      const data = await api.listBackups();
      setBackups(data);
      setActiveId(nextActiveId === null ? data[0]?.id ?? null : nextActiveId ?? activeId ?? data[0]?.id ?? null);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "백업 목록을 불러오지 못했습니다.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  const onCreateBackup = async () => {
    await runWithOverlay(
      {
        title: "백업 생성 중",
        description: "SQLite DB와 storage 파일을 ZIP으로 묶고 manifest를 검증합니다.",
        steps: ["DB 포함", "storage 포함", "manifest 생성", "checksum 검증"],
        successMessage: "백업 요청 결과를 반영했습니다.",
        failureMessage: "백업 생성에 실패했습니다.",
      },
      async () => {
        const created = await api.createBackup();
        const createdValidation = normalizeBackupValidation(created.validation, created.error_message);
        setValidation(createdValidation);
        setRestorePlan(null);
        await refresh(created.id);
        if (created.status === "completed") {
          setError("");
        } else {
          setError(
            created.error_message ||
              createdValidation?.errors?.join(" / ") ||
              "백업 생성 결과가 실패 상태입니다. 백업 이력에서 상세 내용을 확인하세요.",
          );
        }
      },
    );
  };

  const onValidate = async () => {
    if (!activeBackup) return;
    const result = await api.validateBackup(activeBackup.id);
    setValidation(result);
  };

  const onRestorePlan = async () => {
    if (!activeBackup) return;
    const result = await api.createBackupRestorePlan(activeBackup.id);
    setRestorePlan(result);
    setValidation(result.validation);
  };

  const onDryRunRestore = async () => {
    if (!activeBackup) return;
    await runWithOverlay(
      {
        title: "복원 dry-run 검증 중",
        description: "백업 manifest와 checksum을 확인하고 복원 절차만 생성합니다.",
        steps: ["manifest 확인", "checksum 확인", "복원 절차 생성"],
        successMessage: "복원 dry-run 검증을 완료했습니다.",
        failureMessage: "복원 dry-run 검증에 실패했습니다.",
      },
      async () => {
        const result = await api.dryRunBackupRestore(activeBackup.id);
        setRestorePlan(result);
        setValidation(result.validation);
      },
    );
  };

  return (
    <section className="page-grid">
      <div className="page-title">
        <p className="eyebrow">백업/복원</p>
        <h1>백업/복원</h1>
        <p>로컬 DB와 storage 파일을 ZIP으로 백업하고, 복원 전 dry-run 검증을 수행합니다.</p>
      </div>

      {error ? (
        <div className="notice notice--error">
          <strong>확인 필요</strong>
          <span>{error}</span>
        </div>
      ) : null}

      <div className="surface-card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">백업 생성</p>
            <h3>백업 만들기</h3>
          </div>
          <button type="button" onClick={onCreateBackup}>
            백업 생성
          </button>
        </div>
        <div className="empty-state empty-state--info">
          <strong>포함 항목</strong>
          <p>SQLite DB, uploads, corporation-evidence, basis, basis-index, nara-notices, contracts를 포함합니다. .env 원문 API 키는 포함하지 않습니다.</p>
        </div>
      </div>

      <div className="surface-card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">백업 이력</p>
            <h3>백업 이력</h3>
          </div>
          <button type="button" className="button-secondary" onClick={() => refresh()}>
            새로고침
          </button>
        </div>

        {!backups.length ? (
          <div className="empty-state">
            <strong>{loading ? "불러오는 중입니다." : "백업 이력이 없습니다."}</strong>
            <p>백업을 생성하면 이력이 여기에 표시됩니다.</p>
          </div>
        ) : (
          <div className="collection-run-list">
            {backups.map((backup) => (
              <button
                type="button"
                className={`collection-run-row${activeBackup?.id === backup.id ? " active" : ""}`}
                key={backup.id}
                onClick={() => {
                  setActiveId(backup.id);
                  setValidation(null);
                  setRestorePlan(null);
                }}
              >
                <span className={`status-badge status-badge--${statusTone(backup.status)}`}>{backup.status}</span>
                <strong>{backup.file_name || `backup #${backup.id}`}</strong>
                <span>{formatBytes(backup.file_size_bytes)}</span>
                <small>{formatDate(backup.created_at)}</small>
              </button>
            ))}
          </div>
        )}
      </div>

      {activeBackup ? (
        <div className="surface-card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">백업 검증</p>
              <h3>검증과 복원 dry-run</h3>
            </div>
            <div className="toolbar">
              <button type="button" className="button-secondary" onClick={onValidate}>
                검증
              </button>
              <button type="button" className="button-secondary" onClick={onRestorePlan}>
                복원 계획
              </button>
              <button type="button" onClick={onDryRunRestore}>
                Dry-run
              </button>
            </div>
          </div>

          <div className="metric-grid">
            <article>
              <span>백업 ID</span>
              <strong>#{activeBackup.id}</strong>
            </article>
            <article>
              <span>상태</span>
              <strong>{activeBackup.status}</strong>
            </article>
            <article>
              <span>크기</span>
              <strong>{formatBytes(activeBackup.file_size_bytes)}</strong>
            </article>
            <article>
              <span>완료 시각</span>
              <strong>{formatDate(activeBackup.completed_at)}</strong>
            </article>
          </div>

          {validation ? (
            <div className={`empty-state ${validation.valid ? "empty-state--info" : "empty-state--warning"}`}>
              <strong>{validation.valid ? "검증 통과" : "검증 실패"}</strong>
              <p>{validation.errors.length ? validation.errors.join(" / ") : "manifest와 checksum이 유효합니다."}</p>
              {validation.warnings.length ? <small>{validation.warnings.join(" / ")}</small> : null}
            </div>
          ) : null}

          {restorePlan ? (
            <div className="result-list">
              {restorePlan.restore_steps.map((step, index) => (
                <article className="result-row" key={step}>
                  <div>
                    <strong>{index + 1}. {step}</strong>
                    <span>{restorePlan.policy}</span>
                  </div>
                </article>
              ))}
            </div>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
