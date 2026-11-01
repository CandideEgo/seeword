import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { createSharedRequest } from "@/lib/sharedRequest";

/** Flush the next macrotask (release() resets on a 0ms timer). */
const flushTimer = () => new Promise((resolve) => setTimeout(resolve, 0));

describe("createSharedRequest", () => {
  beforeEach(() => {
    // The module reads `window` at call time; a minimal stub is enough for the
    // timer lifecycle it uses (setTimeout / clearTimeout).
    vi.stubGlobal("window", {
      setTimeout: (fn: () => void, ms?: number) => setTimeout(fn, ms) as unknown as number,
      clearTimeout: (id: number) => clearTimeout(id as unknown as NodeJS.Timeout),
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shares one in-flight load between consumers", async () => {
    const load = vi.fn(async () => "value");
    const request = createSharedRequest(load);

    const [a, b] = await Promise.all([request.get(), request.get()]);

    expect(a).toBe("value");
    expect(b).toBe("value");
    expect(load).toHaveBeenCalledTimes(1);
  });

  it("keeps a settled result until released", async () => {
    const load = vi.fn(async () => "value");
    const request = createSharedRequest(load);

    await request.get();
    await request.get();

    expect(load).toHaveBeenCalledTimes(1);
  });

  it("starts a fresh load after release()", async () => {
    const load = vi.fn(async () => "value");
    const request = createSharedRequest(load);

    await request.get();
    request.release();
    await flushTimer();
    await request.get();

    expect(load).toHaveBeenCalledTimes(2);
  });

  it("retries after a rejection instead of replaying it", async () => {
    const load = vi.fn().mockRejectedValueOnce(new Error("boom")).mockResolvedValue("ok");
    const request = createSharedRequest(load);

    await expect(request.get()).rejects.toThrow("boom");
    await expect(request.get()).resolves.toBe("ok");
    expect(load).toHaveBeenCalledTimes(2);
  });

  it("reset() aborts the in-flight request and forgets it", async () => {
    let signal: AbortSignal | undefined;
    const load = vi.fn((next: AbortSignal) => {
      signal = next;
      return new Promise<string>(() => {});
    });
    const request = createSharedRequest(load);

    void request.get();
    request.reset();

    expect(signal?.aborted).toBe(true);
  });
});
