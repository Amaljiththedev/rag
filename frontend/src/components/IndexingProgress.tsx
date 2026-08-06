"use client";

import type { ProgressEvent } from "@/lib/api";

/** Backend stage keys mapped to the labels the product uses. */
const INDEXING = [
  { key: "uploaded", label: "Uploading" },
  { key: "reading", label: "Reading document" },
  { key: "chunking", label: "Finding sections" },
  { key: "embedding", label: "Generating embeddings" },
  { key: "storing", label: "Indexing" },
  { key: "done", label: "Ready" },
];

const RESPONDING = [
  { key: "retrieving", label: "Finding evidence" },
  { key: "ranking", label: "Ranking passages" },
  { key: "generating", label: "Preparing response" },
];

export function IndexingProgress({
  event,
  variant = "indexing",
}: {
  event: ProgressEvent | null;
  variant?: "indexing" | "responding";
}) {
  const stages = variant === "indexing" ? INDEXING : RESPONDING;
  const failed = event?.stage === "error";
  const activeIndex = event ? stages.findIndex((s) => s.key === event.stage) : -1;

  if (failed) {
    return (
      <p className="enter text-[13.5px] leading-relaxed text-critical">
        {event?.message}
      </p>
    );
  }

  return (
    <div className="enter space-y-2.5">
      {stages.map((stage, i) => {
        const done = activeIndex > i;
        const active = activeIndex === i;
        const pending = activeIndex < i;

        // Only the embedding stage reports a real percentage; every other
        // stage is binary, so it fills completely or not at all.
        const pct =
          done ? 100
          : !active ? 0
          : typeof event?.percent === "number" ? event.percent
          : 45;

        return (
          <div key={stage.key} className="grid grid-cols-[152px_1fr_auto] items-center gap-3">
            <span
              className={[
                "meta t150",
                active ? "text-ink" : "",
                done ? "text-muted" : "",
                pending ? "text-muted/50" : "",
              ].join(" ")}
            >
              {stage.label}
            </span>

            <div className="bar-track">
              <div className="bar-fill" style={{ width: `${pct}%` }} />
            </div>

            <span className="meta w-9 text-right">
              {done ? "done" : active ? `${Math.round(pct)}%` : ""}
            </span>
          </div>
        );
      })}

      {event?.message && (
        <p className="meta pt-1" role="status" aria-live="polite">
          {event.message}
        </p>
      )}
    </div>
  );
}
