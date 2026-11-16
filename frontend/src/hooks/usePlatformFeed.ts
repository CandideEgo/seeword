"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { isCefrLevel } from "@/lib/cefrLevels";
import { TOPIC_CATEGORY_LABELS } from "@/lib/topicCategories";
import { usePaginatedList } from "@/hooks/usePaginatedList";
import type { Category, VideoItem } from "@/types/platform";
import type { Paginated, VideoCard } from "@/types";

/** Feed ordering. "recommended" is the personalized mix for the unfiltered home
 *  view; every other value maps to /browse/feed?sort=… and composes with
 *  category/level filters. */
const SORT_VALUES = ["recommended", "hot", "latest", "favorite", "weekly_favorite"] as const;

/** The array is the single source of truth: a value cannot be part of this type
 *  and yet be missing from `SORT_VALUES` — `isFeedSort` would then quietly drop
 *  the `?sort=` a link carries and fall back to the default order. */
export type FeedSort = (typeof SORT_VALUES)[number];

/** Sort options for the feed toolbar. 「推荐」 is the personalized order and is
 *  only meaningful while no category/level filter is active (the caller hides
 *  it otherwise) — the backend has no personalized variant of /browse/feed. */
export const FEED_SORT_OPTIONS: { id: FeedSort; label: string }[] = [
  { id: "recommended", label: "推荐" },
  { id: "latest", label: "最新" },
  { id: "hot", label: "热播" },
  { id: "favorite", label: "收藏最多" },
  { id: "weekly_favorite", label: "本周收藏" },
];

function isFeedSort(value: string | null): value is FeedSort {
  return value !== null && (SORT_VALUES as readonly string[]).includes(value);
}

/** How each order is spelled on the wire. The key set is derived from `FeedSort`,
 *  so a new value there is a compile error until it is mapped here — a hand-written
 *  `if` would instead compile and silently drop the `?sort=` the URL carries.
 *  "latest" is the backend's own default and "recommended" is client-only (the
 *  unfiltered home view), so neither is sent — browse URLs and cache keys for the
 *  pre-existing values stay exactly as they were. */
const BROWSE_SORT_PARAM: Record<Exclude<FeedSort, "recommended" | "latest">, string> = {
  hot: "hot",
  favorite: "favorite",
  weekly_favorite: "weekly_favorite",
};

/** The `sort` to send to /browse/feed, or null to omit the parameter. */
function browseSortParam(sort: FeedSort): string | null {
  if (sort === "recommended" || sort === "latest") return null;
  return BROWSE_SORT_PARAM[sort];
}

/** 首页默认排序：个性化推荐；动手筛选后实际按最新排。 */
const DEFAULT_SORT: FeedSort = "recommended";

interface CategoryResponse {
  categories: Category[];
}

// Fallback categories if the API fails. Labels come from lib/topicCategories
// (single source shared with VideoCard); ids must stay in sync with the backend
// taxonomy (services/video_classification.TOPIC_CATEGORIES).
const TOPIC_TABS = Object.entries(TOPIC_CATEGORY_LABELS).map(([id, label]) => ({ id, label }));

const FALLBACK_CATEGORIES: Category[] = [{ id: "all", label: "全部" }, ...TOPIC_TABS];

/** 后端 categories 的 label 是英文（All / TED Talks…），展示一律用中文标签；
 *  后端将来新增、前端还没收录的 id 才回退到它自己的 label。 */
function localizeCategories(categories: Category[]): Category[] {
  return categories.map((category) =>
    category.id === "all"
      ? { ...category, label: "全部" }
      : { ...category, label: TOPIC_CATEGORY_LABELS[category.id] ?? category.label }
  );
}

/** Map a home-recommendation Video (from /recommendations/home) to VideoItem
 *  so the grid + VideoCard contract stays uniform across feeds. */
function homeVideoToItem(v: VideoCard): VideoItem {
  return {
    video_id: v.id,
    id: v.id,
    url: v.source_url,
    title: v.title,
    title_zh: v.title_zh,
    channel_title: v.channel_name ?? "",
    channel_slug: v.channel_slug ?? undefined,
    thumbnail_url: v.thumbnail_url ?? "",
    duration: v.duration,
    wpm: v.wpm,
    view_count: v.view_count,
    favorite_count: v.favorite_count,
    description: v.description,
    difficulty_level: v.difficulty_level,
    topic_tags: v.topic_tags,
    is_official: v.is_official,
    status: v.status,
    storage_mode: v.storage_mode,
    created_at: v.created_at,
    upload_date: v.upload_date,
    published_at: v.published_at,
  };
}

const PAGE_SIZE = 20;

export type DurationFilter = "all" | "short" | "medium" | "long";

const DURATION_PARAMS: Record<Exclude<DurationFilter, "all">, { min?: number; max?: number }> = {
  short: { max: 300 },
  medium: { min: 301, max: 900 },
  long: { min: 901 },
};

function isDurationFilter(value: string | null): value is DurationFilter {
  return value === "all" || value === "short" || value === "medium" || value === "long";
}

/**
 * 首页下滑流（原 `/browse` 的能力并入首页）。
 *
 * 筛选的唯一真相是 URL：`?category=` / `?level=` / `?sort=`，未筛选时不写参数。
 * 默认视图（无筛选 + 推荐）走 `/recommendations/home` 的个性化混合流；一旦选了
 * 分类或难度，就落到 `/browse/feed`，而那条路没有 "recommended"（browse.py 的
 * Literal 只有四种），所以展示层用 `effectiveSort`（= 最新）。
 */
export function usePlatformFeed() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const [categories, setCategories] = useState<Category[]>(FALLBACK_CATEGORIES);

  // 读取即派生，不做 state↔URL 双向同步 —— 那会竞态。返回时 URL 上带着来时的
  // 筛选，列表、滚动位置、返回按钮三者才对得上。
  const sortParam = searchParams.get("sort");
  const rawCategory = searchParams.get("category");
  const activeCategory = rawCategory || "all";
  const rawLevel = searchParams.get("level") ?? "all";
  // 非法档位当作「全部」：否则下拉显示第一个选项、请求却按非法值筛，页面会
  // 一直空着且看不出为什么（旧链接 / 手改 URL 都能触发）。
  const activeLevel = rawLevel === "all" || isCefrLevel(rawLevel) ? rawLevel : "all";
  const rawDuration = searchParams.get("duration");
  const activeDuration: DurationFilter = isDurationFilter(rawDuration) ? rawDuration : "all";
  const sort: FeedSort = isFeedSort(sortParam) ? sortParam : DEFAULT_SORT;

  const isHomeDefault =
    sort === "recommended" &&
    activeCategory === "all" &&
    activeLevel === "all" &&
    activeDuration === "all";
  const effectiveSort: FeedSort = isHomeDefault
    ? "recommended"
    : sort === "recommended"
      ? "latest"
      : sort;

  const query = searchParams.toString();
  // 已请求写入的 query。「清除筛选」会连续调用两个 setter，而 replace 落地的
  // searchParams 要等下一次 render 才更新 —— 没有这个 ref，两次调用会各自基于
  // 同一个旧 URL 计算，互相覆盖成「只清掉最后一个」。
  const pendingQueryRef = useRef(query);
  useEffect(() => {
    pendingQueryRef.current = query;
  }, [query]);

  /** 写回 URL；非默认值的才写，未筛选时 URL 保持干净。 */
  const updateFilters = useCallback(
    (patch: { category?: string; level?: string; duration?: DurationFilter; sort?: FeedSort }) => {
      const next = new URLSearchParams(pendingQueryRef.current);
      const apply = (key: string, value: string | undefined, fallback: string) => {
        if (value === undefined) return;
        if (value === fallback) next.delete(key);
        else next.set(key, value);
      };
      apply("category", patch.category, "all");
      apply("level", patch.level, "all");
      apply("duration", patch.duration, "all");
      apply("sort", patch.sort, DEFAULT_SORT);
      const nextQuery = next.toString();
      pendingQueryRef.current = nextQuery;
      router.replace(nextQuery ? `${pathname}?${nextQuery}` : pathname, { scroll: false });
    },
    [pathname, router]
  );

  const setActiveCategory = useCallback(
    (value: string) => updateFilters({ category: value }),
    [updateFilters]
  );
  const setActiveLevel = useCallback(
    (value: string) => updateFilters({ level: value }),
    [updateFilters]
  );
  const setSort = useCallback((value: FeedSort) => updateFilters({ sort: value }), [updateFilters]);
  const setDuration = useCallback(
    (value: DurationFilter) => updateFilters({ duration: value }),
    [updateFilters]
  );
  /** 清掉分类、难度与时长（排序保留用户显式选过的值；默认推荐会自动回到个性化流）。 */
  const clearFilters = useCallback(
    () => updateFilters({ category: "all", level: "all", duration: "all" }),
    [updateFilters]
  );

  const {
    items: videos,
    hasMore,
    total,
    loading,
    error,
    reload,
    loadMore,
    loaderRef,
  } = usePaginatedList<VideoItem>({
    fetcher: async (pg) => {
      // 默认视图（全部 + 推荐）: personalized 40/30/20/10 mix.
      // 任何筛选生效: /browse/feed（支持 category+level+sort）。
      if (isHomeDefault) {
        const data = await api<Paginated<VideoCard>>(
          `/api/v1/recommendations/home?page=${pg}&page_size=${PAGE_SIZE}`
        );
        return {
          items: (data.items ?? []).map(homeVideoToItem),
          page: data.page ?? pg,
          page_size: data.page_size ?? PAGE_SIZE,
          has_more: data.has_more,
          total: data.total,
        };
      }

      const params = new URLSearchParams({
        category: activeCategory,
        page: String(pg),
        page_size: String(PAGE_SIZE),
      });
      if (activeLevel !== "all") params.set("level", activeLevel);
      const duration = DURATION_PARAMS[activeDuration as Exclude<DurationFilter, "all">];
      if (activeDuration !== "all" && duration) {
        if (duration.min != null) params.set("duration_min", String(duration.min));
        if (duration.max != null) params.set("duration_max", String(duration.max));
      }
      const browseSort = browseSortParam(sort);
      if (browseSort) params.set("sort", browseSort);
      return api<Paginated<VideoItem>>(`/api/v1/browse/feed?${params.toString()}`);
    },
    mode: "append",
    filters: [activeCategory, activeLevel, activeDuration, sort],
  });

  // Fetch categories on mount - only once. The feed and the browse filter bar
  // share /browse/categories; labels are localized to the Chinese taxonomy.
  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const data = await api<CategoryResponse>(`/api/v1/browse/categories`);
        if (!cancelled && data.categories?.length) {
          setCategories(localizeCategories(data.categories));
        }
      } catch {
        // Use fallback categories - don't show error for categories
        // The feed fetch will show error if backend is unreachable
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  // There is no "import this video" action: the feed only ever returns videos
  // already in the DB (every row has `id`), the old POST /api/v1/videos submit
  // path is gone (INV-003 — no user submissions), and no consumer used the
  // callback that tried it.

  return {
    categories,
    activeCategory,
    setActiveCategory,
    activeLevel,
    setActiveLevel,
    activeDuration,
    setDuration,
    sort,
    effectiveSort,
    setSort,
    clearFilters,
    isFiltered: activeCategory !== "all" || activeLevel !== "all" || activeDuration !== "all",
    videos,
    loading,
    hasMore,
    total,
    error,
    retry: reload,
    loadMore,
    loaderRef,
  };
}
