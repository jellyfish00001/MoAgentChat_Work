// [ai_prepare 修改] 本機模擬 SSO 權限：有無「財務」可用 Agent

"use client";

import { useCallback, useEffect, useState } from "react";

const KEY = "ai_prepare.localAccess";

export type LocalAccessState = {
  /** 模擬財務部門權限；正式環境改由 SSO／群組決定 */
  hasFinance: boolean;
};

const DEFAULTS: LocalAccessState = {
  hasFinance: false,
};

function load(): LocalAccessState {
  if (typeof window === "undefined") return DEFAULTS;
  try {
    const raw = window.localStorage.getItem(KEY);
    if (!raw) return DEFAULTS;
    const p = JSON.parse(raw) as Partial<LocalAccessState>;
    return {
      hasFinance:
        typeof p.hasFinance === "boolean" ? p.hasFinance : DEFAULTS.hasFinance,
    };
  } catch {
    return DEFAULTS;
  }
}

function save(state: LocalAccessState) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(KEY, JSON.stringify(state));
}

export function useLocalAccess() {
  const [state, setState] = useState<LocalAccessState>(DEFAULTS);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    setState(load());
    setHydrated(true);
  }, []);

  const setHasFinance = useCallback((hasFinance: boolean) => {
    setState((prev) => {
      const next = { ...prev, hasFinance };
      save(next);
      return next;
    });
  }, []);

  const toggleFinance = useCallback(() => {
    setHasFinance(!load().hasFinance);
  }, [setHasFinance]);

  return {
    hasFinance: state.hasFinance,
    hydrated,
    setHasFinance,
    toggleFinance,
  };
}
