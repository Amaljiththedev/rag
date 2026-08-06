"use client";

import type { Source } from "./api";

/**
 * Chat history lives in localStorage — there is no auth or user table yet, so a
 * "session" is just the document_set_id the backend handed back on upload.
 */

const KEY = "rag.chats.v1";

export type Message = {
  role: "user" | "assistant";
  content: string;
  refused?: boolean;
  sources?: Source[];
};

export type Chat = {
  documentSetId: string;
  filename: string;
  chunks: number;
  createdAt: number;
  messages: Message[];
};

function read(): Chat[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as Chat[]) : [];
  } catch {
    return [];
  }
}

function write(chats: Chat[]) {
  window.localStorage.setItem(KEY, JSON.stringify(chats));
  // Same-tab listeners: the native `storage` event only fires cross-tab.
  window.dispatchEvent(new Event("rag:chats-changed"));
}

export function listChats(): Chat[] {
  return read().sort((a, b) => b.createdAt - a.createdAt);
}

export function getChat(documentSetId: string): Chat | undefined {
  return read().find((c) => c.documentSetId === documentSetId);
}

export function createChat(chat: Omit<Chat, "messages" | "createdAt">): Chat {
  const chats = read();
  const existing = chats.find((c) => c.documentSetId === chat.documentSetId);
  if (existing) return existing;

  const created: Chat = { ...chat, createdAt: Date.now(), messages: [] };
  write([created, ...chats]);
  return created;
}

export function appendMessage(documentSetId: string, message: Message) {
  const chats = read();
  const chat = chats.find((c) => c.documentSetId === documentSetId);
  if (!chat) return;
  chat.messages.push(message);
  write(chats);
}

export function deleteChat(documentSetId: string) {
  write(read().filter((c) => c.documentSetId !== documentSetId));
}

export function subscribe(onChange: () => void): () => void {
  window.addEventListener("rag:chats-changed", onChange);
  window.addEventListener("storage", onChange);
  return () => {
    window.removeEventListener("rag:chats-changed", onChange);
    window.removeEventListener("storage", onChange);
  };
}
