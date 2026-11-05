"use client";

import { useEffect, useState } from "react";

const STORAGE_KEY = "ai_prepare.localUserId";
/** 本機 demo 預設 userId，與 Scheduler API 查詢參數一致。 */
export const LOCAL_DEMO_USER_ID = "local-demo-user";

/**
 * 提供穩定的本機使用者 ID，供排程 API 的 userId 使用；
 * 優先讀 localStorage，不可用時維持記憶體預設值。
 */
export function useLocalUser(): string {
  const [userId, setUserId] = useState(LOCAL_DEMO_USER_ID);

  useEffect(() => {
    try {
      const stored = window.localStorage.getItem(STORAGE_KEY);
      if (stored?.trim()) {
        setUserId(stored.trim());
        return;
      }
      window.localStorage.setItem(STORAGE_KEY, LOCAL_DEMO_USER_ID);
    } catch {
      // 隱私模式等無法存取 localStorage 時沿用 in-memory 預設
    }
  }, []);

  return userId;
}
