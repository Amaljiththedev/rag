"use client";

import Link from "next/link";
import { use, useEffect, useMemo, useRef, useState } from "react";
import { EvidencePanel } from "@/components/EvidencePanel";
import { IndexingProgress } from "@/components/IndexingProgress";
import { useProgressSocket } from "@/hooks/useProgressSocket";
import { askQuestion, deleteWorkspace, newChannelId } from "@/lib/api";
import { appendEntry, getTranscript, type Entry } from "@/lib/transcript";
import { notifyWorkspacesChanged, useWorkspaces } from "@/lib/useWorkspaces";

export default function WorkspacePage({ params }: PageProps<"/workspace/[id]">) {
  const { id } = use(params);
  const { event, open, close, reset } = useProgressSocket();
  const { workspaces, loading } = useWorkspaces();

  const [entries, setEntries] = useState<Entry[]>([]);
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  const workspace = useMemo(
    () => workspaces.find((w) => w.document_set_id === id),
    [workspaces, id],
  );

  useEffect(() => {
    setEntries(getTranscript(id));
  }, [id]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [entries, busy]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || busy) return;

    setQuestion("");
    setError(null);
    setBusy(true);
    reset();

    const channel = newChannelId();
    await open(channel);

    try {
      const res = await askQuestion(id, trimmed, channel);
      const entry: Entry = {
        question: trimmed,
        answer: res.answer,
        refused: res.refused,
        evidence: res.evidence,
        at: Date.now(),
      };
      appendEntry(id, entry);
      setEntries((prev) => [...prev, entry]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "The request could not be completed.");
    } finally {
      setBusy(false);
      close();
    }
  }

  async function remove() {
    await deleteWorkspace(id);
    notifyWorkspacesChanged();
    window.location.href = "/";
  }

  if (!loading && !workspace) {
    return (
      <div className="flex h-full items-center justify-center px-10">
        <div className="max-w-[44ch] text-center">
          <h2 className="text-[22px] font-semibold tracking-[-0.01em]">
            Workspace not found
          </h2>
          <p className="mt-2.5 text-[14px] leading-relaxed text-muted">
            This document is no longer indexed. Create a workspace to begin again.
          </p>
          <Link
            href="/"
            className="t150 mt-6 inline-block rounded-sm border border-line bg-surface px-3.5 py-1.5 text-[13.5px] hover:bg-hover"
          >
            Create Workspace
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      <header className="shrink-0 border-b border-line px-10 py-4">
        <div className="mx-auto flex max-w-[720px] items-start justify-between gap-6">
          <div className="min-w-0">
            <h1 className="truncate text-[15px] font-semibold tracking-[-0.01em]">
              {workspace?.filename ?? " "}
            </h1>
            <p className="meta mt-1">
              {workspace ? (
                <>
                  Indexed · {workspace.page_count ?? 0}{" "}
                  {workspace.page_count === 1 ? "page" : "pages"} ·{" "}
                  {workspace.chunk_count ?? 0} passages
                </>
              ) : (
                " "
              )}
            </p>
          </div>
          <button
            onClick={remove}
            className="t150 shrink-0 rounded-sm border border-line bg-surface px-2.5 py-1 text-[12.5px] text-muted hover:bg-hover hover:text-ink"
          >
            Remove
          </button>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto px-10 py-10">
        <div className="mx-auto max-w-[720px]">
          {entries.length === 0 && !busy && (
            <div className="py-14">
              <p className="text-[15px] leading-relaxed text-ink">
                Upload a document to begin.
              </p>
              <p className="mt-2 max-w-[52ch] text-[15px] leading-relaxed text-muted">
                Atlas indexes its contents and answers using only the information
                you provide.
              </p>
            </div>
          )}

          <div className="space-y-12">
            {entries.map((entry, i) => (
              <ExchangeBlock key={entry.at} entry={entry} index={i + 1} />
            ))}

            {busy && (
              <div className="enter">
                <span className="eyebrow">Response</span>
                <div className="mt-4">
                  <IndexingProgress event={event} variant="responding" />
                </div>
                <div className="mt-6 space-y-2.5">
                  <div className="line-ghost h-3.5 w-[93%]" />
                  <div className="line-ghost h-3.5 w-[87%]" />
                  <div className="line-ghost h-3.5 w-[58%]" />
                </div>
              </div>
            )}
          </div>

          {error && (
            <p className="enter mt-8 rounded-md border border-line bg-surface px-4 py-3 text-[13.5px] leading-relaxed text-critical">
              {error}
            </p>
          )}

          <div ref={endRef} />
        </div>
      </div>

      <div className="shrink-0 border-t border-line px-10 py-4">
        <form onSubmit={submit} className="mx-auto flex max-w-[720px] items-center gap-3">
          <input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask a question about this document"
            disabled={busy}
            className="t150 flex-1 rounded-md border border-line bg-surface px-3.5 py-2.5 text-[14.5px] outline-none placeholder:text-muted focus:border-ink disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={busy || !question.trim()}
            className="t150 shrink-0 rounded-md bg-accent px-4 py-2.5 text-[13.5px] font-medium text-white hover:opacity-85 disabled:cursor-not-allowed disabled:opacity-30"
          >
            Ask
          </button>
        </form>
      </div>
    </div>
  );
}

function ExchangeBlock({ entry, index }: { entry: Entry; index: number }) {
  return (
    <article className="enter">
      <div className="flex items-baseline gap-3">
        <span className="eyebrow">Question</span>
        <span className="meta">{String(index).padStart(2, "0")}</span>
      </div>
      <h2 className="mt-2 text-[22px] font-semibold leading-snug tracking-[-0.015em]">
        {entry.question}
      </h2>

      <div className="mt-5 border-t border-line pt-5">
        {entry.refused ? (
          <>
            <p className="answer-body text-muted">{entry.answer}</p>
            <p className="meta mt-2.5">
              No passage in this document supports an answer.
            </p>
          </>
        ) : (
          <div className="answer-body">{renderAnswer(entry.answer)}</div>
        )}
      </div>

      {!entry.refused && <EvidencePanel evidence={entry.evidence} />}
    </article>
  );
}

// The model returns light markdown and is inconsistent about citation
// brackets — it emits [1] and the fullwidth 【1】 interchangeably.
const TOKEN = /\*\*(.+?)\*\*|[[【](\d{1,2})[\]】]/g;

function renderInline(text: string, keyBase: string) {
  const nodes: React.ReactNode[] = [];
  let last = 0;
  let key = 0;
  let match: RegExpExecArray | null;

  TOKEN.lastIndex = 0;
  while ((match = TOKEN.exec(text)) !== null) {
    if (match.index > last) nodes.push(text.slice(last, match.index));

    if (match[1] !== undefined) {
      nodes.push(
        <strong key={`${keyBase}-b${key++}`} className="font-semibold">
          {match[1]}
        </strong>,
      );
    } else if (match[2] !== undefined) {
      nodes.push(
        <sup
          key={`${keyBase}-c${key++}`}
          className="meta ml-0.5 align-super text-ink"
        >
          {match[2]}
        </sup>,
      );
    }
    last = match.index + match[0].length;
  }
  if (last < text.length) nodes.push(text.slice(last));
  return nodes;
}

function renderAnswer(text: string) {
  return text
    .split(/\n{2,}/)
    .filter((block) => block.trim())
    .map((block, i) => <p key={i}>{renderInline(block.trim(), `p${i}`)}</p>);
}
