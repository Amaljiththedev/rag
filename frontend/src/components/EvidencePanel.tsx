import type { Evidence } from "@/lib/api";

/**
 * Provenance for an answer. Shows document, section and page — the things a
 * reviewer can actually go and check. Chunk ids stay internal.
 */
export function EvidencePanel({ evidence }: { evidence: Evidence[] }) {
  if (evidence.length === 0) return null;

  return (
    <section className="mt-6 rounded-lg border border-line bg-surface">
      <header className="flex items-baseline justify-between border-b border-line-soft px-4 py-2.5">
        <span className="eyebrow">Evidence</span>
        <span className="meta">
          {evidence.length} {evidence.length === 1 ? "passage" : "passages"}
        </span>
      </header>

      <ul>
        {evidence.map((item, i) => (
          <li
            key={item.chunk_id}
            className={i > 0 ? "border-t border-line-soft" : undefined}
          >
            <div className="flex gap-3.5 px-4 py-3">
              <span className="meta pt-0.5 tabular-nums">
                {String(item.n).padStart(2, "0")}
              </span>

              <div className="min-w-0">
                <p className="truncate text-[13.5px] font-medium leading-snug text-ink">
                  {item.section ?? item.document}
                </p>
                <p className="meta mt-1">
                  {[
                    item.section ? item.document : null,
                    item.page_label,
                  ]
                    .filter(Boolean)
                    .join("  ·  ")}
                </p>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
