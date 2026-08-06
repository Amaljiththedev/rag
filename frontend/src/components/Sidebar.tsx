"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useWorkspaces } from "@/lib/useWorkspaces";

export function Sidebar() {
  const pathname = usePathname();
  const { workspaces, loading, error } = useWorkspaces();

  return (
    <aside className="flex h-screen w-[264px] shrink-0 flex-col border-r border-line bg-canvas">
      <div className="px-5 pt-6 pb-5">
        <Link href="/" className="t150 text-[15px] font-semibold tracking-[-0.01em] hover:opacity-70">
          Atlas
        </Link>
      </div>

      <div className="mx-5 border-t border-line" />

      <div className="px-5 pt-5 pb-2">
        <span className="eyebrow">Documents</span>
      </div>

      <nav className="flex-1 overflow-y-auto px-2.5 pb-3">
        {loading && (
          <div className="space-y-1.5 px-2.5 py-1">
            <div className="line-ghost h-8 w-full" />
            <div className="line-ghost h-8 w-full" />
          </div>
        )}

        {!loading && error && (
          <p className="px-2.5 py-2 text-[13px] leading-relaxed text-critical">
            {error}
          </p>
        )}

        {!loading && !error && workspaces.length === 0 && (
          <p className="px-2.5 py-2 text-[13px] leading-relaxed text-muted">
            No documents indexed.
          </p>
        )}

        <ul className="space-y-px">
          {workspaces.map((ws) => {
            const href = `/workspace/${ws.document_set_id}`;
            const active = pathname === href;
            return (
              <li key={ws.document_set_id}>
                <Link
                  href={href}
                  title={ws.filename}
                  className={[
                    "t150 block rounded-sm px-2.5 py-2",
                    active ? "bg-hover" : "hover:bg-hover",
                  ].join(" ")}
                >
                  <span
                    className={[
                      "block truncate text-[13.5px] leading-snug",
                      active ? "font-medium text-ink" : "text-ink/85",
                    ].join(" ")}
                  >
                    {ws.filename}
                  </span>
                  <span className="meta mt-0.5 block">
                    {ws.page_count ?? 0} {ws.page_count === 1 ? "page" : "pages"}
                    {" · "}
                    {ws.chunk_count ?? 0} passages
                  </span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="mx-5 border-t border-line" />

      <div className="space-y-px p-2.5">
        <Link
          href="/"
          className={[
            "t150 flex items-center gap-2.5 rounded-sm px-2.5 py-2 text-[13.5px]",
            pathname === "/" ? "bg-hover font-medium" : "hover:bg-hover",
          ].join(" ")}
        >
          <PlusGlyph />
          New Workspace
        </Link>
        <Link
          href="/settings"
          className={[
            "t150 flex items-center gap-2.5 rounded-sm px-2.5 py-2 text-[13.5px]",
            pathname === "/settings" ? "bg-hover font-medium" : "hover:bg-hover",
          ].join(" ")}
        >
          <GearGlyph />
          Settings
        </Link>
      </div>
    </aside>
  );
}

function PlusGlyph() {
  return (
    <svg width="13" height="13" viewBox="0 0 14 14" fill="none" aria-hidden="true">
      <path d="M7 2.8v8.4M2.8 7h8.4" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
    </svg>
  );
}

function GearGlyph() {
  return (
    <svg width="13" height="13" viewBox="0 0 14 14" fill="none" aria-hidden="true">
      <circle cx="7" cy="7" r="2.1" stroke="currentColor" strokeWidth="1.2" />
      <path
        d="M7 1.6v1.3M7 11.1v1.3M12.4 7h-1.3M2.9 7H1.6M10.8 3.2l-.9.9M4.1 9.9l-.9.9M10.8 10.8l-.9-.9M4.1 4.1l-.9-.9"
        stroke="currentColor"
        strokeWidth="1.2"
        strokeLinecap="round"
      />
    </svg>
  );
}
