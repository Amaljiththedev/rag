"use client";

import type { Evidence } from "./api";

/**
 * The document list is server state (GET /workspaces). Only the question and
 * answer transcript lives in the browser, keyed by document_set_id.
 */

const KEY = "atlas.transcripts.v1";

export type Entry = {
  question: string;
  answer: string;
  refused: boolean;
  evidence: Evidence[];
  at: number;
};

type Store = Record<string, Entry[]>;

function read(): Store {
  if (typeof window === "undefined") return {};
  try {
    const raw = window.localStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as Store) : {};
  } catch {
    return {};
  }
}

function write(store: Store) {
  window.localStorage.setItem(KEY, JSON.stringify(store));
}

export function getTranscript(documentSetId: string): Entry[] {
  return read()[documentSetId] ?? [];
}

export function appendEntry(documentSetId: string, entry: Entry) {
  const store = read();
  store[documentSetId] = [...(store[documentSetId] ?? []), entry];
  write(store);
}

export function clearTranscript(documentSetId: string) {
  const store = read();
  delete store[documentSetId];
  write(store);
}
