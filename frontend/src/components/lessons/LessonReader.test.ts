import * as React from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createLessonReaderLoader, LessonReader } from "@/components/lessons/LessonReader";
import { getLesson, getLessonState, type LessonDetail, type LessonState } from "@/lib/lessons";
import { ApiClientError } from "@/lib/createApiClient";

vi.mock("@/lib/lessons", async (original) => ({
  ...(await original<typeof import("@/lib/lessons")>()),
  getLesson: vi.fn(),
  getLessonState: vi.fn(),
}));

function detail(revision = "revision-1"): LessonDetail {
  const attribution = {
    attribution: "Test author",
    basis: "Own work",
    evidence_url: "https://example.org",
  };
  return {
    lesson_id: "synthetic-lesson",
    revision_id: revision,
    fingerprint: "test-fingerprint",
    fingerprint_version: "slcs-pack-v0.1-sha256",
    permissions: { model_processing: false, tutor_enabled: false, vocabulary_enabled: true },
    pack: {
      title: `Synthetic ${revision}`,
      media: {
        source_url: "https://example.org/video",
        access_mode: "external_link",
        duration_ms: 1000,
      },
      segments: [],
      vocabulary: [],
      provenance: {
        media: attribution,
        transcript: attribution,
        translation: attribution,
        vocabulary: attribution,
      },
    },
  };
}

function state(lesson: LessonDetail): LessonState {
  return {
    lesson_id: lesson.lesson_id,
    revision_id: lesson.revision_id,
    title: lesson.pack.title,
    access_mode: lesson.pack.media.access_mode,
    fingerprint: lesson.fingerprint,
    fingerprint_version: lesson.fingerprint_version,
    permissions: lesson.permissions,
  };
}

beforeEach(() => vi.resetAllMocks());
afterEach(() => vi.unstubAllGlobals());

describe("pinned lesson reader loading", () => {
  it("loads the full body on the first fixed-revision visit, not just _state", async () => {
    const lesson = detail();
    vi.mocked(getLesson).mockResolvedValue(lesson);
    const signal = new AbortController().signal;
    const load = createLessonReaderLoader(lesson.lesson_id, lesson.revision_id);

    expect(await load(signal)).toBe(lesson);
    expect(getLesson).toHaveBeenCalledExactlyOnceWith(lesson.lesson_id, lesson.revision_id, signal);
    expect(getLessonState).not.toHaveBeenCalled();
  });

  it("pins a current-version visit after loading and only revalidates that revision", async () => {
    const lesson = detail();
    vi.mocked(getLesson).mockResolvedValue(lesson);
    vi.mocked(getLessonState).mockResolvedValue(state(lesson));
    const signal = new AbortController().signal;
    const load = createLessonReaderLoader(lesson.lesson_id, null);

    await load(signal);
    expect(await load(signal)).toBe(lesson);
    expect(getLesson).toHaveBeenCalledExactlyOnceWith(lesson.lesson_id, null, signal);
    expect(getLessonState).toHaveBeenCalledExactlyOnceWith(
      lesson.lesson_id,
      lesson.revision_id,
      signal
    );
  });

  it("updates permission projection without replacing the immutable pack", async () => {
    const lesson = detail();
    vi.mocked(getLesson).mockResolvedValue(lesson);
    const permissions = {
      model_processing: false,
      tutor_enabled: false,
      vocabulary_enabled: false,
    };
    vi.mocked(getLessonState).mockResolvedValue({ ...state(lesson), permissions });
    const signal = new AbortController().signal;
    const load = createLessonReaderLoader(lesson.lesson_id, lesson.revision_id);

    await load(signal);
    const projected = await load(signal);
    expect(projected.pack).toBe(lesson.pack);
    expect(projected.permissions).toEqual(permissions);
    expect(getLesson).toHaveBeenCalledTimes(1);
  });

  it("retries a failed first fixed-revision load with the full body", async () => {
    const lesson = detail();
    vi.mocked(getLesson).mockRejectedValueOnce(new Error("offline")).mockResolvedValueOnce(lesson);
    const load = createLessonReaderLoader(lesson.lesson_id, lesson.revision_id);
    const signal = new AbortController().signal;

    await expect(load(signal)).rejects.toThrow("offline");
    expect(await load(signal)).toBe(lesson);
    expect(getLesson).toHaveBeenNthCalledWith(2, lesson.lesson_id, lesson.revision_id, signal);
    expect(getLessonState).not.toHaveBeenCalled();
  });

  it.each([0, 403, 404, 410, 503])(
    "reloads the pinned body after revalidation failure %s, never current",
    async (status) => {
      const lesson = detail();
      vi.mocked(getLesson).mockResolvedValue(lesson);
      vi.mocked(getLessonState).mockRejectedValue(new ApiClientError("unavailable", status));
      const signal = new AbortController().signal;
      const load = createLessonReaderLoader(lesson.lesson_id, null);

      await load(signal);
      await expect(load(signal)).rejects.toMatchObject({ status });
      expect(await load(signal)).toBe(lesson);
      expect(getLesson).toHaveBeenNthCalledWith(1, lesson.lesson_id, null, signal);
      expect(getLesson).toHaveBeenNthCalledWith(2, lesson.lesson_id, lesson.revision_id, signal);
      expect(getLessonState).toHaveBeenCalledTimes(1);
    }
  );

  it("never returns the cached pack after both availability and pinned-body requests reject withdrawal", async () => {
    const lesson = detail();
    const unavailable = new ApiClientError("withdrawn", 410);
    vi.mocked(getLesson).mockResolvedValueOnce(lesson).mockRejectedValue(unavailable);
    vi.mocked(getLessonState).mockRejectedValue(unavailable);
    const signal = new AbortController().signal;
    const load = createLessonReaderLoader(lesson.lesson_id, null);

    await load(signal);
    await expect(load(signal)).rejects.toBe(unavailable);
    await expect(load(signal)).rejects.toBe(unavailable);
    expect(getLesson).toHaveBeenLastCalledWith(lesson.lesson_id, lesson.revision_id, signal);
    expect(getLessonState).toHaveBeenCalledTimes(1);
  });

  it("does not reuse a body returned after its request was aborted", async () => {
    const lesson = detail();
    const controller = new AbortController();
    vi.mocked(getLesson)
      .mockImplementationOnce(async () => {
        controller.abort();
        return lesson;
      })
      .mockResolvedValueOnce(lesson);
    const load = createLessonReaderLoader(lesson.lesson_id, lesson.revision_id);

    await expect(load(controller.signal)).rejects.toMatchObject({ name: "AbortError" });
    const retrySignal = new AbortController().signal;
    expect(await load(retrySignal)).toBe(lesson);
    expect(getLesson).toHaveBeenCalledTimes(2);
    expect(getLessonState).not.toHaveBeenCalled();
  });

  it("keeps independent loader state for another lesson or revision", async () => {
    const first = detail();
    const second = { ...detail("revision-2"), lesson_id: "another-lesson" };
    vi.mocked(getLesson).mockResolvedValueOnce(first).mockResolvedValueOnce(second);
    const signal = new AbortController().signal;
    const oldLoad = createLessonReaderLoader(first.lesson_id, first.revision_id);
    const newLoad = createLessonReaderLoader(second.lesson_id, second.revision_id);

    await oldLoad(signal);
    expect(await newLoad(signal)).toBe(second);
    expect(getLesson).toHaveBeenNthCalledWith(2, second.lesson_id, second.revision_id, signal);
    expect(getLessonState).not.toHaveBeenCalled();
  });

  it("keys the whole reader session by the route so body, progress and selection reset together", () => {
    // Vitest uses the project's node environment; this checks the React session
    // boundary without pretending to exercise DOM effects or browser navigation.
    vi.stubGlobal("React", React);
    const props = { lessonId: "lesson", revision: "rev-1", anchor: null, conversationId: null };
    const original = LessonReader(props).key;
    expect(LessonReader({ ...props }).key).toBe(original);
    expect(LessonReader({ ...props, lessonId: "other" }).key).not.toBe(original);
    expect(LessonReader({ ...props, revision: "rev-2" }).key).not.toBe(original);
    expect(
      LessonReader({ ...props, anchor: { segment_id: "s1", token_ids: ["t1"] } }).key
    ).not.toBe(original);
    expect(LessonReader({ ...props, conversationId: "conversation" }).key).not.toBe(original);
  });
});
