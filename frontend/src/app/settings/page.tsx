"use client";

import { API_BASE } from "@/lib/api";
import { useWorkspaces } from "@/lib/useWorkspaces";

export default function SettingsPage() {
  const { workspaces } = useWorkspaces();

  const totalPages = workspaces.reduce((n, w) => n + (w.page_count ?? 0), 0);
  const totalPassages = workspaces.reduce((n, w) => n + (w.chunk_count ?? 0), 0);

  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto max-w-[680px] px-10 py-16">
        <span className="eyebrow">Configuration</span>
        <h1 className="mt-3 text-[28px] font-semibold leading-tight tracking-[-0.02em]">
          Settings
        </h1>

        <section className="mt-10 rounded-lg border border-line bg-surface">
          <header className="border-b border-line-soft px-5 py-3">
            <span className="eyebrow">Index</span>
          </header>
          <dl className="divide-y divide-line-soft">
            <Row label="Documents" value={String(workspaces.length)} />
            <Row label="Pages indexed" value={String(totalPages)} />
            <Row label="Passages" value={String(totalPassages)} />
          </dl>
        </section>

        <section className="mt-6 rounded-lg border border-line bg-surface">
          <header className="border-b border-line-soft px-5 py-3">
            <span className="eyebrow">Retrieval</span>
          </header>
          <dl className="divide-y divide-line-soft">
            <Row label="Strategy" value="Hybrid · dense + keyword, RRF fused" />
            <Row label="Embedding model" value="all-MiniLM-L6-v2 · 384d" />
            <Row label="Vector store" value="PostgreSQL · pgvector" />
            <Row label="Grounding" value="Refuses when evidence is absent" />
          </dl>
        </section>

        <section className="mt-6 rounded-lg border border-line bg-surface">
          <header className="border-b border-line-soft px-5 py-3">
            <span className="eyebrow">Connection</span>
          </header>
          <dl className="divide-y divide-line-soft">
            <Row label="API endpoint" value={API_BASE} mono />
          </dl>
        </section>
      </div>
    </div>
  );
}

function Row({
  label,
  value,
  mono = false,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="flex items-baseline justify-between gap-6 px-5 py-3">
      <dt className="text-[13.5px] text-muted">{label}</dt>
      <dd className={mono ? "meta text-ink" : "text-[13.5px] text-ink"}>{value}</dd>
    </div>
  );
}
