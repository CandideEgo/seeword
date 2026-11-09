"use client";

import {
  useState,
  useEffect,
  useLayoutEffect,
  useRef,
  useCallback,
  useMemo,
  ViewTransition,
  type CSSProperties,
} from "react";
import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useDeepLink } from "@/hooks/useDeepLink";
import { useWatchClip } from "@/hooks/useWatchClip";
import { validWatchClip } from "@/lib/watchClip";
import { useWatchStore, type SubtitleMode } from "@/stores/watchStore";
import { useMediaQuery } from "@/hooks/useMediaQuery";
import { useRequireAuth } from "@/hooks/useRequireAuth";
import { useStickyPip } from "@/hooks/useStickyPip";
import { useSubtitleFollow } from "@/hooks/useSubtitleFollow";
import { useWatchChromeBridge } from "@/hooks/useWatchChromeBridge";
import { useVideoPlayer, bestVideoUrl, youtubeId, PLAYBACK_RATES } from "@/hooks/useVideoPlayer";
import { useWordLookup } from "@/hooks/useWordLookup";
import { useVideoMeta } from "@/hooks/useVideoMeta";
import { useWatchPreferences } from "@/hooks/useWatchPreferences";
import { useWatchVocabulary } from "@/hooks/useWatchVocabulary";
import { useWatchWordCard } from "@/hooks/useWatchWordCard";
import { mediaUrl } from "@/lib/api";
import {
  endWatchTime,
  glossFlowForReplay,
  track,
  trackFirstPlay,
  trackReplay,
  trackWatchTime,
} from "@/lib/analytics";
import { isWordSelected } from "@/lib/watchWordHighlight";
import { findSubtitleIndex } from "@/lib/subtitles";
import { resolveWatchReturn, watchFocusIssue, watchHref } from "@/lib/watchEntry";
import type { Subtitle, VideoDetail } from "@/types";
import { formatDuration, formatTime, formatCount } from "@/lib/format";
import { cn } from "@/lib/utils";
import { WordTooltipInline } from "@/components/subtitle/WordTooltipInline";
import { WordCardSheet } from "@/components/watch/WordCardSheet";
import { VideoControls } from "@/components/watch/VideoControls";
import { WatchDivider } from "@/components/watch/WatchDivider";
import { SaveSentenceButton } from "@/components/watch/SaveSentenceButton";
import { PageHeader } from "@/components/ui/PageHeader";
import { VideoTitle } from "@/components/video/VideoTitle";
import { WatchSourceCard } from "@/components/watch/WatchSourceCard";
import { RelatedVideos } from "@/components/watch/RelatedVideos";
import { VideoStats } from "@/components/video/VideoStats";
import { PublishedVideoEditorial } from "@/components/watch/PublishedVideoEditorial";
import { useWatchLayout } from "@/hooks/useWatchLayout";
import { CurrentSentenceCard } from "@/components/watch/CurrentSentenceCard";
import { LearningActions } from "@/components/watch/LearningActions";
import { WatchMoreSheet } from "@/components/watch/WatchMoreSheet";
import { reducedAid, validInterval } from "@/lib/watchSession";
import { cefrWithExamHint } from "@/lib/cefrLevels";
import {
  ArrowLeft,
  ArrowRight,
  Loader2,
  Play,
  Bookmark,
  Heart,
  Pencil,
  X,
  AlertCircle,
  FileText,
  PanelTop,
  RotateCcw,
  Maximize,
  PictureInPicture2,
  RectangleHorizontal,
  MoreHorizontal,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Textarea } from "@/components/ui/Input";
import { FullPageSpinner } from "@/components/common/Spinner";
import { ErrorState } from "@/components/common/ErrorState";
import { STEP_LABELS } from "@/lib/videoStatus";
import { Card } from "@/components/ui/Card";

// D1：字幕字号档位 → 像素的映射已随当前句卡搬到
// `components/watch/CurrentSentenceCard.tsx`（当前句现在只有那一份渲染）。

/**
 * 返回出口：带上 `?from=` 标记就回来源页，回到那个页面的 URL 状态；
 * 没有标记（旧链接、外部直达）才退化为浏览器后退。
 * 一律用 `replace`：`push` 会造出「首页 → 播放页 → 首页 → 后退 → 播放页」的历史环。
 */
function useWatchReturn(videoId: string): { label: string; go: () => void } {
  const router = useRouter();
  const searchParams = useSearchParams();

  return useMemo(() => {
    // `from=transcript` 的返回目标是 `/watch/{id}/transcript`，所以要带上 id。
    const target = resolveWatchReturn(searchParams, videoId);
    if (target) {
      return { label: target.label, go: () => router.replace(target.href) };
    }
    return {
      label: "返回",
      go: () => {
        if (window.history.length > 1) router.back();
        else router.replace("/");
      },
    };
  }, [router, searchParams, videoId]);
}

/**
 * 视频的动作行（点赞 / 收藏 / 加入学习 / 单词训练 / 笔记）。
 *
 * 抽出来是因为移动端要换位置：#24/#28 乙把首屏全给画面，页头那 102px 不能留在
 * 播放器上方（原型 B2-tap 实测画框顶 y=44＝壳顶，app 曾是 y=166）。移动端这一行
 * 落到字幕卡下面，桌面端仍在页头原位。
 */
function VideoActions({
  compact,
  isLiked,
  likeCount,
  isFavorited,
  noteOpen,
  onToggleLike,
  onToggleFavorite,
  onNotes,
}: {
  compact: boolean;
  isLiked: boolean;
  likeCount: number;
  isFavorited: boolean;
  noteOpen: boolean;
  onToggleLike: () => void;
  onToggleFavorite: () => void;
  onNotes: () => void;
}) {
  // 移动端一律 44px 触控目标（#24/#28 的触控基线）；桌面端是带文字的 pill，
  // 与首页/频道页的描边按钮同一套语言。
  if (compact) {
    const box = "w-11 h-11";
    return (
      <div className="flex items-center gap-1">
        <button
          className={cn(
            box,
            "px-2 rounded-lg flex items-center gap-1 text-muted hover:bg-surface-card hover:text-ink transition-colors cursor-pointer"
          )}
          onClick={onToggleLike}
          aria-label={isLiked ? `取消点赞（${likeCount}）` : `点赞（${likeCount}）`}
          title={isLiked ? "取消点赞" : "点赞"}
        >
          <Heart size={18} className={cn(isLiked && "fill-current text-error")} />
        </button>
        <button
          className={cn(
            box,
            "rounded-lg flex items-center justify-center text-muted hover:bg-surface-card hover:text-ink transition-colors cursor-pointer"
          )}
          onClick={onToggleFavorite}
          aria-label={isFavorited ? "取消收藏" : "收藏视频"}
          title={isFavorited ? "取消收藏" : "收藏"}
        >
          <Bookmark size={18} className={cn(isFavorited && "fill-current text-brand-500")} />
        </button>
        <button
          className={cn(
            box,
            "rounded-lg flex items-center justify-center transition-colors cursor-pointer",
            noteOpen
              ? "bg-brand-50 text-brand-500"
              : "text-muted hover:bg-surface-card hover:text-ink"
          )}
          onClick={onNotes}
          aria-label="笔记"
          title="笔记"
        >
          <Pencil size={18} />
        </button>
      </div>
    );
  }

  const pill =
    "inline-flex h-8 items-center gap-1.5 rounded-pill border px-3 text-meta font-semibold transition-colors cursor-pointer";
  return (
    <div className="flex flex-wrap items-center gap-2">
      <button
        className={cn(
          pill,
          isLiked
            ? "border-error/30 bg-red-soft text-error"
            : "border-hairline text-body hover:border-ink hover:text-ink"
        )}
        onClick={onToggleLike}
        aria-pressed={isLiked}
        aria-label={isLiked ? `取消点赞（${likeCount}）` : `点赞（${likeCount}）`}
      >
        <Heart size={14} className={cn(isLiked && "fill-current")} />
        {likeCount > 0 ? formatCount(likeCount) : "点赞"}
      </button>
      <button
        className={cn(
          pill,
          isFavorited
            ? "border-brand-200 bg-brand-50 text-brand-700"
            : "border-hairline text-body hover:border-ink hover:text-ink"
        )}
        onClick={onToggleFavorite}
        aria-label={isFavorited ? "取消收藏" : "收藏视频"}
        aria-pressed={isFavorited}
      >
        <Bookmark size={14} className={cn(isFavorited && "fill-current")} />
        {isFavorited ? "已收藏" : "收藏"}
      </button>
      <button
        className={cn(
          pill,
          noteOpen
            ? "border-brand-200 bg-brand-50 text-brand-700"
            : "border-hairline text-body hover:border-ink hover:text-ink"
        )}
        onClick={onNotes}
        aria-expanded={noteOpen}
      >
        <Pencil size={14} />
        笔记
      </button>
    </div>
  );
}

export default function WatchPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { isAuthenticated, isLoading } = useRequireAuth();
  const requireAuth = (): boolean => {
    if (isLoading || !isAuthenticated) {
      router.push("/login");
      return false;
    }
    return true;
  };
  const [acceptedFocus, setAcceptedFocus] = useState<string | null>(null);
  const [noteOpen, setNoteOpen] = useState(false);
  // ⋯ 面板（DEC-069 / #31）：来源/版权/语言/字号/倍速/动作行全收进这里，首屏那 355px
  // 次要信息归零。面板由页面渲染（在滚动容器里），开关状态经壳顶栏的 ⋯ 来回。
  const [moreOpen, setMoreOpen] = useState(false);
  const immersive = useWatchStore((s) => s.immersive);
  const videoAspectRatio = useWatchStore((s) => s.videoAspectRatio);
  const setImmersive = useWatchStore((s) => s.setImmersive);
  const keyboardActions = useRef({ previous: () => {}, next: () => {}, replay: () => {} });
  const previousSentence = useCallback(() => keyboardActions.current.previous(), []);
  const nextSentence = useCallback(() => keyboardActions.current.next(), []);
  const replayCurrentSentence = useCallback(() => keyboardActions.current.replay(), []);
  const toggleImmersive = useCallback(() => {
    setMoreOpen(false);
    const state = useWatchStore.getState();
    state.setImmersive(!state.immersive);
  }, []);
  const exitImmersive = useCallback(() => useWatchStore.getState().setImmersive(false), []);
  const moreTriggerRef = useRef<HTMLButtonElement>(null);
  const [titleExpanded, setTitleExpanded] = useState(false);

  // D13: deep link from /favorites with ?note=1 opens the note drawer
  // immediately so the user lands on their saved note.
  const searchParams = useSearchParams();
  const clipId = searchParams.get("clip");
  const clipResult = useWatchClip(id, clipId);
  const clipSlot = clipResult?.slot;
  const clipRange = clipSlot?.content.clip;
  const [invalidClip, setInvalidClip] = useState<string | null>(null);
  const [endedClip, setEndedClip] = useState<string | null>(null);
  const [clipPosition, setClipPosition] = useState(0);
  const appliedClip = useRef<string | null>(null);
  // A12 性能基线：只记第一次真正出画的耗时（同一个视频重播不算）。
  const firstPlayReported = useRef(false);
  const back = useWatchReturn(id);
  useEffect(() => {
    if (searchParams.get("note") === "1") setNoteOpen(true);
  }, [searchParams]);

  // 时间同步回调通过 ref 读取最新 video / setter（避免与 useVideoPlayer 返回值的前向引用）。
  const videoForTickRef = useRef<VideoDetail | null>(null);
  const setSubtitleIndexRef = useRef<(idx: number) => void>(() => {});
  const currentIndexRef = useRef(0);
  const [temporaryMode, setTemporaryMode] = useState<SubtitleMode | null>(null);
  const preferredMode = useWatchStore((s) => s.subtitleMode);
  const persistSubtitleMode = useWatchStore((s) => s.setSubtitleMode);
  const subtitleMode = temporaryMode ?? preferredMode;
  const [replayTarget, setReplayTarget] = useState<Subtitle | null>(null);
  const clearOnIntentRef = useRef<() => void>(() => {});
  const handleUserIntent = useCallback((clearAid = true) => {
    if (clearAid) {
      setTemporaryMode(null);
      setReplayTarget(null);
    }
    clearOnIntentRef.current();
  }, []);

  // Playback-time tick shared by both backends (HTML5 poll / YouTube poll):
  // keeps the current-subtitle highlight in sync. 学习时长不在这里累加 —— 它只
  // 认「播放状态 + 可见性 + 墙钟」（见下方 effect 与 lib/watchTime.ts）。
  const handleTimeTick = useCallback(
    (t: number) => {
      const v = videoForTickRef.current;
      if (!v) return;
      const idx = findSubtitleIndex(v.subtitles, t);
      if (idx !== -1) setSubtitleIndexRef.current(idx);
      if (clipId) setClipPosition(t);
      currentIndexRef.current = idx === -1 ? currentIndexRef.current : idx;
    },
    [clipId]
  );

  const {
    video,
    playbackMode,
    currentSubtitleIndex,
    setCurrentSubtitleIndex,
    videoRef,
    ytContainerRef,
    isYtMode,
    isPlaying,
    mediaState,
    mediaError,
    saveState,
    pauseForHelp,
    closeHelp,
    replaySentence,
    play,
    togglePlayPause,
    navigateSubtitle,
    seekTo,
    retry,
    rate,
    setRate,
    muted,
    toggleMute,
    setVolume,
    cycleSubtitleMode,
    fullscreenElRef,
    toggleFullscreen,
  } = useVideoPlayer({
    onPreviousSentence: previousSentence,
    onNextSentence: nextSentence,
    onReplaySentence: replayCurrentSentence,
    onToggleImmersive: toggleImmersive,
    onExitImmersive: exitImmersive,
    playbackRange: clipRange
      ? { start: clipRange.start_time, end: clipRange.end_time, onEnd: () => setEndedClip(clipId) }
      : null,
    playbackBlocked: !!clipId && (!clipRange || invalidClip === clipId),
    videoId: id,
    onTimeTick: handleTimeTick,
    hasExplicitFocus: !!(clipId || searchParams.get("sub") || searchParams.get("t")),
    subtitleModeOverride: subtitleMode,
    onUserIntent: handleUserIntent,
  });
  useEffect(() => {
    if (playbackMode !== "ready") setImmersive(false);
  }, [playbackMode, setImmersive]);

  // 有效学习时长（A02）：口径是「播放中且页面可见的墙钟秒数」，细节与边界在
  // lib/watchTime.ts。这里只按秒喂一次播放状态；`isPlaying` 翻转的那一次会
  // 立刻结算并补报尾段，所以暂停/切后台不会把最后几秒丢掉。
  useEffect(() => {
    trackWatchTime(id, isPlaying);
    if (isPlaying && !firstPlayReported.current) {
      firstPlayReported.current = true;
      // performance.now() 就是相对 navigation start 的毫秒数，正是「首播耗时」。
      if (typeof performance !== "undefined") trackFirstPlay(performance.now(), id);
    }
    if (!isPlaying) return;
    const timer = setInterval(() => trackWatchTime(id, true), 1000);
    return () => clearInterval(timer);
  }, [id, isPlaying]);

  // 离开观看页时结算尾段（路由切换、关闭标签页）。
  useEffect(() => endWatchTime, []);

  useEffect(() => {
    if (!clipId) {
      appliedClip.current = null;
      return;
    }
    if (!clipId || !clipSlot || !clipRange || !video || playbackMode !== "ready") return;
    if (!validWatchClip(clipSlot, video.subtitles, video.duration)) {
      setInvalidClip(clipId);
      return;
    }
    const key = `${id}|${clipId}`;
    if (appliedClip.current === key) return;
    appliedClip.current = key;
    setEndedClip(null);
    seekTo(clipRange.start_time, searchParams.get("autoplay") === "1");
  }, [clipId, clipSlot, clipRange, video, playbackMode, id, seekTo, searchParams]);

  useEffect(() => {
    if (clipId && clipRange && mediaState === "ended") setEndedClip(clipId);
  }, [clipId, clipRange, mediaState]);

  // Keep the tick callback's video reference in sync.
  useEffect(() => {
    videoForTickRef.current = video;
    setSubtitleIndexRef.current = setCurrentSubtitleIndex;
  }, [video, setCurrentSubtitleIndex]);

  // 字幕跟随（DEC-073）的两条路与暂停/恢复规则在 useSubtitleFollow 里；这里只安排
  // 「跟随哪个元素」与「画框贴顶了没有」两件事。
  // #30 决议：移动端滚过画框之后，画面**贴顶常驻**（不是缩成右下角小窗）。
  // 桌面端保持常规流里的 sticky 版式。
  const slotRef = useRef<HTMLDivElement>(null);
  const workspaceRef = useRef<HTMLDivElement>(null);
  const isMobile = useMediaQuery("(max-width: 1024px)");
  const leftPanelWidth = useWatchStore((s) => s.leftPanelWidth);
  const setLeftPanelWidth = useWatchStore((s) => s.setLeftPanelWidth);
  const mobileFrameSize = useWatchStore((s) => s.mobileFrameSize);
  const setMobileFrameSize = useWatchStore((s) => s.setMobileFrameSize);
  const hydrateLayout = useWatchStore((s) => s.hydrateLayout);
  const { split, asideHeight } = useWatchLayout(
    workspaceRef,
    playbackMode === "ready",
    isMobile,
    leftPanelWidth
  );
  // #30：移动端滚过画框之后画面贴顶常驻；DEC-069 之后钉住位置从壳顶变成**顶栏下沿**
  // （`main` 上沿，顶栏是 main 之上的常规流行）。`dismiss` 已随画面内的退出 X 一起删除
  // —— 退出跟随 = 滚回顶部（`useStickyPip` 的 `!out → setDismissed(false)` 本来就这么做）。
  const { isStuck } = useStickyPip(slotRef, isMobile && !immersive && playbackMode === "ready");
  const { subtitleListRef, resumeFollow, followEnabled, setFollowEnabled } = useSubtitleFollow({
    currentSubtitleIndex,
    isMobile,
    isStuck,
    slotRef,
  });

  const {
    isFavorited,
    isLiked,
    likeCount,
    favoriteCount,
    noteDraft,
    setNoteDraft,
    toggleFavorite,
    toggleLike,
    saveNote,
    clearNote,
  } = useVideoMeta(id, video?.like_count ?? 0, video?.favorite_count ?? 0);
  const {
    selectedWord,
    wordGloss,
    context: wordContext,
    lookupError,
    enrichmentError,
    retryLookup,
    handleWordClick,
    saveToVocabulary,
    speakWord,
    clearWord,
  } = useWordLookup({ requireAuth, videoId: id });
  useEffect(() => {
    clearOnIntentRef.current = clearWord;
  }, [clearWord]);
  const handleSaveWord = saveToVocabulary;

  // ---- 词卡锚点 / 来源句（audit D-watch P1 #9、#13）----------------------------
  // 位置与来源句状态在 useWatchWordCard；来源句解析与「再点同一个词 = 收起」的判定在
  // lib/watchWordSource（纯函数，有单测）。页面只把结果交给渲染。
  const { wordAnchorRect, wordSourceLabel, closeWordCard, openWordCard, revealWordSource } =
    useWatchWordCard({
      selectedWord,
      wordContext,
      replayTarget,
      subtitles: video?.subtitles,
      getCurrentIndex: () => currentIndexRef.current,
      clearWord,
      lookUpWord: handleWordClick,
      pauseForHelp,
      closeHelp,
      resumeFollow,
      videoTitle: video?.title,
      videoId: id,
      isMobile,
      immersive,
    });

  // D3b/S7b: deep-link focus — ?sub=<subtitle id> lands on one sentence
  // 「回到对应句子」/「回看原句」, ?word= highlights that word too, legacy ?t=
  // stays as a pure seek. The resolution and the once-per-link rule live in
  // `useDeepLink` / `lib/watchEntry`; this is only what the page does with it.
  const handleSentenceFocus = useCallback(
    (index: number) => {
      resumeFollow(); // 深链落点算一次显式导航：把跟随拉回来
      currentIndexRef.current = index;
      setCurrentSubtitleIndex(index); // 句高亮 + 字幕跟随联动
    },
    [resumeFollow, setCurrentSubtitleIndex]
  );
  useDeepLink({
    enabled: !clipId,
    videoId: id,
    duration: video?.duration,
    playbackMode,
    subtitles: video?.subtitles,
    params: searchParams,
    videoRef,
    onSentenceFocus: handleSentenceFocus,
    onWordFocus: (word, index) =>
      openWordCard(word, null, index != null && index >= 0 ? video?.subtitles[index] : null),
    onAutoplay: play,
    onSeek: seekTo,
  });

  const setSubtitleMode = (mode: SubtitleMode) => {
    setTemporaryMode(null);
    persistSubtitleMode(mode);
  };
  useEffect(() => {
    setTemporaryMode(null);
  }, [preferredMode]);
  function handleReplay(reduce = false) {
    const subtitles = video?.subtitles;
    const source = replayTarget ?? wordContext ?? subtitles?.[currentSubtitleIndex];
    if (!source) return;
    clearWord();
    closeHelp(false);
    if (replaySentence(source.start_time, source.end_time)) {
      setReplayTarget(source);
      if (reduce) setTemporaryMode(reducedAid(subtitleMode));
      // A14：落在词卡会话窗口内、同一句的重听带上该次 gloss_open 的 flow_id；
      // 普通逐句重听不带，两类分开计数（见 lib/analytics.ts 的 trackReplay）。
      const sourceIndex = subtitles ? subtitles.indexOf(source) : -1;
      const glossFlowId = glossFlowForReplay(sourceIndex >= 0 ? sourceIndex : null);
      trackReplay(id, glossFlowId, {
        sentence_index: sourceIndex >= 0 ? sourceIndex : null,
        from_gloss: glossFlowId !== undefined,
        reduced_aid: reduce,
      });
    }
  }
  const replayRef = useRef(handleReplay);
  useLayoutEffect(() => {
    replayRef.current = handleReplay;
  });
  const replayStable = useCallback(() => replayRef.current(), []);
  const selectedExamLevel = useWatchStore((s) => s.selectedExamLevel);
  const setSelectedExamLevel = useWatchStore((s) => s.setSelectedExamLevel);
  const hydrateSubtitleMode = useWatchStore((s) => s.hydrateSubtitleMode);

  // 字幕模式首帧用默认值，挂载后再补一次本地存储值（BUG-13）——模块初始化时读
  // localStorage 会让服务端渲染与客户端首帧不一致。
  useEffect(() => {
    hydrateSubtitleMode();
    hydrateLayout();
    useWatchStore.getState().setVideoAspectRatio(16 / 9);
    setImmersive(false);
    return () => setImmersive(false);
  }, [id, hydrateSubtitleMode, hydrateLayout, setImmersive]);

  // D1：目标考试级别与字幕字号都来自用户偏好（读写集中在 useWatchPreferences）。
  const { subtitleFontSize, handleExamLevelChange, handleFontSizeChange } = useWatchPreferences({
    enabled: isAuthenticated,
    setSelectedExamLevel,
  });

  // 字幕着色所需的词表、本视频的过筛集合与「加入学习」动作（见 useWatchVocabulary）。
  const { vocabSet, addingVocabSet, addVocabSet, levelClassFor } = useWatchVocabulary({
    videoId: id,
    isAuthenticated,
    requireAuth,
    selectedExamLevel,
    onOpenSet: (setId) => router.push(`/vocabulary/sets/${setId}`),
  });

  function handleNextSubtitle() {
    if (!video?.subtitles) return;
    if (currentSubtitleIndex < video.subtitles.length - 1) {
      const next = video.subtitles[currentSubtitleIndex + 1];
      if (!next) return;
      resumeFollow(); // 显式「下一句」= 恢复跟随
      setCurrentSubtitleIndex(currentSubtitleIndex + 1);
      seekTo(next.start_time);
    }
  }

  // onNext 必须与 onPrev 对称：store 里只放**稳定引用**，闭包经 ref 镜像读最新状态。
  // （第一版把 handleNextSubtitle 直接塞进 store：它闭包里的 currentSubtitleIndex 冻结在
  //  memo 上次重算的那一刻，实测「下一句」会往回跳，然后彻底不动。见 INV-025。）
  const nextRef = useRef(handleNextSubtitle);
  useLayoutEffect(() => {
    nextRef.current = handleNextSubtitle;
  });
  const onNextStable = useCallback(() => nextRef.current(), []);
  useLayoutEffect(() => {
    keyboardActions.current = {
      previous: () => {
        resumeFollow();
        navigateSubtitle(-1);
      },
      next: onNextStable,
      replay: replayStable,
    };
  }, [resumeFollow, navigateSubtitle, onNextStable, replayStable]);

  // 考试词高亮（DEC-073 四档）与「当前词是否被选中」的判定都在
  // `useWatchVocabulary` / `lib/watchWordHighlight`，页面只把 `levelClassFor` 交给渲染。
  const isSelectedWord = useCallback(
    (word: string) => isWordSelected(word, selectedWord),
    [selectedWord]
  );

  // ---- 页面 → 壳：顶栏内容 + 底栏句柄（DEC-069 / #31）----------------------------
  // 装配与 INV-025 那几条约束都在 useWatchChromeBridge 里；这里只交出页面这一侧的状态与回调。
  // **必须放在下面那些 early return 之前**：hook 一旦在某个分支被跳过，React 直接抛
  // 「Rendered fewer hooks than expected」并把整棵页面树卸载 —— 实测表现是只剩壳、
  // 页面内容整块消失（这个坑真踩过）。
  const chrome = useWatchChromeBridge({
    enabled: playbackMode === "ready",
    video,
    videoRef,
    moreOpen,
    setMoreOpen,
    onReplay: replayStable,
    onSeek: seekTo,
    selectedExamLevel,
    onExamLevelChange: handleExamLevelChange,
    onBack: back.go,
    isPlaying,
    onTogglePlay: togglePlayPause,
    resumeFollow,
    navigateSubtitle,
    onNext: onNextStable,
    isYtMode,
  });

  // --- Keyboard shortcuts: 页面层不再持有快捷键 —— D1 后统一由
  // useVideoPlayer 处理（空格/←→/↑↓音量/M/F/C/S）；句子导航通过统一播放器协调。

  // --- Loading / Error states ---
  // 终态处理失败先于通用加载失败态：playbackMode === "error" 也会由处理中轮询到的
  // error 置位（见 useVideoPlayer），其通用文案会遮蔽这里的真实原因与 error_message。
  if (video?.status === "error")
    return (
      <ErrorState
        title="视频暂时无法播放"
        message="请选择其他视频，或通过帮助与反馈联系我们。"
        action={
          <button onClick={back.go} className="mt-4 text-copy text-brand-700 hover:underline">
            {back.label}
          </button>
        }
        fullPage
      />
    );

  if (!video && playbackMode !== "error") return <FullPageSpinner />;

  if (playbackMode === "error") {
    return (
      <div className="flex min-h-full items-center justify-center bg-canvas">
        <div className="text-center">
          <AlertCircle size={48} className="mx-auto text-muted mb-4" />
          <p className="text-ink">加载视频失败</p>
          <p className="mt-1 text-copy text-muted">请检查网络连接后重试</p>
          <Button onClick={retry} className="mt-4">
            重新加载
          </Button>
        </div>
      </div>
    );
  }

  if (!video) return <FullPageSpinner />;

  // 已下线（需求 §5.1 offline / §5.3）：媒体已释放，学习记录仍在。
  // 收藏夹与集合页「回看原视频」会落到这里，故给出明确说明与出口。
  if (playbackMode === "offline") {
    return (
      <div className="flex min-h-full items-center justify-center bg-canvas">
        <div className="text-center max-w-md px-4">
          <AlertCircle size={48} className="mx-auto text-muted mb-4" />
          <p className="text-copy-lg font-semibold text-ink">该视频已下架</p>
          <p className="mt-2 text-copy text-muted leading-relaxed">
            视频媒体已释放存储空间，不再提供播放。
            <br />
            你的学习记录（词库与视频集合）仍然保留，可以继续学习。
          </p>
          <div className="flex gap-3 justify-center mt-6">
            <Button onClick={() => router.push("/vocabulary")}>去单词训练</Button>
            <Button variant="outline" onClick={back.go}>
              {back.label}
            </Button>
          </div>
        </div>
      </div>
    );
  }

  if (playbackMode === "processing") {
    const stepLabel = video.processing_step
      ? (STEP_LABELS[video.processing_step] ?? "处理中...")
      : "处理中...";
    return (
      <div className="flex min-h-full items-center justify-center bg-canvas">
        <div className="text-center">
          <Loader2 size={32} className="mx-auto animate-spin text-brand-500" />
          <p className="mt-4 text-ink">{stepLabel}</p>
          <p className="mt-1 text-copy text-muted">视频下载和转码需要几分钟，请稍候</p>
          {video.status === "ready_subtitles" && (
            <p className="mt-2 text-meta text-success">字幕已就绪，视频处理中...</p>
          )}
        </div>
      </div>
    );
  }

  const focusIssue =
    acceptedFocus === `${id}|${searchParams}`
      ? null
      : watchFocusIssue(searchParams, video.subtitles, video.duration);
  const currentSubtitle = replayTarget ?? wordContext ?? video.subtitles[currentSubtitleIndex];
  const displayedIndex = currentSubtitle
    ? video.subtitles.findIndex((s) => s.id === currentSubtitle.id)
    : currentSubtitleIndex;
  /**
   * 学习笔记面板。抽出来是因为它现在有两个落点（DEC-069 第 6 条把移动端的笔记入口
   * 收进了 ⋯ 面板）：桌面端仍在页头原位，移动端由 `WatchMoreSheet` 的 `extra` 渲染。
   */
  const notesPanel = noteOpen ? (
    <Card padding={4} className="mt-3 animate-fade-in">
      <div className="flex items-center justify-between mb-2.5">
        <span className="text-copy font-semibold">学习笔记</span>
        <button
          onClick={() => setNoteOpen(false)}
          className="text-muted hover:text-ink"
          aria-label="关闭笔记"
        >
          <X size={16} />
        </button>
      </div>
      <Textarea
        value={noteDraft}
        onChange={(e) => setNoteDraft(e.target.value)}
        placeholder="记录重点句型、生词或心得..."
        rows={3}
        className="resize-none mb-3"
      />
      <div className="flex items-center justify-end gap-2">
        <Button variant="outline" size="sm" onClick={clearNote}>
          清空
        </Button>
        <Button size="sm" onClick={saveNote}>
          保存
        </Button>
      </div>
    </Card>
  ) : null;

  const learningPlaybackActions = (
    <>
      <Button
        variant="text"
        onClick={() => {
          setMoreOpen(false);
          play();
        }}
      >
        继续播放
      </Button>
      {currentSubtitle && <SaveSentenceButton subtitleId={currentSubtitle.id} />}
      {temporaryMode !== null && (
        <Button variant="outline" onClick={() => setTemporaryMode(null)}>
          恢复辅助
        </Button>
      )}
    </>
  );

  // 路由过渡（Phase 2）：首页 ↔ 观看页整块淡出/淡入。包成变量再交给
  // <ViewTransition>，避免把整页 JSX 缩进改一遍；不支持 View Transitions 的
  // 浏览器与减少动效用户都自动降级为瞬时切换（CSS 见 globals.css）。
  const page = (
    <div
      className={cn(
        "watch-page pb-8",
        immersive && "is-immersive",
        immersive && selectedWord && "has-word-card"
      )}
      style={{ "--watch-media-aspect": videoAspectRatio } as CSSProperties}
    >
      <div className="watch-heading">
        <div className="flex min-h-9 items-center justify-between gap-3">
          <div className="flex min-w-0 items-center gap-2 text-meta text-muted">
            <button
              type="button"
              onClick={back.go}
              aria-label={back.label}
              className="inline-flex min-h-11 shrink-0 items-center gap-1 font-semibold hover:text-ink"
            >
              <ArrowLeft size={14} />
              {back.label}
            </button>
            <span aria-hidden>·</span>
            {video.channel_slug ? (
              <Link
                href={`/channels/${video.channel_slug}`}
                className="truncate hover:text-brand-700"
              >
                {video.channel_name || "SeeWord"}
              </Link>
            ) : (
              <span className="truncate">{video.channel_name || "SeeWord"}</span>
            )}
          </div>
          {isMobile ? (
            <Button
              variant="text"
              size="sm"
              data-testid="watch-more-button"
              aria-label="更多设置"
              title="更多设置"
              ref={moreTriggerRef}
              onClick={chrome.onMore}
              aria-expanded={moreOpen}
            >
              <MoreHorizontal size={20} aria-hidden />
            </Button>
          ) : (
            <VideoActions
              compact
              isLiked={isLiked}
              likeCount={likeCount}
              isFavorited={isFavorited}
              noteOpen={noteOpen}
              onToggleLike={toggleLike}
              onToggleFavorite={toggleFavorite}
              onNotes={() => setNoteOpen((v) => !v)}
            />
          )}
        </div>
        <PageHeader
          className="watch-page-heading"
          title={
            <VideoTitle
              video={video}
              as="span"
              clampZh={titleExpanded ? 0 : 1}
              clampEn={!titleExpanded}
            />
          }
          meta={
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
              <span>
                {video.difficulty_level ? cefrWithExamHint(video.difficulty_level) : "难度待评估"}
              </span>
              <span>{formatDuration(video.duration)}</span>
              <span>{video.subtitles.length} 句字幕</span>
              <button
                type="button"
                aria-expanded={titleExpanded}
                onClick={() => setTitleExpanded((v) => !v)}
                className="text-muted hover:text-ink"
              >
                {titleExpanded ? "收起标题" : "展开标题"}
              </button>
            </div>
          }
        />
      </div>
      {clipId && (
        <section
          aria-label="片段任务"
          className="mb-3 rounded-md border border-hairline bg-surface-soft px-3 py-2 text-meta"
        >
          {clipRange && invalidClip !== clipId ? (
            <>
              <h2 className="font-semibold text-ink">{clipSlot!.content.headline}</h2>
              <p className="text-muted">
                片段 {formatTime(clipRange.start_time)}–{formatTime(clipRange.end_time)} · 剩余{" "}
                {Math.ceil(
                  Math.max(0, clipRange.end_time - Math.max(clipRange.start_time, clipPosition))
                )}{" "}
                秒
              </p>
              <progress
                aria-label="片段播放进度"
                className="h-1 w-full accent-brand-500"
                max={clipRange.end_time - clipRange.start_time}
                value={Math.max(
                  0,
                  Math.min(clipRange.end_time, clipPosition) - clipRange.start_time
                )}
              />
              {endedClip === clipId && (
                <div role="status" className="mt-1 text-ink">
                  <p>已到片段终点。可以重听，或选择继续完整视频。</p>
                  <Button
                    size="sm"
                    onClick={() => {
                      setEndedClip(null);
                      seekTo(clipRange.start_time);
                    }}
                  >
                    重听片段
                  </Button>
                  <Button
                    variant="text"
                    size="sm"
                    onClick={() =>
                      router.replace(
                        watchHref(id, {
                          from: "home",
                          extra: { t: clipRange.end_time, autoplay: 1 },
                        })
                      )
                    }
                  >
                    继续完整视频
                  </Button>
                </div>
              )}
            </>
          ) : (
            <p role="status">
              {invalidClip === clipId
                ? "字幕位置已变化，片段已失效。请展开“片段与表达”查看当前内容，或打开完整视频。"
                : (clipResult?.error ?? "正在验证片段信息…")}
            </p>
          )}
          <div className="flex gap-3">
            <Link
              className="min-h-9 inline-flex items-center text-brand-700"
              href={watchHref(id, { from: "home" })}
            >
              看完整视频
            </Link>
            <Link className="min-h-9 inline-flex items-center text-muted" href="/">
              回首页
            </Link>
          </div>
        </section>
      )}
      <div
        ref={workspaceRef}
        data-testid="watch-workspace"
        data-layout={immersive ? "immersive" : isMobile ? "mobile" : split ? "split" : "stacked"}
        className={cn(
          "watch-workspace",
          isMobile && "is-mobile",
          !isMobile && !!split && !immersive && "is-split"
        )}
        style={
          {
            "--watch-video-width": split ? `${split.left}px` : undefined,
            "--watch-aside-height": asideHeight ? `${asideHeight}px` : undefined,
          } as CSSProperties
        }
      >
        <div id="watch-video-column" className={cn("watch-video-column", isMobile && "contents")}>
          <div className={cn("watch-stage", isMobile && "contents")}>
            {immersive && !isMobile && (
              <button
                type="button"
                onClick={toggleImmersive}
                aria-label="退出沉浸"
                aria-keyshortcuts="t"
                title="退出沉浸（T / Esc）"
                className="watch-immersive-exit"
              >
                <X size={16} aria-hidden />
                退出沉浸
                <kbd className="watch-key" aria-hidden>
                  T
                </kbd>
              </button>
            )}
            <div className="watch-viewing-group">
              <div className="watch-picture-slot">
                <div
                  ref={slotRef}
                  data-testid="video-frame"
                  data-frame-size={isMobile ? mobileFrameSize : "desktop"}
                  className={cn(
                    "watch-video-frame relative w-full bg-surface-dark overflow-hidden rounded-lg",
                    isMobile && "is-mobile",
                    isMobile && isStuck && "is-stuck"
                  )}
                >
                  <div
                    ref={(el) => {
                      // D1：F 全屏的目标容器（播放器外壳）。
                      fullscreenElRef.current = el;
                    }}
                    className="watch-media absolute inset-0"
                  >
                    {playbackMode === "ready" && bestVideoUrl(video) ? (
                      <>
                        <video
                          ref={chrome.attachVideo ?? videoRef}
                          // iOS Safari 对无 playsinline 的 <video> 会强制系统全屏播放，
                          // 页面字幕被遮盖；必须内联播放才能字幕/视频同屏。
                          playsInline
                          webkit-playsinline="true"
                          x5-playsinline="true"
                          src={mediaUrl(bestVideoUrl(video)!, {
                            // /media 需要可识别的观看者，<video> 无法带 Authorization
                            // 头，统一用 ?token= 携带。
                            withToken: true,
                          })}
                          // 首帧解码前显示封面，避免加载瞬间是一块黑屏。
                          poster={video.thumbnail_url ? mediaUrl(video.thumbnail_url) : undefined}
                          className="h-full w-full object-contain"
                          onLoadedMetadata={(event) => {
                            const { videoWidth, videoHeight } = event.currentTarget;
                            if (videoWidth > 0 && videoHeight > 0)
                              useWatchStore
                                .getState()
                                .setVideoAspectRatio(videoWidth / videoHeight);
                          }}
                          // 不再挂 onTimeUpdate（BUG-14）：250ms 轮询已是唯一 tick 源，
                          // 两条路径各跑一遍二分查找属冗余。轮询同时负责 iOS 的
                          // isPlaying 校正，摘掉原生事件不会丢同步或播放态。
                          onPlay={() =>
                            track("play", { position_s: videoRef.current?.currentTime ?? 0 }, id)
                          }
                          onPause={() =>
                            track("pause", { position_s: videoRef.current?.currentTime ?? 0 }, id)
                          }
                          onSeeked={() =>
                            track("seek", { position_s: videoRef.current?.currentTime ?? 0 }, id)
                          }
                          onEnded={() => {
                            track(
                              "complete",
                              { position_s: videoRef.current?.currentTime ?? 0 },
                              id
                            );
                          }}
                        />
                        {/* DEC-069：画面内**零覆盖物** —— 标题/返回键/退出 X/级别药丸/入画字幕
                      全部搬走（标题与返回进壳顶栏、级别进壳顶栏、字幕进画面正下方的当前句卡）。
                      桌面端只有 D1 控制条这一层，移动端连它也不在画面里（底栏接管）。 */}
                        {!isMobile && (
                          <VideoControls
                            videoRef={videoRef}
                            isPlaying={isPlaying}
                            duration={video.duration}
                            rate={rate}
                            setRate={setRate}
                            muted={muted}
                            toggleMute={toggleMute}
                            setVolume={setVolume}
                            subtitleMode={subtitleMode}
                            onCycleSubtitleMode={cycleSubtitleMode}
                            subtitleFontSize={subtitleFontSize}
                            onFontSizeChange={handleFontSizeChange}
                            toggleFullscreen={toggleFullscreen}
                            onTogglePlay={togglePlayPause}
                            onSeek={(t) => seekTo(t, isPlaying)}
                            immersive={immersive}
                            onToggleImmersive={toggleImmersive}
                          />
                        )}
                      </>
                    ) : playbackMode === "ready" && isYtMode && youtubeId(video) ? (
                      <div ref={ytContainerRef} className="h-full w-full" />
                    ) : (
                      <div className="flex h-full w-full items-center justify-center">
                        <div className="text-center">
                          <Play size={40} className="mx-auto text-white/30" />
                          <p className="mt-3 text-copy text-white/40">视频未就绪</p>
                        </div>
                      </div>
                    )}
                  </div>
                  {/* DEC-069：级别药丸搬进壳顶栏（移动端）；画面里不再有任何可点覆盖物 */}
                </div>
              </div>

              {/* Current sentence shares the full frame width in both layouts. */}
              {currentSubtitle && (
                <CurrentSentenceCard
                  variant={isMobile || immersive ? "band" : "card"}
                  className={cn(isMobile && "mt-0 rounded-none border-0 px-0")}
                  textEn={currentSubtitle.text_en}
                  textZh={currentSubtitle.text_zh ?? null}
                  wordLevels={currentSubtitle.word_levels ?? null}
                  subtitleMode={subtitleMode}
                  fontSize={subtitleFontSize}
                  isSelected={isSelectedWord}
                  levelClassFor={levelClassFor}
                  onWordClick={openWordCard}
                  onTogglePlay={togglePlayPause}
                  counter={`${displayedIndex + 1} / ${video.subtitles.length}`}
                />
              )}
            </div>
            <div className="watch-word-space" aria-hidden />
            {isMobile && (
              <div
                data-immersive-tools={immersive ? "true" : undefined}
                className="watch-mobile-tools flex flex-wrap items-center gap-x-3 gap-y-1 border-b border-hairline py-2 text-meta"
              >
                <div
                  role="group"
                  aria-label="画面大小"
                  className={cn(
                    "inline-flex rounded-pill bg-surface-soft p-1",
                    immersive && "hidden"
                  )}
                >
                  {(["standard", "compact"] as const).map((size) => (
                    <button
                      key={size}
                      type="button"
                      aria-pressed={mobileFrameSize === size}
                      onClick={() => setMobileFrameSize(size)}
                      aria-label={size === "standard" ? "标准" : "紧凑"}
                      title={size === "standard" ? "标准画面" : "紧凑画面"}
                      className={cn(
                        "inline-flex h-11 w-11 items-center justify-center rounded-pill font-medium",
                        mobileFrameSize === size && "bg-canvas text-brand-700"
                      )}
                    >
                      {size === "standard" ? (
                        <RectangleHorizontal size={18} aria-hidden />
                      ) : (
                        <PictureInPicture2 size={18} aria-hidden />
                      )}
                    </button>
                  ))}
                </div>
                <label className="inline-flex items-center gap-1">
                  <span className="sr-only">倍速</span>
                  <select
                    aria-label="播放倍速"
                    value={rate}
                    onChange={(e) => setRate(Number(e.target.value))}
                    className="min-h-11 bg-canvas text-ink"
                  >
                    {PLAYBACK_RATES.map((n) => (
                      <option key={n} value={n}>
                        {n}×
                      </option>
                    ))}
                  </select>
                </label>
                <button type="button" onClick={cycleSubtitleMode} className="min-h-11 text-body">
                  字幕：
                  {
                    { bilingual: "双语", english: "英文", chinese: "中文", hidden: "隐藏" }[
                      subtitleMode
                    ]
                  }
                </button>
                <Button
                  variant="text"
                  size="icon"
                  onClick={toggleFullscreen}
                  aria-label="全屏"
                  title="全屏"
                >
                  <Maximize size={18} aria-hidden />
                </Button>
                <Button
                  variant="text"
                  size="sm"
                  icon={PanelTop}
                  onClick={toggleImmersive}
                  aria-pressed={immersive}
                  aria-keyshortcuts="t"
                  aria-label={immersive ? "退出沉浸" : "沉浸观看"}
                  title={immersive ? "退出沉浸（T / Esc）" : "沉浸观看（T）"}
                  className={cn(
                    "watch-mobile-immersive",
                    !immersive && "watch-mobile-immersive-entry"
                  )}
                >
                  <span>{immersive ? "退出沉浸" : "沉浸观看"}</span>
                  <kbd className="watch-key" aria-hidden>
                    T
                  </kbd>
                </Button>
              </div>
            )}
            {!isMobile && (
              <div
                className="watch-sentence-actions flex flex-wrap items-center gap-2 border-y border-hairline py-2"
                data-immersive-tools={immersive ? "true" : undefined}
                data-testid="sentence-actions"
              >
                <div className="watch-sentence-group" role="group" aria-label="逐句播放">
                  <Button
                    variant="text"
                    icon={ArrowLeft}
                    size="sm"
                    onClick={previousSentence}
                    aria-label="上一句"
                    aria-keyshortcuts="a"
                    disabled={!video.subtitles.length}
                  >
                    上一句
                    <kbd className="watch-key" aria-hidden>
                      A
                    </kbd>
                  </Button>
                  <Button
                    variant="tonal"
                    icon={RotateCcw}
                    size="sm"
                    className="watch-replay-primary"
                    title="重听本句（R），到句末暂停"
                    onClick={replayCurrentSentence}
                    aria-label="重听本句"
                    aria-keyshortcuts="r"
                    disabled={
                      !currentSubtitle ||
                      !validInterval(
                        currentSubtitle.start_time,
                        currentSubtitle.end_time,
                        video.duration
                      )
                    }
                  >
                    重听本句
                    <kbd className="watch-key" aria-hidden>
                      R
                    </kbd>
                  </Button>
                  <Button
                    variant="text"
                    icon={ArrowRight}
                    size="sm"
                    iconRight
                    onClick={nextSentence}
                    aria-label="下一句"
                    aria-keyshortcuts="d"
                    disabled={!video.subtitles.length}
                  >
                    下一句
                    <kbd className="watch-key" aria-hidden>
                      D
                    </kbd>
                  </Button>
                </div>
                <div className="watch-learning-actions">{learningPlaybackActions}</div>
                {isYtMode && !immersive && (
                  <Button
                    variant="text"
                    size="sm"
                    icon={PanelTop}
                    onClick={toggleImmersive}
                    aria-pressed={immersive}
                    aria-keyshortcuts="t"
                  >
                    {immersive ? "退出沉浸" : "沉浸观看"}
                    <kbd className="watch-key" aria-hidden>
                      T
                    </kbd>
                  </Button>
                )}
              </div>
            )}
            {!isMobile && (
              <section
                aria-label="我的笔记"
                className="watch-notes mt-4 border-t border-hairline pt-4"
              >
                <div className="flex items-center justify-between gap-3">
                  <h2 className="text-copy font-semibold text-ink">我的笔记</h2>
                  <Button
                    variant="text"
                    size="sm"
                    onClick={() => setNoteOpen((v) => !v)}
                    aria-expanded={noteOpen}
                  >
                    {noteOpen ? "收起" : noteDraft.trim() ? "编辑" : "记一条"}
                  </Button>
                </div>
                {noteOpen ? (
                  notesPanel
                ) : noteDraft.trim() ? (
                  <p className="mt-2 whitespace-pre-line text-copy leading-relaxed text-body">
                    {noteDraft}
                  </p>
                ) : (
                  <p className="mt-2 text-meta text-muted">
                    还没有笔记。记下重点句型、生词或心得，存成整段视频的笔记。
                  </p>
                )}
              </section>
            )}
            {focusIssue && (
              <div role="alert" className="py-2 text-meta text-muted">
                {focusIssue.message}
                {focusIssue.fallback !== null && (
                  <Button
                    variant="text"
                    size="sm"
                    onClick={() => {
                      setAcceptedFocus(`${id}|${searchParams}`);
                      seekTo(focusIssue.fallback!, false);
                    }}
                  >
                    使用备用时间
                  </Button>
                )}
                <Button
                  variant="text"
                  size="sm"
                  onClick={() => {
                    setAcceptedFocus(`${id}|${searchParams}`);
                    seekTo(0, false);
                  }}
                >
                  从头观看
                </Button>
              </div>
            )}
            <div role="status" className="py-1 text-meta text-muted" data-testid="watch-status">
              {mediaError ||
                (mediaState === "loading"
                  ? "正在加载媒体…"
                  : mediaState === "buffering"
                    ? "正在缓冲…"
                    : mediaState === "ended"
                      ? "播放已结束，可以重看或返回"
                      : "")}
              {mediaError && (
                <>
                  <Button variant="text" size="sm" onClick={retry}>
                    重试媒体
                  </Button>
                  <Button variant="text" size="sm" onClick={back.go}>
                    {back.label}
                  </Button>
                </>
              )}
              {saveState === "saving" && " 正在保存位置…"}
              {saveState === "error" && " 位置保存失败，网络恢复后将重试"}
              {!video.subtitles.length && " 本段暂无字幕，可以继续观看"}
              {temporaryMode !== null && " 本次已减少辅助；视频内嵌文字不受站内开关控制"}
            </div>
          </div>

          {/* 移动端动作行（#24/#28 乙）已并入 ⋯ 面板（DEC-069 第 6 条）：首屏不再有它。 */}
          {/* 来源声明（ICP 合规）也已并入 ⋯ 面板：原视频来源 + 版权声明。 */}
        </div>

        {!isMobile && split && !immersive && (
          <WatchDivider split={split} onChange={setLeftPanelWidth} />
        )}
        <aside
          id="watch-transcript"
          data-testid="watch-transcript"
          hidden={immersive}
          className="watch-transcript bg-canvas border border-hairline rounded-lg overflow-hidden min-w-0"
        >
          <div className="flex shrink-0 items-center justify-between gap-3 border-b border-hairline px-3 py-2">
            <div className="min-w-0">
              <h2 className="text-copy font-bold text-ink">文稿</h2>
              <p className="text-caption text-muted">{video.subtitles.length} 句 · 整段</p>
            </div>
            <div className="flex shrink-0 items-center gap-3">
              {/* 右栏文稿是跟随播放的窄列表；通读整段、按考试词定位在文档视图里
                      更顺手。带上 id 过去，文稿页的「回到视频」才能按 from=transcript
                      回到本页（而不是丢回首页）。 */}
              <Link
                href={`/watch/${id}/transcript`}
                className="inline-flex items-center gap-0.5 whitespace-nowrap text-caption font-semibold text-brand-700 transition-colors hover:text-brand-800"
              >
                <FileText size={13} aria-hidden />
                看全文
              </Link>
              <label className="flex min-h-11 shrink-0 cursor-pointer select-none items-center gap-1.5 px-1 text-caption text-muted">
                <input
                  type="checkbox"
                  checked={followEnabled}
                  onChange={(e) => setFollowEnabled(e.target.checked)}
                  className="h-3.5 w-3.5 accent-brand-500"
                />
                跟随
              </label>
            </div>
          </div>
          {/* 字幕列表 —— 隐藏模式时提示，其余按模式渲染 */}
          {subtitleMode === "hidden" ? (
            <div className="p-8 text-center text-meta text-muted">
              字幕已关闭，按 S 键或控制条切换显示模式
            </div>
          ) : (
            <div
              ref={subtitleListRef}
              data-coach="subtitles"
              className={cn("subtitle-scroll", isMobile ? "pt-1" : "min-h-0 overflow-y-auto p-1.5")}
            >
              <div className="flex flex-col gap-0.5">
                {video.subtitles.map((sub, i) => (
                  <button
                    key={sub.id}
                    id={`subtitle-${i}`}
                    aria-current={i === currentSubtitleIndex ? "true" : undefined}
                    onClick={() => {
                      resumeFollow(); // 点文稿行是显式导航：恢复跟随
                      setCurrentSubtitleIndex(i);
                      seekTo(sub.start_time);
                    }}
                    className={cn(
                      "flex w-full items-start gap-2 rounded-lg border-l-[3px] border-transparent cursor-pointer text-left transition-colors duration-100 hover:bg-surface-soft p-3",
                      // R5（DEC-070 定案②）：当前项用淡蓝底 + 3px 蓝色左竖线，
                      // 文字回到 ink；「正在读的那一句」的唯一强调色留给当前句卡。
                      i === currentSubtitleIndex && "bg-brand-50 border-l-brand-500"
                    )}
                  >
                    <span className="min-w-0 flex-1">
                      {subtitleMode !== "chinese" && (
                        // 橙色只留给字幕带：当前项不再染 `text-brand-500`（DEC-070 定案②）。
                        <div className="font-medium text-copy leading-relaxed text-ink">
                          {sub.text_en.split(" ").map((word, wi) => (
                            <span key={wi} className={levelClassFor(word, sub.word_levels)}>
                              {word}{" "}
                            </span>
                          ))}
                        </div>
                      )}
                      {(subtitleMode === "bilingual" || subtitleMode === "chinese") &&
                        sub.text_zh && (
                          <div className="text-muted mt-0.5 text-meta">{sub.text_zh}</div>
                        )}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </aside>
      </div>

      <WatchSourceCard video={{ ...video, favorite_count: favoriteCount }} />
      <details open className="mt-4 border-t border-hairline py-3">
        <summary className="cursor-pointer text-copy font-semibold text-ink">视频信息</summary>
        <div className="mt-3 space-y-3">
          {video.description?.trim() && (
            <p className="whitespace-pre-line break-words text-copy leading-relaxed text-body">
              {video.description}
            </p>
          )}
          {video.source_url && (
            <a
              href={video.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block text-meta text-brand-700"
            >
              查看原始来源 ↗
            </a>
          )}
          <VideoStats
            likeCount={likeCount}
            viewCount={video.view_count}
            favoriteCount={favoriteCount}
          />
          <LearningActions
            compact={isMobile}
            vocabSet={vocabSet}
            addingVocabSet={addingVocabSet}
            onVocabSet={addVocabSet}
            onDrill={() => router.push("/vocabulary")}
          />
        </div>
      </details>
      <PublishedVideoEditorial key={video.id} video={video} />
      <RelatedVideos videoId={video.id} />

      <section
        aria-label="接着看"
        className="mt-6 flex flex-wrap items-center gap-3 border-t border-hairline pt-4"
      >
        <Button onClick={() => router.push("/#feed")}>继续选片</Button>
        <Button variant="text" onClick={() => router.push("/vocabulary")}>
          复习已保存的词
        </Button>
      </section>

      {/* Word tooltip overlay —— 桌面：可拖动浮动卡；移动端：贴画面下沿升起的浮层（#27 决议乙） */}
      {selectedWord && (
        <div data-coach="word-card">
          {isMobile || immersive ? (
            <WordCardSheet
              key={selectedWord}
              anchorRef={slotRef}
              word={selectedWord}
              gloss={wordGloss}
              onClose={closeWordCard}
              onPronounce={() => speakWord(selectedWord)}
              onSave={handleSaveWord}
              sourceLabel={wordSourceLabel}
              onRevealSource={revealWordSource}
              lookupError={lookupError}
              enrichmentError={enrichmentError}
              onRetry={retryLookup}
              onReplay={() => handleReplay()}
              onReduceReplay={() => handleReplay(true)}
            />
          ) : (
            <WordTooltipInline
              key={selectedWord}
              word={selectedWord}
              gloss={wordGloss}
              onClose={closeWordCard}
              onPronounce={() => speakWord(selectedWord)}
              onSave={handleSaveWord}
              anchorRect={wordAnchorRect}
              sourceLabel={wordSourceLabel}
              onRevealSource={revealWordSource}
              lookupError={lookupError}
              enrichmentError={enrichmentError}
              onRetry={retryLookup}
              onReplay={() => handleReplay()}
              onReduceReplay={() => handleReplay(true)}
            />
          )}
        </div>
      )}

      {/* 手机设置、次要学习操作与笔记集中在同一张抽屉。 */}
      <WatchMoreSheet
        triggerRef={moreTriggerRef}
        open={moreOpen}
        onClose={() => setMoreOpen(false)}
        subtitleMode={subtitleMode}
        onSubtitleModeChange={setSubtitleMode}
        fontSize={subtitleFontSize}
        onFontSizeChange={handleFontSizeChange}
        rates={PLAYBACK_RATES}
        rate={rate}
        onRateChange={setRate}
        sourceUrl={video.source_url ?? null}
        extra={isMobile && noteOpen ? notesPanel : undefined}
        actions={
          <div className="space-y-3">
            {isMobile && (
              <>
                <div data-testid="sentence-actions" className="flex flex-wrap gap-2">
                  {learningPlaybackActions}
                </div>
                <VideoActions
                  compact
                  isLiked={isLiked}
                  likeCount={likeCount}
                  isFavorited={isFavorited}
                  noteOpen={noteOpen}
                  onToggleLike={toggleLike}
                  onToggleFavorite={toggleFavorite}
                  onNotes={() => setNoteOpen((v) => !v)}
                />
              </>
            )}
            <LearningActions
              compact
              vocabSet={vocabSet}
              addingVocabSet={addingVocabSet}
              onVocabSet={addVocabSet}
              onDrill={() => router.push("/vocabulary")}
            />
          </div>
        }
      />
    </div>
  );

  return (
    <ViewTransition enter="page-in" exit="page-out" default="none">
      {page}
    </ViewTransition>
  );
}
