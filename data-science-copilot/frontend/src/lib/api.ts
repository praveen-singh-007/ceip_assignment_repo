import type {
  AskResponse,
  DatasetLoadResponse,
  HealthResponse,
  SampleDatasetInfo,
} from "./types";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function parseErrorDetail(res: Response): Promise<string> {
  try {
    const body = await res.json();
    if (typeof body?.detail === "string") return body.detail;
  } catch {
    // response wasn't JSON; fall through to the generic message below
  }
  return `Request failed with status ${res.status}`;
}

export async function getHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE_URL}/api/health`);
  if (!res.ok) throw new Error(await parseErrorDetail(res));
  return res.json();
}

export async function listSamples(): Promise<SampleDatasetInfo[]> {
  const res = await fetch(`${API_BASE_URL}/api/datasets/samples`);
  if (!res.ok) throw new Error(await parseErrorDetail(res));
  return res.json();
}

export async function loadSample(key: string): Promise<DatasetLoadResponse> {
  const res = await fetch(`${API_BASE_URL}/api/datasets/samples/${key}/load`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(await parseErrorDetail(res));
  return res.json();
}

export async function uploadDataset(file: File): Promise<DatasetLoadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE_URL}/api/datasets/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error(await parseErrorDetail(res));
  return res.json();
}

export async function askQuestion(
  sessionId: string,
  question: string
): Promise<AskResponse> {
  const res = await fetch(`${API_BASE_URL}/api/analysis/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, question }),
  });
  if (!res.ok) throw new Error(await parseErrorDetail(res));
  return res.json();
}

export function resolveFileUrl(path: string | null | undefined): string | null {
  if (!path) return null;
  return `${API_BASE_URL}${path}`;
}
