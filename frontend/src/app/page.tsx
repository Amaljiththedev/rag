"use client";

import { useRouter } from "next/navigation";
import { useRef, useState } from "react";
import { ProgressTrail } from "@/components/ProgressTrail";
import { useProgressSocket } from "@/hooks/useProgressSocket";
import { newChannelId, uploadFile } from "@/lib/api";
import { createChat } from "@/lib/chats";

const ACCEPTED = [".pdf", ".txt"];

export default function HomePage() {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const { event, open, close, reset } = useProgressSocket();

  const [busy, setBusy] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleFile(file: File) {
    const ext = file.name.slice(file.name.lastIndexOf(".")).toLowerCase();
    if (!ACCEPTED.includes(ext)) {
      setError(`Only ${ACCEPTED.join(" and ")} files are supported.`);
      return;
    }

    setError(null);
    setBusy(true);
    reset();

    const channel = newChannelId();
    // Connect before uploading, or the first stages fire unheard.
    await open(channel);

    try {
      const result = await uploadFile(file, channel);
      createChat({
        documentSetId: result.document_set_id,
        filename: result.filename,
        chunks: result.chunks_created,
      });
      router.push(`/chat/${result.document_set_id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed.");
      setBusy(false);
    } finally {
      close();
    }
  }

  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto max-w-[560px] px-8 py-20">
        <span className="label-caps">Upload</span>

        <h1 className="font-display mt-4 text-[42px] leading-[1.12] text-ink-900">
          Ask your document
          <span className="italic text-accent"> anything.</span>
        </h1>

        <p className="mt-4 max-w-[42ch] text-[15px] leading-relaxed text-ink-500">
          Every answer is drawn from the file you upload and cited back to it.
          Nothing else is consulted.
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
            "mt-11 border px-8 py-12 text-center transition-colors",
            dragging ? "border-accent bg-accent-soft" : "border-ink-200 bg-surface",
            busy ? "opacity-55" : "",
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

          <p className="font-display text-[19px] text-ink-700">
            Drop a file here
          </p>

          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            disabled={busy}
            className="mt-4 border-b border-accent pb-0.5 text-[13px] text-accent transition-opacity hover:opacity-70 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {busy ? "Processing…" : "or choose one"}
          </button>

          <p className="label-caps mt-7">PDF · TXT</p>
        </div>

        {busy && (
          <div className="mt-10 border-t border-ink-200 pt-6">
            <ProgressTrail event={event} variant="upload" />
          </div>
        )}

        {error && (
          <p className="fade-rise mt-8 border-l-2 border-danger bg-danger-bg py-3 pl-4 pr-4 text-[13px] leading-relaxed text-danger">
            {error}
          </p>
        )}

        <p className="mt-14 border-t border-ink-200 pt-5 text-[12px] leading-relaxed text-ink-400">
          Scanned or image-only PDFs cannot be read yet — they would need OCR.
          Use a digital PDF whose text you can select.
        </p>
      </div>
    </div>
  );
}
