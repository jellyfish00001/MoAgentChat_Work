// [ai_prepare 修改] 支援相對路徑（例如 /api）：自動補上目前網頁的網址
// 這樣 NEXT_PUBLIC_API_URL 在 build 時填 /api 就好，QAS 和 PRD 可以用同一個 image
export function resolveApiUrl(queryApiUrl: string, envApiUrl?: string): string {
  const url = envApiUrl || queryApiUrl;
  if (url?.startsWith("/") && typeof window !== "undefined") {
    return `${window.location.origin}${url}`;
  }
  return url;
}
