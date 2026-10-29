"use client";

import { useEffect, useState } from "react";
import {
  applyUiTheme,
  DEFAULT_UI_THEME,
  migrateLegacyTheme,
  readStoredUiTheme,
  UI_THEME_KEY,
  type UiTheme,
} from "@/lib/ui-theme";

export type { UiTheme };

export interface OceanSettingsState {
  /** 背景動畫開關 */
  enabled: boolean;
  /** 鯊魚數量（1–8） */
  sharkCount: number;
  /** UI + ASCII theme */
  theme: UiTheme;
}

const KEY = "ai_prepare.ocean";
const MIN_SHARKS = 0;
const MAX_SHARKS = 8;
const DEFAULTS: OceanSettingsState = {
  enabled: true,
  sharkCount: 4,
  theme: DEFAULT_UI_THEME,
};

function clampCount(n: number) {
  return Math.max(MIN_SHARKS, Math.min(MAX_SHARKS, Math.round(n)));
}

function load(): OceanSettingsState {
  if (typeof window === "undefined") return DEFAULTS;
  try {
    const raw = window.localStorage.getItem(KEY);
    const theme = readStoredUiTheme();
    if (!raw) {
      return { ...DEFAULTS, theme };
    }
    const p = JSON.parse(raw) as Partial<OceanSettingsState> & {
      theme?: unknown;
    };
    return {
      enabled: typeof p.enabled === "boolean" ? p.enabled : DEFAULTS.enabled,
      sharkCount:
        typeof p.sharkCount === "number"
          ? clampCount(p.sharkCount)
          : DEFAULTS.sharkCount,
      theme: p.theme != null ? migrateLegacyTheme(p.theme) : theme,
    };
  } catch {
    return DEFAULTS;
  }
}

/**
 * ASCII 海洋 + UI Theme 設定，持久化到 localStorage。
 * Theme 變更會同步 `document.documentElement.dataset.theme`。
 */
export function useOceanSettings() {
  const [state, setState] = useState<OceanSettingsState>(DEFAULTS);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    const next = load();
    setState(next);
    applyUiTheme(next.theme);
    setHydrated(true);
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    try {
      window.localStorage.setItem(KEY, JSON.stringify(state));
      window.localStorage.setItem(UI_THEME_KEY, state.theme);
    } catch {
      // 忽略儲存失敗（例如隱私模式）
    }
    applyUiTheme(state.theme);
  }, [state, hydrated]);

  return {
    ...state,
    hydrated,
    setEnabled: (enabled: boolean) => setState((s) => ({ ...s, enabled })),
    setSharkCount: (sharkCount: number) =>
      setState((s) => ({ ...s, sharkCount: clampCount(sharkCount) })),
    setTheme: (theme: UiTheme) => setState((s) => ({ ...s, theme })),
  };
}
