"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { deleteChat, listChats, subscribe, type Chat } from "@/lib/chats";

export function Sidebar() {
  const pathname = usePathname();
  const [chats, setChats] = useState<Chat[]>([]);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const refresh = () => setChats(listChats());
    refresh();
    setReady(true);
    return subscribe(refresh);
  }, []);

  return (
    <aside className="flex h-screen w-[248px] shrink-0 flex-col border-r border-ink-200 bg-surface">
      <div className="px-6 pt-7 pb-6">
        <Link href="/" className="block">
          <span className="font-display text-[22px] leading-none text-ink-900">
            Document
          </span>
          <span className="font-display text-[22px] leading-none italic text-accent">
            {" "}
            Chat
          </span>
        </Link>
      </div>

      <div className="px-6">
        <Link
          href="/"
          className={[
            "flex items-center justify-between border-t border-ink-200 py-2.5 text-[13px] transition-colors",
            pathname === "/"
              ? "text-accent"
              : "text-ink-600 hover:text-ink-900",
          ].join(" ")}
        >
          New upload
          <span className="text-base leading-none">+</span>
        </Link>
      </div>

      <div className="mt-7 px-6 pb-3">
        <span className="label-caps">Documents</span>
      </div>

      <nav className="flex-1 overflow-y-auto px-6 pb-4">
        {!ready && (
          <div className="space-y-2">
            <div className="shimmer h-4 w-full rounded-sm" />
            <div className="shimmer h-4 w-4/5 rounded-sm" />
          </div>
        )}

        {ready && chats.length === 0 && (
          <p className="text-[13px] leading-relaxed text-ink-400">
            Nothing here yet. Upload a document to begin.
          </p>
        )}

        <ul>
          {chats.map((chat, i) => {
            const href = `/chat/${chat.documentSetId}`;
            const active = pathname === href;
            return (
              <li key={chat.documentSetId} className="group relative">
                <Link
                  href={href}
                  title={chat.filename}
                  className={[
                    "flex items-baseline gap-2.5 border-t border-ink-200 py-2.5 pr-6 transition-colors",
                    active ? "text-accent" : "text-ink-700 hover:text-ink-900",
                  ].join(" ")}
                >
                  <span className="font-mono text-[10px] tabular-nums text-ink-400">
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  <span className="truncate text-[13px] leading-snug">
                    {chat.filename}
                  </span>
                </Link>
                <button
                  onClick={() => deleteChat(chat.documentSetId)}
                  aria-label={`Remove ${chat.filename} from list`}
                  className="absolute right-0 top-1/2 hidden -translate-y-1/2 px-1 text-[15px] leading-none text-ink-300 hover:text-danger group-hover:block"
                >
                  ×
                </button>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="border-t border-ink-200 px-6 py-4">
        <p className="text-[11px] leading-relaxed text-ink-400">
          Chats live in this browser only. Removing one here does not delete its
          indexed text.
        </p>
      </div>
    </aside>
  );
}
