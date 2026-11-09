"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { createSharedRequest } from "@/lib/sharedRequest";
import { useAuthStore } from "@/stores/authStore";
import type { VideoCard } from "@/types";

/**
 * 「继续学习」的唯一条目：最近一条未完成且真的看过的记录。
 *
 * 首页把同一条数据用在两个地方（`DiscoverContinue` 的续看条、`HomePage`
 * 的首屏布局门）。它们共用本模块级的共享请求：一次页面加载只发一次
 * `/learning/continue`，第二个消费者直接拿结果，而不是等第一个完成后
 * 再发一遍。
 */
export interface ContinueItem {
  video: VideoCard;
  position_seconds: number;
  progress_percentage: number;
  remaining_seconds: number | null;
}

interface ContinueResponse {
  items: ContinueItem[];
  total: number;
}

const continueRequest = createSharedRequest<ContinueItem | null>((signal) =>
  api<ContinueResponse>("/api/v1/learning/continue?limit=1", { signal }).then(
    (data) => data.items[0] ?? null
  )
);

export interface ContinueLearningState {
  item: ContinueItem | null;
  loading: boolean;
  failed: boolean;
  retry: () => void;
}

export function useContinueLearning(): ContinueLearningState {
  const authenticated = useAuthStore((state) => state.isAuthenticated);
  const [item, setItem] = useState<ContinueItem | null>(null);
  const [loading, setLoading] = useState(false);
  const [failed, setFailed] = useState(false);
  const [attempt, setAttempt] = useState(0);

  const retry = useCallback(() => {
    // Drop the cached failure/result so the retry really hits the network.
    continueRequest.reset();
    setAttempt((value) => value + 1);
  }, []);

  useEffect(() => {
    if (!authenticated) {
      continueRequest.reset();
      setItem(null);
      setLoading(false);
      setFailed(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setFailed(false);
    continueRequest
      .get()
      .then((next) => {
        if (!cancelled) setItem(next);
      })
      .catch(() => {
        if (!cancelled) {
          setFailed(true);
          setItem(null);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
      continueRequest.release();
    };
  }, [authenticated, attempt]);

  return { item, loading, failed, retry };
}
