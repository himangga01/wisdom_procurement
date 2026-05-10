import type { AiModelOption, AiModelSelection, AiModelSettings } from "./types";

const STORAGE_KEY = "wisdom_procurement.ai_model_selection";

export const FALLBACK_AI_MODEL_OPTIONS: AiModelOption[] = [
  {
    provider: "gemini",
    model: "gemini-2.5-flash",
    label: "Gemini 2.5 Flash",
    description: "저비용/고속 요약 기본값입니다.",
    configured: false,
    recommended: true,
  },
  {
    provider: "openai",
    model: "gpt-5.4-mini",
    label: "OpenAI gpt-5.4-mini",
    description: "기존 OpenAI 요약 경로입니다.",
    configured: false,
    recommended: false,
  },
];

export function selectionToKey(selection: AiModelSelection) {
  return `${selection.model_provider}:${selection.model_name}`;
}

export function keyToSelection(value: string): AiModelSelection {
  const [provider, ...modelParts] = value.split(":");
  return {
    model_provider: provider || "gemini",
    model_name: modelParts.join(":") || "gemini-2.5-flash",
  };
}

export function defaultSelection(settings?: AiModelSettings | null): AiModelSelection {
  return {
    model_provider: settings?.default_provider || "gemini",
    model_name: settings?.default_model || "gemini-2.5-flash",
  };
}

export function loadStoredSelection(settings?: AiModelSettings | null): AiModelSelection {
  const fallback = defaultSelection(settings);
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return fallback;
    const parsed = JSON.parse(raw) as Partial<AiModelSelection>;
    if (!parsed.model_provider || !parsed.model_name) return fallback;
    return {
      model_provider: parsed.model_provider,
      model_name: parsed.model_name,
    };
  } catch {
    return fallback;
  }
}

export function saveStoredSelection(selection: AiModelSelection) {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(selection));
}

export function optionsFromSettings(settings?: AiModelSettings | null) {
  return settings?.options?.length ? settings.options : FALLBACK_AI_MODEL_OPTIONS;
}
