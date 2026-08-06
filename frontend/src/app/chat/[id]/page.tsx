"use client";

import Link from "next/link";
import { use, useEffect, useRef, useState } from "react";
import { ProgressTrail } from "@/components/ProgressTrail";
import { ShimmerAnswer } from "@/components/Shimmer";
import { useProgressSocket } from "@/hooks/useProgressSocket";
import { askQuestion, newChannelId } from "@/lib/api";
import { appendMessage, getChat, type Chat, type Message } from "@/lib/chats";

export default function ChatPage({ params }: PageProps<"/chat/[id]">) {
  const { id } = use(params);
  const { event, open, close, reset } = useProgressSocket();

  const [chat, setChat] = useState<Chat | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const found = getChat(id);
    setChat(found ?? null);
    setMessages(found?.messages ?? []);
    setLoaded(true);
  }, [id]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);

  async function send(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || busy) return;

    const userMessage: Message = { role: "user", content: trimmed };
    setMessages((m) => [...m, userMessage]);
    appendMessage(id, userMessage);
    setQuestion("");
    setError(null);
    setBusy(true);
    reset();

    const channel = newChannelId();
    await open(channel);

    try {
      const result = await askQuestion(id, trimmed, channel);
      const reply: Message = {
        role: "assistant",
        content: result.answer,
        refused: result.refused,
        sources: result.sources,
      };
      setMessages((m) => [...m, reply]);
      appendMessage(id, reply);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setBusy(false);
      close();
    }
  }

  if (loaded && !chat) {
    return (
      <div className="flex h-full items-center justify-center px-8">
        <div className="max-w-[38ch] text-center">
          <h2 className="font-display text-[28px] text-ink-900">
            Chat not found
          </h2>
          <p className="mt-3 text-[14px] leading-relaxed text-ink-500">
            This chat isn&apos;t stored in this browser. Upload the document
            again to start a new one.
          </p>
          <Link
            href="/"
            className="mt-6 inline-block border-b border-accent pb-0.5 text-[13px] text-accent hover:opacity-70"
          >
            New upload
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      <header className="shrink-0 border-b border-ink-200 px-10 py-5">
        {loaded ? (
          <div className="mx-auto max-w-[640px]">
            <span className="label-caps">Reading</span>
            <h1 className="font-display mt-1.5 truncate text-[21px] leading-tight text-ink-900">
              {chat?.filename}
            </h1>
            <p className="mt-1 font-mono text-[10px] tabular-nums text-ink-400">
              {chat?.chunks} {chat?.chunks === 1 ? "chunk" : "chunks"} indexed
            </p>
          </div>
        ) : (
          <div className="mx-auto max-w-[640px] space-y-2">
            <div className="shimmer h-3 w-16 rounded-sm" />
            <div className="shimmer h-5 w-56 rounded-sm" />
          </div>
        )}
      </header>

      <div className="flex-1 overflow-y-auto px-10 py-10">
        <div className="mx-auto max-w-[640px] space-y-10">
          {loaded && messages.length === 0 && !busy && (
            <p className="font-display py-16 text-center text-[19px] italic text-ink-300">
              Ask anything about this document.
            </p>
          )}

          {messages.map((message, i) => (
            <MessageBlock key={i} message={message} />
          ))}

          {busy && (
            <div className="fade-rise space-y-6">
              <ProgressTrail event={event} variant="query" />
              <ShimmerAnswer />
            </div>
          )}

          {error && (
            <p className="fade-rise border-l-2 border-danger bg-danger-bg py-3 pl-4 pr-4 text-[13px] leading-relaxed text-danger">
              {error}
            </p>
          )}

          <div ref={bottomRef} />
        </div>
      </div>

      <div className="shrink-0 border-t border-ink-200 px-10 py-5">
        <form onSubmit={send} className="mx-auto flex max-w-[640px] items-center gap-4">
          <input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask a question…"
            disabled={busy}
            className="flex-1 border-b border-ink-200 bg-transparent pb-2 text-[15px] outline-none transition-colors placeholder:text-ink-300 focus:border-accent disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={busy || !question.trim()}
            className="shrink-0 text-[13px] tracking-wide text-accent transition-opacity hover:opacity-70 disabled:cursor-not-allowed disabled:text-ink-300"
          >
            Ask →
          </button>
        </form>
      </div>
    </div>
  );
}

function MessageBlock({ message }: { message: Message }) {
  // Questions read as a marginal note; answers as the body text.
  if (message.role === "user") {
    return (
      <div className="fade-rise border-l-2 border-ink-300 pl-4">
        <span className="label-caps">Question</span>
        <p className="mt-1 text-[15px] leading-relaxed text-ink-700">
          {message.content}
        </p>
      </div>
    );
  }

  // A refusal is not an answer, so it is set quieter and carries no citations.
  if (message.refused) {
    return (
      <div className="fade-rise">
        <p className="prose-answer italic text-ink-400">{message.content}</p>
        <p className="mt-2 text-[12px] leading-relaxed text-ink-400">
          Nothing in this document covers that.
        </p>
      </div>
    );
  }

  return (
    <div className="fade-rise">
      <p className="prose-answer whitespace-pre-wrap">{message.content}</p>

      {message.sources && message.sources.length > 0 && (
        <div className="mt-6 border-t border-ink-200 pt-4">
          <span className="label-caps">
            {message.sources.length} Source
            {message.sources.length === 1 ? "" : "s"}
          </span>
          <ul className="mt-2.5 space-y-1.5">
            {message.sources.map((source) => (
              <li
                key={source.chunk_id}
                className="flex items-baseline gap-2.5 text-[12px] leading-relaxed text-ink-500"
              >
                <span className="font-mono text-[10px] tabular-nums text-accent">
                  {String(source.n).padStart(2, "0")}
                </span>
                <span>{source.section}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
