export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export const WS_BASE =
  process.env.NEXT_PUBLIC_WS_BASE_URL ?? API_BASE.replace(/^http/, "ws");

export type Source = {
  n: number;
  chunk_id: string;
  section: string;
};

export type UploadResult = {
  document_set_id: string;
  filename: string;
  chunks_created: number;
};

export type QueryResult = {
  question: string;
  answer: string;
  refused: boolean;
  sources: Source[];
};

export type ProgressEvent = {
  stage: string;
  message: string;
  percent?: number;
  current?: number;
  total_chunks?: number;
};

export function newChannelId(): string {
  return crypto.randomUUID();
}

async function readError(res: Response, fallback: string): Promise<string> {
  try {
    const body = await res.json();
    if (typeof body?.detail === "string") return body.detail;
    if (Array.isArray(body?.detail)) {
      return body.detail.map((d: { msg?: string }) => d.msg ?? "").join(", ") || fallback;
    }
  } catch {
    // response wasn't JSON
  }
  return fallback;
}

export async function uploadFile(
  file: File,
  channel: string,
): Promise<UploadResult> {
  const form = new FormData();
  form.append("file", file);
  form.append("channel", channel);

  const res = await fetch(`${API_BASE}/upload`, {
    method: "POST",
    body: form,
  });

  if (!res.ok) {
    throw new Error(await readError(res, `Upload failed (${res.status})`));
  }
  return res.json();
}

export async function askQuestion(
  documentSetId: string,
  question: string,
  channel: string,
): Promise<QueryResult> {
  const res = await fetch(`${API_BASE}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      document_set_id: documentSetId,
      question,
      channel,
    }),
  });

  if (!res.ok) {
    throw new Error(await readError(res, `Query failed (${res.status})`));
  }
  return res.json();
}
