"use client";

import type { ProgressEvent } from "@/lib/api";

const UPLOAD_STAGES = [
  { key: "uploaded", label: "Received" },
  { key: "reading", label: "Reading" },
  { key: "chunking", label: "Chunking" },
  { key: "embedding", label: "Embedding" },
  { key: "storing", label: "Indexing" },
  { key: "done", label: "Ready" },
];

const QUERY_STAGES = [
  { key: "retrieving", label: "Searching" },
  { key: "generating", label: "Composing" },
  { key: "done", label: "Done" },
];

/**
 * The live pipeline position, set as a numbered running head rather than a
 * progress widget — done stages stay legible, the current one is inked amber.
 */
export function ProgressTrail({
  event,
  variant = "upload",
}: {
  event: ProgressEvent | null;
  variant?: "upload" | "query";
}) {
  const stages = variant === "upload" ? UPLOAD_STAGES : QUERY_STAGES;
  const activeIndex = event ? stages.findIndex((s) => s.key === event.stage) : -1;
  const failed = event?.stage === "error";

  return (
    <div className="fade-rise">
      <ol className="flex flex-wrap items-baseline gap-x-5 gap-y-1.5">
        {stages.map((stage, i) => {
          const done = activeIndex > i;
          const active = activeIndex === i && !failed;
          return (
            <li key={stage.key} className="flex items-baseline gap-1.5">
              <span
                className={[
                  "font-mono text-[10px] tabular-nums",
                  active ? "text-accent" : done ? "text-ink-400" : "text-ink-300",
                ].join(" ")}
              >
                {String(i + 1).padStart(2, "0")}
              </span>
              <span
                className={[
                  "text-[12px] tracking-wide transition-colors",
                  active ? "text-accent stage-pulse" : "",
                  done ? "text-ink-500" : "",
                  !active && !done ? "text-ink-300" : "",
                ].join(" ")}
              >
                {stage.label}
              </span>
            </li>
          );
        })}
      </ol>

      {typeof event?.percent === "number" && !failed && (
        <div className="mt-3 h-px w-full bg-ink-200">
          <div
            className="h-px bg-accent transition-[width] duration-300"
            style={{ width: `${event.percent}%` }}
          />
        </div>
      )}

      {event && (
        <p
          className={[
            "mt-3 text-[13px]",
            failed ? "text-danger" : "text-ink-500",
          ].join(" ")}
          role="status"
          aria-live="polite"
        >
          {event.message}
        </p>
      )}
    </div>
  );
}
