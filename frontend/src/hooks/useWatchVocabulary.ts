"use client";

/**
 * 观看页的词汇侧读模型（FE-06 提取点）。
 *
 * 页面原先自己管三份词汇状态：正在学/复习中的词、已掌握的词、本视频是否已
 * 生成过筛集合，再把它们喂给字幕着色函数。这里把「取数与写操作」收成一个
 * hook，页面只拿到 `levelClassFor` 与「加入学习」动作。
 *
 * 着色规则本身在 `lib/watchWordHighlight.ts`（纯函数，有单测）。
 */

import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";

import { api } from "@/lib/api";
import { apiErrorMessage } from "@/lib/errors";
import { wordHighlightClassFor } from "@/lib/watchWordHighlight";
import type { VocabSetCreateResponse } from "@/types";

/**
 * 观看页只需要知道「本视频是否已建过集合」以及它的 id（点开时用），
 * 不需要 ``/vocab-sets`` 卡片里的标题、数量与缩略图。
 */
export interface WatchVocabSet {
  id: string;
  video_id: string | null;
}

interface WatchContextResponse {
  learning_words: string[];
  mastered_words: string[];
  vocab_set: WatchVocabSet | null;
}

interface Options {
  videoId: string;
  isAuthenticated: boolean;
  requireAuth: () => boolean;
  selectedExamLevel: string | null;
  /** 已存在集合时的出口（页面传 router.push，hook 不持有导航）。 */
  onOpenSet: (setId: string) => void;
}

interface WatchVocabulary {
  /** 正在学 / 复习中的词（字幕高亮最强档）。 */
  learningWords: Set<string>;
  /** 已掌握的词（只留虚线下划线）。 */
  masteredWords: Set<string>;
  /** 本视频的过筛集合；null 表示还没加入学习。 */
  vocabSet: WatchVocabSet | null;
  addingVocabSet: boolean;
  /** 已加入 → 打开集合；未加入 → 创建并 toast。 */
  addVocabSet: () => Promise<void>;
  /** 字幕 token → 档位类名。 */
  levelClassFor: (word: string, wordLevels: Record<string, string[]> | null) => string;
}

export function useWatchVocabulary({
  videoId,
  isAuthenticated,
  requireAuth,
  selectedExamLevel,
  onOpenSet,
}: Options): WatchVocabulary {
  const [learningWords, setLearningWords] = useState<Set<string>>(new Set());
  const [masteredWords, setMasteredWords] = useState<Set<string>>(new Set());
  const [vocabSet, setVocabSet] = useState<WatchVocabSet | null>(null);
  const [addingVocabSet, setAddingVocabSet] = useState(false);

  // 词表 + 本视频集合：一次请求取齐（``/vocabulary/watch-context``）。
  // 以前是三次（learning/reviewing 词、mastered 词、全部集合列表），播放页
  // 每次进入都要等三个往返。失败一律非致命：拿不到就不高亮、按钮保持
  // 「加入学习」，不挡播放。
  useEffect(() => {
    if (!isAuthenticated) return;
    let cancelled = false;
    const controller = new AbortController();
    api<WatchContextResponse>(
      `/api/v1/vocabulary/watch-context?video_id=${encodeURIComponent(videoId)}`,
      { signal: controller.signal }
    )
      .then((res) => {
        if (cancelled) return;
        setLearningWords(new Set(res.learning_words));
        setMasteredWords(new Set(res.mastered_words));
        setVocabSet(res.vocab_set);
      })
      .catch(() => {
        // 非致命：保留现有高亮与按钮状态。
      });
    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [isAuthenticated, videoId]);

  const addVocabSet = useCallback(async () => {
    if (!requireAuth()) return;
    if (vocabSet) {
      onOpenSet(vocabSet.id);
      return;
    }
    if (addingVocabSet) return;
    setAddingVocabSet(true);
    try {
      const res = await api<VocabSetCreateResponse>("/api/v1/vocab-sets", {
        method: "POST",
        body: JSON.stringify({
          video_id: videoId,
          ...(selectedExamLevel ? { exam_level: selectedExamLevel } : {}),
        }),
      });
      toast.success(res.message || "已加入学习");
      setVocabSet({ id: res.id, video_id: res.video_id });
    } catch (err) {
      toast.error(apiErrorMessage(err, "加入失败，请重试"));
    } finally {
      setAddingVocabSet(false);
    }
  }, [requireAuth, vocabSet, onOpenSet, addingVocabSet, videoId, selectedExamLevel]);

  const levelClassFor = useCallback(
    (word: string, wordLevels: Record<string, string[]> | null) =>
      wordHighlightClassFor(word, wordLevels, {
        selectedExamLevel,
        learningWords,
        masteredWords,
      }),
    [selectedExamLevel, learningWords, masteredWords]
  );

  return {
    learningWords,
    masteredWords,
    vocabSet,
    addingVocabSet,
    addVocabSet,
    levelClassFor,
  };
}
