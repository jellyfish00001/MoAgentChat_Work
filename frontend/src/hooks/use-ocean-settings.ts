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
  /** 鯊魚數量（0–8） */
  sharkCount: number;
  /** 體型倍率（0.5–2，相對預設） */
  sharkSizeScale: number;
  /** 速度倍率（0.5–1.5，相對預設） */
  sharkSpeedScale: number;
  /** UI + ASCII theme */
  theme: UiTheme;
}

const KEY = "ai_prepare.ocean";
const MIN_SHARKS = 0;
const MAX_SHARKS = 8;
export const MIN_SHARK_SIZE = 0.5;
export const MAX_SHARK_SIZE = 2;
export const MIN_SHARK_SPEED = 0.5;
export const MAX_SHARK_SPEED = 1.5;

const DEFAULTS: OceanSettingsState = {
  enabled: true,
  sharkCount: 1,
  sharkSizeScale: 1,
  sharkSpeedScale: 0.8,
  theme: DEFAULT_UI_THEME,
};

function clampCount(n: number) {
  return Math.max(MIN_SHARKS, Math.min(MAX_SHARKS, Math.round(n)));
}

function clampSize(n: number) {
  return Math.max(MIN_SHARK_SIZE, Math.min(MAX_SHARK_SIZE, Math.round(n * 10) / 10));
}

function clampSpeed(n: number) {
  return Math.max(MIN_SHARK_SPEED, Math.min(MAX_SHARK_SPEED, Math.round(n * 10) / 10));
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
      sharkSizeScale:
        typeof p.sharkSizeScale === "number"
          ? clampSize(p.sharkSizeScale)
          : DEFAULTS.sharkSizeScale,
      sharkSpeedScale:
        typeof p.sharkSpeedScale === "number"
          ? clampSpeed(p.sharkSpeedScale)
          : DEFAULTS.sharkSpeedScale,
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
    setSharkSizeScale: (sharkSizeScale: number) =>
      setState((s) => ({ ...s, sharkSizeScale: clampSize(sharkSizeScale) })),
    setSharkSpeedScale: (sharkSpeedScale: number) =>
      setState((s) => ({ ...s, sharkSpeedScale: clampSpeed(sharkSpeedScale) })),
    setTheme: (theme: UiTheme) => setState((s) => ({ ...s, theme })),
  };
}
