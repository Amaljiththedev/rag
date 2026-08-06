"use client";

import { useRouter } from "next/navigation";
import { useRef, useState } from "react";
import { IndexingProgress } from "@/components/IndexingProgress";
import { useProgressSocket } from "@/hooks/useProgressSocket";
import { newChannelId, uploadFile, type UploadResult } from "@/lib/api";
import { notifyWorkspacesChanged } from "@/lib/useWorkspaces";

const ACCEPTED = [".pdf", ".txt"];

export default function CreateWorkspacePage() {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const { event, open, close, reset } = useProgressSocket();

  const [busy, setBusy] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState<{ name: string; size: number } | null>(null);
  const [result, setResult] = useState<UploadResult | null>(null);

  async function handleFile(file: File) {
    const ext = file.name.slice(file.name.lastIndexOf(".")).toLowerCase();
    if (!ACCEPTED.includes(ext)) {
      setError(`Unsupported file type. Atlas indexes ${ACCEPTED.join(" and ")} documents.`);
      return;
    }

    setError(null);
    setResult(null);
    setPending({ name: file.name, size: file.size });
    setBusy(true);
    reset();

    const channel = newChannelId();
    // Connect before uploading, or the first stages fire unheard.
    await open(channel);

    try {
      const uploaded = await uploadFile(file, channel);
      setResult(uploaded);
      notifyWorkspacesChanged();
      router.push(`/workspace/${uploaded.document_set_id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Indexing failed.");
      setBusy(false);
    } finally {
      close();
    }
  }

  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto max-w-[680px] px-10 py-16">
        <span className="eyebrow">New Workspace</span>
        <h1 className="mt-3 text-[32px] font-semibold leading-[1.15] tracking-[-0.02em]">
          Create Workspace
        </h1>
        <p className="mt-3 max-w-[54ch] text-[15px] leading-relaxed text-muted">
          Atlas indexes the documents you provide and answers strictly from their
          contents, citing the section and page each fact came from.
        </p>

        <div
          onDragOver={(e) => {
            e.preventDefault();
            if (!busy) setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragging(false);
            if (busy) return;
            const file = e.dataTransfer.files?.[0];
            if (file) handleFile(file);
          }}
          className={[
            "t150 mt-10 rounded-lg border border-dashed px-8 py-14 text-center",
            dragging ? "border-ink bg-hover" : "border-line bg-surface",
            busy ? "opacity-60" : "",
          ].join(" ")}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.txt"
            className="hidden"
            disabled={busy}
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) handleFile(file);
              e.target.value = "";
            }}
          />

          <p className="text-[15px] font-medium">Drop documents</p>
          <p className="meta mt-2">or</p>

          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            disabled={busy}
            className="t150 mt-3 rounded-sm border border-line bg-surface px-3.5 py-1.5 text-[13.5px] hover:bg-hover disabled:cursor-not-allowed disabled:opacity-50"
          >
            Browse Files
          </button>

          <p className="meta mt-6">PDF, TXT · up to 50 MB</p>
        </div>

        {(busy || result) && pending && (
          <section className="mt-8 rounded-lg border border-line bg-surface">
            <header className="flex items-baseline justify-between gap-4 border-b border-line-soft px-5 py-3">
              <span className="truncate text-[13.5px] font-medium">{pending.name}</span>
              <span className="meta shrink-0">
                {(pending.size / 1024).toFixed(0)} KB
                {result ? ` · ${result.page_count} pages · ${result.chunks_created} passages` : ""}
              </span>
            </header>
            <div className="px-5 py-4">
              <IndexingProgress event={event} variant="indexing" />
            </div>
          </section>
        )}

        {error && (
          <p className="enter mt-8 rounded-md border border-line bg-surface px-4 py-3 text-[13.5px] leading-relaxed text-critical">
            {error}
          </p>
        )}

        <p className="meta mt-12 leading-relaxed">
          Scanned or image-only PDFs are not yet supported — they require OCR.
          Provide a digital PDF with a text layer.
        </p>
      </div>
    </div>
  );
}
