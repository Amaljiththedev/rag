"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { WS_BASE, type ProgressEvent } from "@/lib/api";

/**
 * Opens a progress WebSocket and returns the latest stage event.
 *
 * The socket must be connected *before* the HTTP request starts, otherwise the
 * first stages fire with nobody listening — so `open()` resolves only once the
 * connection is actually established.
 */
export function useProgressSocket() {
  const socketRef = useRef<WebSocket | null>(null);
  const [event, setEvent] = useState<ProgressEvent | null>(null);

  const open = useCallback((channel: string): Promise<void> => {
    return new Promise((resolve) => {
      try {
        const ws = new WebSocket(`${WS_BASE}/ws/progress/${channel}`);
        socketRef.current = ws;

        ws.onmessage = (raw) => {
          try {
            setEvent(JSON.parse(raw.data) as ProgressEvent);
          } catch {
            // ignore malformed frames
          }
        };
        ws.onopen = () => resolve();
        // Progress is a nicety — if the socket fails, let the request proceed.
        ws.onerror = () => resolve();
      } catch {
        resolve();
      }
    });
  }, []);

  const close = useCallback(() => {
    socketRef.current?.close();
    socketRef.current = null;
  }, []);

  const reset = useCallback(() => setEvent(null), []);

  useEffect(() => () => socketRef.current?.close(), []);

  return { event, open, close, reset };
}
