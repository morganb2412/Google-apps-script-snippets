import type { ProjectContext } from "../types/project";

const PROJECT_PATTERNS = [
  /^\/home\/projects\/([a-zA-Z0-9_-]+)(?:\/|$)/,
  /^\/d\/([a-zA-Z0-9_-]+)(?:\/|$)/,
];

export function extractScriptId(url: URL): string | null {
  if (url.hostname !== "script.google.com") return null;
  for (const pattern of PROJECT_PATTERNS) {
    const match = url.pathname.match(pattern);
    if (match?.[1]) return match[1];
  }
  return null;
}

export function normalizeProjectName(title: string): string | null {
  const name = title
    .replace(/\s*[–—-]\s*Google Apps Script\s*$/i, "")
    .replace(/^Google Apps Script\s*[–—-]\s*/i, "")
    .trim();
  return name && name.toLowerCase() !== "google apps script" ? name : null;
}

export function detectProjectContext(urlValue: string, title: string): ProjectContext | null {
  const url = new URL(urlValue);
  const scriptId = extractScriptId(url);
  if (!scriptId) return null;
  return {
    scriptId,
    name: normalizeProjectName(title),
    editorUrl: `${url.origin}${url.pathname}`,
    detectedAt: new Date().toISOString(),
  };
}
