"use client";

import { useCallback, useEffect, useState } from "react";
import { listWorkspaces, type Workspace } from "./api";

/**
 * The document list is server truth. A window event lets the upload flow tell
 * every mounted consumer to refetch without a shared store.
 */
const CHANGED = "atlas:workspaces-changed";

export function notifyWorkspacesChanged() {
  window.dispatchEvent(new Event(CHANGED));
}

export function useWorkspaces() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setWorkspaces(await listWorkspaces());
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not reach the index.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    window.addEventListener(CHANGED, refresh);
    return () => window.removeEventListener(CHANGED, refresh);
  }, [refresh]);

  return { workspaces, loading, error, refresh };
}
