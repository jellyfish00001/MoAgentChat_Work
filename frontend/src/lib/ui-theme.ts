/**
 * Wistron UI themes — 唯一主題入口。
 * 色票／語意色只改 `globals.css` 的 `[data-theme=…]`；元件用 `bg-panel` 等 class，勿散落 hex。
 */

export type UiTheme = "wistron-dark" | "wistron-light";

export const UI_THEME_KEY = "ai_prepare.ui_theme";
/** 新使用者預設：明亮主題（與 aipark-frontend-ui 約定一致）。 */
export const DEFAULT_UI_THEME: UiTheme = "wistron-light";

export const UI_THEMES: {
  value: UiTheme;
  label: string;
  /** Swatch colors shown in the theme icon (bg + accent) */
  swatch: [string, string];
}[] = [
  {
    value: "wistron-light",
    label: "Light",
    swatch: ["#E8EEF1", "#3D7388"],
  },
  {
    value: "wistron-dark",
    label: "Dark",
    swatch: ["#152A36", "#A7DD6C"],
  },
];

/** Map legacy ocean / classic theme values to Light or Dark. */
export function migrateLegacyTheme(raw: unknown): UiTheme {
  if (raw === "wistron-dark") return "wistron-dark";
  if (raw === "wistron-light") return "wistron-light";
  if (raw === "dark") return "wistron-dark";
  if (raw === "light") return "wistron-light";
  // 舊 classic／wistron → Light（對齊預設）
  if (raw === "wistron-classic" || raw === "wistron") return "wistron-light";
  return DEFAULT_UI_THEME;
}

export function applyUiTheme(theme: UiTheme) {
  if (typeof document === "undefined") return;
  document.documentElement.dataset.theme = theme;
}

export function readStoredUiTheme(): UiTheme {
  if (typeof window === "undefined") return DEFAULT_UI_THEME;
  try {
    const fromTheme = window.localStorage.getItem(UI_THEME_KEY);
    if (fromTheme) return migrateLegacyTheme(fromTheme);
    const oceanRaw = window.localStorage.getItem("ai_prepare.ocean");
    if (oceanRaw) {
      const p = JSON.parse(oceanRaw) as { theme?: unknown };
      if (p.theme != null) return migrateLegacyTheme(p.theme);
    }
  } catch {
    /* ignore */
  }
  return DEFAULT_UI_THEME;
}
