import type { Row } from "../types/Row";

export type ProcessRequest = {
  sigmaV0: number;
  rows: Row[];
};

export type ProcessResponse = {
  compressionIdx: number | null;
  recompressionIdx: number | null;
  warnings: string[];
};

function getApiBaseUrl(): string {
  const raw = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "";
  const trimmed = raw.trim();
  const base = trimmed.length > 0 ? trimmed : "http://localhost:8000";
  return base.endsWith("/") ? base.slice(0, -1) : base;
}

export async function processData(request: ProcessRequest): Promise<ProcessResponse> {
  const res = await fetch(`${getApiBaseUrl()}/api/process`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `Request failed with status ${res.status}`);
  }

  return (await res.json()) as ProcessResponse;
}

