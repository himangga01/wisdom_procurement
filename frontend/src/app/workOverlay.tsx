import { createContext, ReactNode, useContext, useEffect, useRef, useState } from "react";

type ToastTone = "success" | "error" | "info";

type WorkOverlayOptions = {
  title: string;
  description?: string;
  steps?: string[];
  successMessage?: string;
  failureMessage?: string;
  minVisibleMs?: number;
  blockNavigation?: boolean;
};

type ActiveTask = Required<Pick<WorkOverlayOptions, "title" | "steps" | "minVisibleMs" | "blockNavigation">> &
  Pick<WorkOverlayOptions, "description"> & {
    id: number;
    currentStep: number;
    startedAt: number;
  };

type WorkToast = {
  id: number;
  tone: ToastTone;
  message: string;
  detail?: string;
};

type WorkOverlayContextValue = {
  active: boolean;
  runWithOverlay: <T>(options: WorkOverlayOptions, action: () => Promise<T>) => Promise<T>;
  showToast: (message: string, tone?: ToastTone, detail?: string) => void;
};

const DEFAULT_STEPS = ["요청 준비", "서버 처리", "결과 반영"];
const WorkOverlayContext = createContext<WorkOverlayContextValue | null>(null);

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : "알 수 없는 오류가 발생했습니다.";
}

export function WorkOverlayProvider({ children }: { children: ReactNode }) {
  const [activeTask, setActiveTask] = useState<ActiveTask | null>(null);
  const [toasts, setToasts] = useState<WorkToast[]>([]);
  const nextIdRef = useRef(1);

  const showToast = (message: string, tone: ToastTone = "success", detail?: string) => {
    const id = nextIdRef.current++;
    setToasts((prev) => [...prev, { id, tone, message, detail }]);
    window.setTimeout(() => {
      setToasts((prev) => prev.filter((toast) => toast.id !== id));
    }, 3200);
  };

  const runWithOverlay = async <T,>(options: WorkOverlayOptions, action: () => Promise<T>) => {
    const id = nextIdRef.current++;
    const startedAt = Date.now();
    const task: ActiveTask = {
      id,
      title: options.title,
      description: options.description,
      steps: options.steps?.length ? options.steps : DEFAULT_STEPS,
      currentStep: 0,
      startedAt,
      minVisibleMs: options.minVisibleMs ?? 450,
      blockNavigation: options.blockNavigation ?? true,
    };

    setActiveTask(task);

    try {
      const result = await action();
      const remainingMs = Math.max(0, task.minVisibleMs - (Date.now() - startedAt));
      if (remainingMs > 0) {
        await new Promise((resolve) => window.setTimeout(resolve, remainingMs));
      }
      setActiveTask((prev) => (prev?.id === id ? null : prev));
      if (options.successMessage) {
        showToast(options.successMessage, "success");
      }
      return result;
    } catch (error) {
      const remainingMs = Math.max(0, task.minVisibleMs - (Date.now() - startedAt));
      if (remainingMs > 0) {
        await new Promise((resolve) => window.setTimeout(resolve, remainingMs));
      }
      setActiveTask((prev) => (prev?.id === id ? null : prev));
      showToast(options.failureMessage ?? "작업을 완료하지 못했습니다.", "error", errorMessage(error));
      throw error;
    }
  };

  useEffect(() => {
    if (!activeTask) return;
    const timer = window.setInterval(() => {
      setActiveTask((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          currentStep: Math.min(prev.currentStep + 1, prev.steps.length - 1),
        };
      });
    }, 1200);
    return () => window.clearInterval(timer);
  }, [activeTask?.id]);

  useEffect(() => {
    if (!activeTask?.blockNavigation) return;
    const onBeforeUnload = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      event.returnValue = "";
    };
    window.addEventListener("beforeunload", onBeforeUnload);
    return () => window.removeEventListener("beforeunload", onBeforeUnload);
  }, [activeTask?.blockNavigation]);

  return (
    <WorkOverlayContext.Provider value={{ active: Boolean(activeTask), runWithOverlay, showToast }}>
      {children}

      {activeTask ? (
        <div className="work-overlay-backdrop" role="dialog" aria-modal="true" aria-live="polite">
          <div className="work-overlay-panel">
            <div className="work-overlay-spinner" aria-hidden="true" />
            <div className="work-overlay-copy">
              <p className="eyebrow">Processing</p>
              <h3>{activeTask.title}</h3>
              {activeTask.description ? <p>{activeTask.description}</p> : null}
            </div>
            <div className="work-overlay-progress" role="progressbar" aria-label="작업 처리 진행 중">
              <span />
            </div>
            <ol className="work-step-list">
              {activeTask.steps.map((step, index) => (
                <li
                  key={step}
                  className={[
                    "work-step",
                    index < activeTask.currentStep ? "work-step--done" : "",
                    index === activeTask.currentStep ? "work-step--active" : "",
                  ]
                    .filter(Boolean)
                    .join(" ")}
                >
                  <span>{index + 1}</span>
                  <strong>{step}</strong>
                </li>
              ))}
            </ol>
          </div>
        </div>
      ) : null}

      {toasts.length ? (
        <div className="work-toast-stack" aria-live="polite">
          {toasts.map((toast) => (
            <div key={toast.id} className={`work-toast work-toast--${toast.tone}`}>
              <strong>{toast.message}</strong>
              {toast.detail ? <span>{toast.detail}</span> : null}
            </div>
          ))}
        </div>
      ) : null}
    </WorkOverlayContext.Provider>
  );
}

export function useWorkOverlay() {
  const context = useContext(WorkOverlayContext);
  if (!context) {
    throw new Error("useWorkOverlay must be used inside WorkOverlayProvider.");
  }
  return context;
}
