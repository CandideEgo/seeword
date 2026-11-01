"use client";

/**
 * A module-level, page-lifetime shared request.
 *
 * Several home-page surfaces ask the same endpoint at nearly the same time
 * (the resume strip and the layout gate, the right rail and the channel rail).
 * The API client already collapses *concurrent* identical GETs, but a
 * component that mounts after the first response would issue a second request.
 * This helper keeps the promise until the page is really left, so one page view
 * costs one request.
 *
 * Lifecycle mirrors the editorial loader in `app/(main)/page.tsx`:
 * - `get()` returns the in-flight/settled promise and cancels a pending release;
 * - `release()` (called from an effect cleanup) aborts and forgets the request
 *   on the next tick, so React StrictMode's mount → cleanup → mount does not
 *   cancel a request the second mount is about to consume;
 * - a rejection clears the cache so a retry actually retries.
 *
 * On the server there is no shared state: each call starts its own request.
 */
export interface SharedRequest<T> {
  get: () => Promise<T>;
  release: () => void;
  reset: () => void;
}

export function createSharedRequest<T>(
  load: (signal: AbortSignal) => Promise<T>
): SharedRequest<T> {
  let promise: Promise<T> | null = null;
  let controller: AbortController | null = null;
  let releaseTimer: number | null = null;

  const clearTimer = () => {
    if (releaseTimer !== null) {
      window.clearTimeout(releaseTimer);
      releaseTimer = null;
    }
  };

  const reset = () => {
    if (typeof window === "undefined") return;
    clearTimer();
    controller?.abort();
    controller = null;
    promise = null;
  };

  const get = (): Promise<T> => {
    if (typeof window === "undefined") {
      return load(new AbortController().signal);
    }
    clearTimer();
    if (!promise) {
      const current = new AbortController();
      controller = current;
      const request = load(current.signal).catch((error: unknown) => {
        // A failed request must not be replayed from the module cache forever.
        if (promise === request) {
          promise = null;
          controller = null;
        }
        throw error;
      });
      promise = request;
    }
    return promise;
  };

  const release = () => {
    if (typeof window === "undefined") return;
    clearTimer();
    releaseTimer = window.setTimeout(() => {
      releaseTimer = null;
      controller?.abort();
      controller = null;
      promise = null;
    }, 0);
  };

  return { get, release, reset };
}
