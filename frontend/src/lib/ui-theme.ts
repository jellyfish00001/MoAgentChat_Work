/** Wistron UI themes — driven by CSS semantic tokens on `html[data-theme]`. */

export type UiTheme = "wistron-dark" | "wistron-light";

export const UI_THEME_KEY = "ai_prepare.ui_theme";
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
    swatch: ["#0B1921", "#A7DD6C"],
  },
];

/** Map legacy ocean / classic theme values to Light or Dark. */
export function migrateLegacyTheme(raw: unknown): UiTheme {
  if (raw === "wistron-dark") return "wistron-dark";
  if (raw === "wistron-light") return "wistron-light";
  if (raw === "dark") return "wistron-dark";
  if (raw === "light") return "wistron-light";
  // Former classic / wistron → light (new default)
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
