"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import {
  mediaStateFor,
  youTubeEventFor,
  type MediaFacts,
  type MediaLifecycleEvent,
} from "@/lib/mediaLifecycle";
import {
  createYouTubePlayer as mountYouTubePlayer,
  destroyYouTubePlayer,
  ensureYouTubeApi,
  type YTPlayerInstance,
} from "@/lib/youtubePlayer";
import { SUBTITLE_MODE_ORDER } from "@/lib/subtitleModes";
import { useWatchStore, type SubtitleMode } from "@/stores/watchStore";
import { WatchSession, validInterval } from "@/lib/watchSession";
import { WatchProgressQueue, type ProgressSaveState } from "@/lib/watchProgressQueue";
import type { VideoDetail } from "@/types";

export type PlaybackMode = "ready" | "processing" | "loading" | "error" | "offline";

// D1 播放器控制条：倍速档位与持久化（产品设计规划 §D1）。
export const PLAYBACK_RATES = [0.5, 0.75, 1, 1.25, 1.5, 2];
const RATE_STORAGE_KEY = "seeword_playback_rate";

function loadPersistedRate(): number {
  if (typeof window === "undefined") return 1;
  const saved = Number(window.localStorage.getItem(RATE_STORAGE_KEY));
  return PLAYBACK_RATES.includes(saved) ? saved : 1;
}

/** Pick the best available video URL (1080p > 720p > 480p). */
export function bestVideoUrl(v: VideoDetail): string | null {
  return v.video_url_1080p || v.video_url_720p || v.video_url_480p || null;
}

/** Extract YouTube video ID from a URL. */
export function youtubeId(v: VideoDetail): string | null {
  const m = v.source_url?.match(
    /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/shorts\/)([A-Za-z0-9_-]{11})/
  );
  return m ? m[1] : null;
}

/** Whether the video can be played (local file or YouTube embed). */
export function canPlay(v: VideoDetail): boolean {
  return !!bestVideoUrl(v) || !!youtubeId(v);
}

/**
 * iOS 设备检测（iPhone/iPad/iPod）。iPadOS 13+ 的 Safari UA 伪装成 Mac，
 * 需用 maxTouchPoints 兜底。用于 iOS 专属的播放器兼容路径（如 seek 防御）。
 */
function isIOS(): boolean {
  if (typeof navigator === "undefined") return false;
  return (
    /iPad|iPhone|iPod/.test(navigator.userAgent) ||
    (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1)
  );
}

interface UseVideoPlayerOptions {
  onPreviousSentence?: () => void;
  onNextSentence?: () => void;
  onReplaySentence?: () => void;
  onToggleImmersive?: () => void;
  onExitImmersive?: () => void;
  playbackRange?: { start: number; end: number; onEnd: () => void } | null;
  playbackBlocked?: boolean;
  videoId: string;
  /** Playback-time tick (HTML5 timeupdate / YouTube poll) for subtitle sync. */
  onTimeTick?: (time: number) => void;
  hasExplicitFocus?: boolean;
  subtitleModeOverride?: SubtitleMode;
  onUserIntent?: (clearAid: boolean) => void;
}

interface UseVideoPlayerReturn {
  video: VideoDetail | null;
  playbackMode: PlaybackMode;
  currentSubtitleIndex: number;
  setCurrentSubtitleIndex: (idx: number) => void;
  videoRef: React.RefObject<HTMLVideoElement>;
  /** Container element for the YouTube IFrame player (rendered when isYtMode). */
  ytContainerRef: React.RefObject<HTMLDivElement>;
  /** Whether the current video plays via YouTube IFrame (no local file). */
  isYtMode: boolean;
  /** 是否正在播放（原生事件快速路径 + 播放时钟轮询校正的单一事实源）。 */
  isPlaying: boolean;
  mediaState: "loading" | "buffering" | "paused" | "playing" | "ended" | "error";
  mediaError: string | null;
  saveState: ProgressSaveState;
  currentTime: () => number;
  pauseForHelp: () => void;
  closeHelp: (resume?: boolean) => void;
  replaySentence: (start: number, end: number) => boolean;
  isDesktop: boolean;
  play: () => void;
  togglePlayPause: () => void;
  seekBy: (delta: number) => void;
  seekTo: (time: number, playAfterSeek?: boolean) => void;
  navigateSubtitle: (delta: number) => void;
  retry: () => void;
  // ── D1 控制条能力 ─────────────────────────────────────────────
  /** 当前倍速（持久化到 localStorage）。 */
  rate: number;
  setRate: (rate: number) => void;
  cycleRate: () => void;
  /** 音量 0-1（HTML5）；YT 模式映射到 0-100。 */
  setVolume: (v: number) => void;
  muted: boolean;
  toggleMute: () => void;
  /** S 键：字幕显示模式循环（双语/英/中/隐藏）。 */
  cycleSubtitleMode: () => void;
  /** 全屏目标容器（watch 页把播放器外壳赋给它）；F 键切换。 */
  fullscreenElRef: React.MutableRefObject<HTMLElement | null>;
  toggleFullscreen: () => void;
}

/**
 * Hook for video playback state and controls on the watch page.
 *
 * Two playback backends:
 *  - HTML5 <video> when a local file exists (video_url_*).
 *  - YouTube IFrame (YT.Player) when the video is routed to YouTube and has
 *    no local file. The IFrame player is controlled via the official IFrame
 *    API (postMessage under the hood), which makes seekTo work — clicking a
 *    subtitle in the right panel now jumps the YouTube video too.
 */
export function useVideoPlayer({
  onPreviousSentence,
  onNextSentence,
  onReplaySentence,
  onToggleImmersive,
  onExitImmersive,
  playbackRange = null,
  playbackBlocked = false,
  videoId,
  onTimeTick,
  hasExplicitFocus = false,
  subtitleModeOverride,
  onUserIntent,
}: UseVideoPlayerOptions): UseVideoPlayerReturn {
  const sessionRef = useRef(new WatchSession());
  const boundsRef = useRef({ playbackRange, playbackBlocked });
  useEffect(() => {
    boundsRef.current = { playbackRange, playbackBlocked };
  }, [playbackRange, playbackBlocked]);
  const intentCallbackRef = useRef(onUserIntent);
  const captionModeRef = useRef(subtitleModeOverride);
  useEffect(() => {
    intentCallbackRef.current = onUserIntent;
    captionModeRef.current = subtitleModeOverride;
  }, [onUserIntent, subtitleModeOverride]);
  const [mediaState, setMediaState] = useState<UseVideoPlayerReturn["mediaState"]>("loading");
  const [mediaError, setMediaError] = useState<string | null>(null);
  const [saveState, setSaveState] = useState<ProgressSaveState>("idle");
  const progressRef = useRef<WatchProgressQueue | null>(null);
  const positionTouchedRef = useRef(false);
  const expectedSeekRef = useRef<number | null>(null);
  const seekRevisionRef = useRef(0);
  const nativeSeekAppliedRef = useRef(false);
  const seekRetryRef = useRef(false);
  const pendingPlayRef = useRef(false);
  const playRequestRef = useRef(0);
  const videoRef = useRef<HTMLVideoElement>(null!);
  const ytContainerRef = useRef<HTMLDivElement>(null!);
  const ytPlayerRef = useRef<YTPlayerInstance | null>(null);
  const ytReadyRef = useRef(false);
  const ytPlayingRef = useRef(false);
  const mountedYtIdRef = useRef<string | null>(null);
  const ytTargetIdRef = useRef<string | null>(null);
  const pendingYtSeekRef = useRef<{ time: number; playAfterSeek: boolean } | null>(null);

  const [video, setVideo] = useState<VideoDetail | null>(null);
  const [playbackMode, setPlaybackMode] = useState<PlaybackMode>("loading");
  const [currentSubtitleIndex, setCurrentSubtitleIndex] = useState(0);
  const [isDesktop, setIsDesktop] = useState(false);
  const [isYtMode, setIsYtMode] = useState(false);
  /** 是否正在播放 —— 单一事实源：原生事件做快速路径，播放时钟轮询校正。
   *  iOS Safari 会发伪 pause 事件、可能漏发 playing 事件，轮询保证最终一致。 */
  const [isPlaying, setIsPlaying] = useState(false);

  // ── D1 控制条状态 ──────────────────────────────────────────────
  const [rate, setRateState] = useState<number>(loadPersistedRate);
  const [muted, setMuted] = useState(false);
  const mutedRef = useRef(false);
  const rateRef = useRef(rate);
  useEffect(() => {
    rateRef.current = rate;
  }, [rate]);
  // 全屏目标：watch 页把播放器外壳节点赋给此 ref（F 键切换）。
  const fullscreenElRef = useRef<HTMLElement | null>(null);

  // Keep a ref in sync so callbacks (navigateSubtitle) can read the latest
  // video data without stale closures or putting side effects in updaters.
  const videoDataRef = useRef<VideoDetail | null>(null);
  useEffect(() => {
    videoDataRef.current = video;
  }, [video]);

  // Mirrors currentSubtitleIndex so navigateSubtitle can compute the next
  // index synchronously — React never runs a setState updater synchronously,
  // so reading a value written inside one would always see the stale index.
  const currentSubtitleIndexRef = useRef(0);
  useEffect(() => {
    currentSubtitleIndexRef.current = currentSubtitleIndex;
  }, [currentSubtitleIndex]);

  const onTimeTickRef = useRef(onTimeTick);
  useEffect(() => {
    onTimeTickRef.current = onTimeTick;
  }, [onTimeTick]);

  /**
   * 播放生命周期 → 媒体 UI 状态。原生 `<video>` 与 YouTube IFrame 的事件名
   * 不同，但都先翻译成 `lib/mediaLifecycle` 的共同事件，再共用同一张映射表，
   * 避免两条后端各写一份三元表达式后悄悄分叉。
   */
  const applyMediaEvent = useCallback((event: MediaLifecycleEvent, facts: MediaFacts) => {
    const next = mediaStateFor(event, facts);
    if (next) setMediaState(next);
  }, []);

  const rawPause = useCallback(() => {
    playRequestRef.current++;
    pendingPlayRef.current = false;
    if (pendingYtSeekRef.current) pendingYtSeekRef.current.playAfterSeek = false;
    videoRef.current?.pause();
    ytPlayerRef.current?.pauseVideo();
  }, []);
  const rawPlay = useCallback(() => {
    if (sessionRef.current.helpOpen) return;
    const { playbackBlocked: blocked, playbackRange: bounds } = boundsRef.current;
    if (blocked) return;
    const position =
      expectedSeekRef.current ??
      videoRef.current?.currentTime ??
      ytPlayerRef.current?.getCurrentTime() ??
      0;
    if (bounds && position >= bounds.end) {
      bounds.onEnd();
      return;
    }
    if (bounds && position < bounds.start - 0.1) return;
    const request = ++playRequestRef.current;
    const revision = sessionRef.current.revision;
    const el = videoRef.current;
    pendingPlayRef.current = true;
    if (pendingYtSeekRef.current) pendingYtSeekRef.current.playAfterSeek = true;
    window.speechSynthesis?.cancel();
    setMediaError(null);
    if (el)
      void el.play().catch(() => {
        if (
          request !== playRequestRef.current ||
          revision !== sessionRef.current.revision ||
          el !== videoRef.current
        )
          return;
        setIsPlaying(false);
        setMediaState("paused");
        setMediaError("播放未能开始，请点击播放重试");
      });
    else if (ytReadyRef.current) ytPlayerRef.current?.playVideo();
  }, []);
  const markIntent = useCallback((clearRange = true, preservePosition = false) => {
    sessionRef.current.command(clearRange);
    if (!preservePosition) {
      seekRevisionRef.current++;
      pendingYtSeekRef.current = null;
      expectedSeekRef.current = null;
      nativeSeekAppliedRef.current = false;
      seekRetryRef.current = false;
    }
    intentCallbackRef.current?.(clearRange);
  }, []);
  useEffect(() => {
    const session = sessionRef.current;
    const seekRevision = seekRevisionRef;
    session.command();
    seekRevision.current++;
    positionTouchedRef.current = false;
    expectedSeekRef.current = null;
    setMediaState("loading");
    setMediaError(null);
    setSaveState("idle");
    return () => {
      session.command();
      seekRevision.current++;
    };
  }, [videoId]);

  // Detect desktop layout
  useEffect(() => {
    const mql = window.matchMedia("(min-width: 1024px)");
    const check = (e: MediaQueryListEvent | MediaQueryList) => setIsDesktop(e.matches);
    check(mql);
    mql.addEventListener("change", check);
    return () => mql.removeEventListener("change", check);
  }, []);

  // Load video data
  const loadRequestRef = useRef(0);
  const loadVideo = useCallback(() => {
    const request = ++loadRequestRef.current;
    sessionRef.current.command();
    setVideo(null);
    setCurrentSubtitleIndex(0);
    setPlaybackMode("loading");
    api<VideoDetail>(`/api/v1/videos/${videoId}`)
      .then((v) => {
        if (request !== loadRequestRef.current) return;
        setVideo(v);
        // 已下线（需求 §5.1 offline）：媒体已删除，不再可播；字幕/学习记录保留，
        // 由 watch 页渲染「已下架」态（收藏夹与集合页入口不断链）。
        if (v.storage_mode === "offline") {
          setPlaybackMode("offline");
          return;
        }
        // 登录墙之外的匿名响应不含字幕/媒体 URL，canPlay 会拦住。
        if (v.status === "ready" && canPlay(v)) setPlaybackMode("ready");
        else if (v.status === "ready_subtitles" || v.status === "processing")
          setPlaybackMode("processing");
        else setPlaybackMode("loading");
      })
      .catch(() => {
        if (request !== loadRequestRef.current) return;
        setPlaybackMode("error");
        toast.error("加载视频失败");
      });
  }, [videoId]);

  const cancelLoad = useCallback(() => {
    loadRequestRef.current++;
  }, []);
  useEffect(() => {
    loadVideo();
    return cancelLoad;
  }, [loadVideo, cancelLoad]);

  // Poll for video status when processing
  useEffect(() => {
    if (!video || (video.status !== "processing" && video.status !== "ready_subtitles")) return;
    let active = true;
    const interval = setInterval(async () => {
      try {
        const updated = await api<VideoDetail>(`/api/v1/videos/${videoId}`);
        if (!active) return;
        setVideo(updated);
        if (updated.status === "ready" && canPlay(updated)) setPlaybackMode("ready");
        else if (updated.status === "ready_subtitles" || updated.status === "processing")
          setPlaybackMode("processing");
        else if (updated.status === "error") {
          setPlaybackMode("error");
          toast.error("视频处理失败");
        }
      } catch {
        /* ignore polling errors */
      }
    }, 3000);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, [video, videoId]);

  // ---------------------------------------------------------------------------
  // YouTube IFrame player (fallback when no local file)
  // ---------------------------------------------------------------------------

  // 脚本加载与播放器创建/销毁在 lib/youtubePlayer.ts，这里只接回调与状态。
  const createYouTubePlayer = useCallback(
    (ytId: string): boolean => {
      ytReadyRef.current = false;
      ytPlayingRef.current = false;
      const player = mountYouTubePlayer(ytContainerRef.current, ytId, {
        onReady: () => {
          ytReadyRef.current = true;
          setMediaState("paused");
          const pendingSeek = pendingYtSeekRef.current;
          const ready = ytPlayerRef.current;
          if (pendingSeek && ready?.seekTo) {
            pendingYtSeekRef.current = null;
            ready.seekTo(pendingSeek.time, true);
            if (pendingSeek.playAfterSeek) ready.playVideo();
          }
        },
        onStateChange: (e: { data?: number }) => {
          // 1 = playing, 2 = paused, 3 = buffering, 0 = ended
          if (e?.data === 1) {
            window.speechSynthesis?.cancel();
            positionTouchedRef.current = true;
          }
          applyMediaEvent(youTubeEventFor(e.data), {
            // 3（buffering）按「未暂停」处理，否则会被 waiting 规则当成预取忽略。
            paused: e.data !== 1 && e.data !== 3,
            ended: e.data === 0,
          });
          ytPlayingRef.current = e?.data === 1;
          setIsPlaying(e?.data === 1);
          if (e?.data === 2) {
            // Surface the final position once when pausing (time ticks keep
            // running so subtitle highlight stays in sync during pause too).
            onTimeTickRef.current?.(ytPlayerRef.current?.getCurrentTime?.() ?? 0);
            if (positionTouchedRef.current)
              progressRef.current?.enqueue(ytPlayerRef.current?.getCurrentTime?.() ?? 0);
          }
        },
        onError: () => {
          sessionRef.current.command();
          setMediaState("error");
          setMediaError("视频暂时无法播放，请重试或返回来源");
        },
      });
      if (!player) return false;
      ytPlayerRef.current = player;
      return true;
    },
    [applyMediaEvent]
  );

  /** Mount the YouTube IFrame player into ytContainerRef (idempotent per video). */
  const mountYouTube = useCallback(
    (ytId: string) => {
      if (mountedYtIdRef.current === ytId) return;
      ytTargetIdRef.current = ytId;
      ensureYouTubeApi().then(() => {
        // 目标已改（切换视频/卸载），或已被更早的等待者创建：放弃这次创建。
        if (ytTargetIdRef.current !== ytId || mountedYtIdRef.current === ytId) return;
        // 容器尚未渲染时创建失败，不记录 id，留待下一次 effect 重试。
        if (createYouTubePlayer(ytId)) mountedYtIdRef.current = ytId;
      });
    },
    [createYouTubePlayer]
  );

  const destroyYouTube = useCallback(() => {
    destroyYouTubePlayer(ytPlayerRef.current);
    ytPlayerRef.current = null;
    ytReadyRef.current = false;
    ytPlayingRef.current = false;
    mountedYtIdRef.current = null;
    ytTargetIdRef.current = null;
  }, []);

  // Derive the playback backend from the loaded video. When a local file
  // exists we prefer HTML5; otherwise fall back to the YouTube IFrame.
  // isYtMode 也必须在依赖里：容器只在它为真时渲染，第一次尝试可能早于
  // 容器挂载，需要在容器就位后的这次运行里重试。
  useEffect(() => {
    if (playbackMode !== "ready" || !video) {
      setIsYtMode(false);
      destroyYouTube();
      return;
    }
    const yt = youtubeId(video);
    const useYt = !!yt && !bestVideoUrl(video);
    setIsYtMode(useYt);
    if (useYt && yt) mountYouTube(yt);
    else destroyYouTube();
  }, [playbackMode, video, mountYouTube, destroyYouTube, isYtMode]);

  // YouTube time poll: keeps the subtitle highlight + watch-time tracking in
  // sync while the IFrame plays (IFrame has no timeupdate DOM events).
  useEffect(() => {
    if (!isYtMode) return;
    const interval = setInterval(() => {
      const p = ytPlayerRef.current;
      if (!p || !ytReadyRef.current || typeof p.getCurrentTime !== "function") return;
      onTimeTickRef.current?.(p.getCurrentTime() ?? 0);
    }, 250);
    return () => clearInterval(interval);
  }, [isYtMode]);

  // ---------------------------------------------------------------------------
  // HTML5 playback clock: native events as the fast path + a 250ms poll as the
  // authoritative source. iOS Safari 的媒体事件不可靠——timeupdate 可能停发、
  // play() 后会出现伪 pause 事件——轮询保证字幕同步与播放态最终一致；
  // desktop 上事件正常时轮询只是静默校正（同值 setState 不触发重渲染）。
  // ---------------------------------------------------------------------------
  useEffect(() => {
    if (playbackMode !== "ready" || isYtMode) return;
    const el = videoRef.current;
    if (!el) return;

    const onPlay = () => {
      window.speechSynthesis?.cancel();
      positionTouchedRef.current = true;
      setIsPlaying(true);
      applyMediaEvent("play", { paused: el.paused, ended: el.ended });
      setMediaError(null);
    };
    const onPause = () => {
      setIsPlaying(false);
      applyMediaEvent("pause", { paused: true, ended: el.ended });
      if (positionTouchedRef.current && expectedSeekRef.current === null)
        progressRef.current?.enqueue(el.currentTime);
    };
    const onReady = () => {
      applyMediaEvent("ready", { paused: el.paused, ended: el.ended });
      setMediaError(null);
    };
    const onWaiting = () => {
      applyMediaEvent("waiting", { paused: el.paused, ended: el.ended });
    };
    const onError = () => {
      sessionRef.current.command();
      applyMediaEvent("error", { paused: el.paused, ended: el.ended });
      setMediaError("媒体加载失败，请重试或返回来源");
    };
    const onSeeking = () => {
      positionTouchedRef.current = true;
      if (expectedSeekRef.current !== null) return;
      markIntent();
    };
    const onSeeked = () => {
      const target = expectedSeekRef.current;
      if (target !== null && !nativeSeekAppliedRef.current) return;
      if (target !== null && Math.abs(el.currentTime - target) > 0.25) {
        if (isIOS() && !seekRetryRef.current) {
          seekRetryRef.current = true;
          const revision = seekRevisionRef.current;
          requestAnimationFrame(() => {
            if (seekRevisionRef.current !== revision) return;
            el.currentTime = target;
            if (pendingPlayRef.current) rawPlay();
          });
          return;
        }
        setMediaError("句子定位未完成，请重新选择目标句");
        sessionRef.current.command();
      }
      if (target !== null && Math.abs(el.currentTime - target) <= 0.25)
        sessionRef.current.confirmSeek(el.currentTime);
      expectedSeekRef.current = null;
      onTimeTickRef.current?.(el.currentTime);
    };
    const listeners = {
      playing: onPlay,
      canplay: onReady,
      loadedmetadata: onReady,
      waiting: onWaiting,
      stalled: onWaiting,
      error: onError,
      seeking: onSeeking,
      seeked: onSeeked,
      ended: onPause,
    };
    for (const [name, fn] of Object.entries(listeners)) el.addEventListener(name, fn);
    if (el.readyState >= 2) onReady();
    el.addEventListener("play", onPlay);
    el.addEventListener("pause", onPause);
    // 初始同步：例如从保存进度恢复、或元素重建后的事件兜底。
    setIsPlaying(!el.paused);

    const interval = setInterval(() => {
      const v = videoRef.current;
      if (!v) return;
      const t = v.currentTime;
      if (Number.isFinite(t) && expectedSeekRef.current === null) onTimeTickRef.current?.(t);
      setIsPlaying(!v.paused);
    }, 250);
    return () => {
      el.removeEventListener("play", onPlay);
      el.removeEventListener("pause", onPause);
      for (const [name, fn] of Object.entries(listeners)) el.removeEventListener(name, fn);
      clearInterval(interval);
    };
  }, [playbackMode, isYtMode, markIntent, rawPlay, applyMediaEvent]);

  // Clean up the IFrame player on unmount.
  useEffect(() => {
    return () => destroyYouTube();
  }, [destroyYouTube]);

  // ---------------------------------------------------------------------------
  // Unified playback controls (both backends)
  // ---------------------------------------------------------------------------

  const currentTime = useCallback((): number => {
    if (videoRef.current && Number.isFinite(videoRef.current.currentTime))
      return videoRef.current.currentTime;
    if (ytReadyRef.current && ytPlayerRef.current?.getCurrentTime)
      return ytPlayerRef.current.getCurrentTime() ?? 0;
    return 0;
  }, []);

  const play = useCallback(() => {
    markIntent(true, true);
    rawPlay();
  }, [markIntent, rawPlay]);
  const togglePlayPause = useCallback(() => {
    const playing = videoRef.current ? !videoRef.current.paused : ytPlayingRef.current;
    markIntent(!playing, true);
    if (playing) rawPause();
    else rawPlay();
  }, [markIntent, rawPause, rawPlay]);

  const seekTo = useCallback(
    (time: number, playAfterSeek = true) => {
      if (!Number.isFinite(time) || time < 0) return;
      const bounds = boundsRef.current.playbackRange;
      if (bounds) time = Math.max(bounds.start, Math.min(time, bounds.end));
      markIntent();
      positionTouchedRef.current = true;
      const revision = seekRevisionRef.current;
      pendingPlayRef.current = playAfterSeek;
      expectedSeekRef.current = time;
      const el = videoRef.current;
      if (el) {
        const apply = () => {
          if (seekRevisionRef.current !== revision) return;
          const t = Number.isFinite(el.duration) ? Math.min(time, el.duration) : time;
          expectedSeekRef.current = t;
          nativeSeekAppliedRef.current = true;
          if (isIOS() || !pendingPlayRef.current) el.pause();
          if (Math.abs(el.currentTime - t) < 0.01 && !el.seeking) {
            expectedSeekRef.current = null;
          } else el.currentTime = t;
          if (pendingPlayRef.current) rawPlay();
        };
        if (el.readyState >= (isIOS() ? 2 : 1)) apply();
        else {
          const cleanup = () => {
            el.removeEventListener("loadedmetadata", ready);
            el.removeEventListener("canplay", ready);
            el.removeEventListener("error", cleanup);
          };
          const ready = (event?: Event) => {
            if (isIOS() && event?.type === "loadedmetadata") return;
            if (el.readyState < (isIOS() ? 2 : 1)) return;
            cleanup();
            // Leave the initial media event stack before seeking: WebKit may
            // otherwise finish its initial position reset after our assignment.
            requestAnimationFrame(apply);
          };
          el.addEventListener("loadedmetadata", ready);
          el.addEventListener("canplay", ready);
          el.addEventListener("error", cleanup, { once: true });
        }
      } else if (ytReadyRef.current && ytPlayerRef.current) {
        expectedSeekRef.current = time;
        ytPlayerRef.current.seekTo(time, true);
        if (playAfterSeek) rawPlay();
        else rawPause();
      } else pendingYtSeekRef.current = { time, playAfterSeek };
    },
    [markIntent, rawPlay, rawPause]
  );

  const seekBy = useCallback(
    (delta: number) => {
      seekTo(
        Math.max(0, currentTime() + delta),
        videoRef.current ? !videoRef.current.paused : ytPlayingRef.current
      );
    },
    [seekTo, currentTime]
  );
  const pauseForHelp = useCallback(() => {
    sessionRef.current.openHelp(videoRef.current ? !videoRef.current.paused : ytPlayingRef.current);
    rawPause();
  }, [rawPause]);
  const closeHelp = useCallback(
    (resume = true) => {
      const shouldResume = sessionRef.current.closeHelp();
      if (resume && shouldResume) rawPlay();
    },
    [rawPlay]
  );
  const replaySentence = useCallback(
    (start: number, end: number) => {
      const duration = videoRef.current?.duration || videoDataRef.current?.duration;
      if (!validInterval(start, end, duration)) {
        setMediaError("本段暂无可用句子定位");
        return false;
      }
      seekTo(start);
      sessionRef.current.range = { start, end, armed: false };
      if (expectedSeekRef.current === null) sessionRef.current.confirmSeek(currentTime());
      return true;
    },
    [seekTo, currentTime]
  );

  // A separate fast boundary clock prevents the 250ms subtitle clock cutting into the next sentence.
  useEffect(() => {
    const timer = setInterval(() => {
      const time = currentTime();
      const target = expectedSeekRef.current;
      if (target !== null) {
        const el = videoRef.current;
        if (!el && ytReadyRef.current && Math.abs(time - target) <= 0.25) {
          sessionRef.current.confirmSeek(time);
          expectedSeekRef.current = null;
        } else return;
      }
      const playing = videoRef.current ? !videoRef.current.paused : ytPlayingRef.current;
      const { playbackRange: bounds, playbackBlocked: blocked } = boundsRef.current;
      if (blocked && playing) {
        rawPause();
        return;
      }
      if (bounds && playing && time >= bounds.end) {
        rawPause();
        bounds.onEnd();
        return;
      }
      if (sessionRef.current.shouldStop(time, playing)) rawPause();
    }, 40);
    return () => clearInterval(timer);
  }, [currentTime, rawPause]);

  const navigateSubtitle = useCallback(
    (delta: number) => {
      const vd = videoDataRef.current;
      if (!vd?.subtitles?.length) return;
      // Compute the target index from the ref (not from inside a setState
      // updater — updaters run asynchronously, so a value written there would
      // not be readable by the seekTo below).
      const newIndex = Math.max(
        0,
        Math.min(vd.subtitles.length - 1, currentSubtitleIndexRef.current + delta)
      );
      if (newIndex === currentSubtitleIndexRef.current) return;
      const bounds = boundsRef.current.playbackRange;
      if (
        bounds &&
        (vd.subtitles[newIndex].start_time < bounds.start ||
          vd.subtitles[newIndex].start_time >= bounds.end)
      )
        return;
      currentSubtitleIndexRef.current = newIndex;
      setCurrentSubtitleIndex(newIndex);
      seekTo(vd.subtitles[newIndex].start_time);
    },
    [seekTo]
  );

  // ---------------------------------------------------------------------------
  // D1 控制条能力：倍速 / 音量 / 静音 / 字幕模式 / 全屏（双后端）
  // ---------------------------------------------------------------------------

  const setRate = useCallback((next: number) => {
    if (!PLAYBACK_RATES.includes(next)) return;
    setRateState(next);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(RATE_STORAGE_KEY, String(next));
    }
    if (videoRef.current) videoRef.current.playbackRate = next;
    ytPlayerRef.current?.setPlaybackRate?.(next);
  }, []);

  const cycleRate = useCallback(() => {
    const idx = PLAYBACK_RATES.indexOf(rateRef.current);
    const next = PLAYBACK_RATES[(idx + 1) % PLAYBACK_RATES.length];
    setRate(next);
  }, [setRate]);

  // ready 后（含切换视频）把持久化倍速应用到 HTML5 元素。
  useEffect(() => {
    if (playbackMode !== "ready" || isYtMode) return;
    if (videoRef.current) videoRef.current.playbackRate = rateRef.current;
  }, [playbackMode, isYtMode, video]);

  const setVolume = useCallback((v: number) => {
    const clamped = Math.max(0, Math.min(1, v));
    if (videoRef.current) {
      videoRef.current.volume = clamped;
      if (clamped > 0 && videoRef.current.muted) {
        videoRef.current.muted = false;
        setMuted(false);
        mutedRef.current = false;
      }
    }
    ytPlayerRef.current?.setVolume?.(Math.round(clamped * 100));
  }, []);

  const toggleMute = useCallback(() => {
    const next = !mutedRef.current;
    mutedRef.current = next;
    setMuted(next);
    if (videoRef.current) videoRef.current.muted = next;
    if (next) ytPlayerRef.current?.mute?.();
    else ytPlayerRef.current?.unMute?.();
  }, []);

  const cycleSubtitleMode = useCallback(() => {
    const { subtitleMode, setSubtitleMode } = useWatchStore.getState();
    // S 键循环顺序与模式行、⋯ 面板同源（lib/subtitleModes）：双语 → 英文 → 中文 → 关闭。
    const idx = SUBTITLE_MODE_ORDER.indexOf(captionModeRef.current ?? subtitleMode);
    const next = SUBTITLE_MODE_ORDER[(idx + 1) % SUBTITLE_MODE_ORDER.length];
    setSubtitleMode(next);
  }, []);

  const toggleFullscreen = useCallback(() => {
    const el = fullscreenElRef.current;
    if (!el) return;
    if (document.fullscreenElement) {
      document.exitFullscreen().catch(() => {});
      return;
    }
    // iOS 回退：iPhone Safari 不支持 Fullscreen API，部分 WebView 只对
    // video 元素支持全屏——两种情况都落到 webkitEnterFullscreen。
    const enterIosFullscreen = () => {
      const v = videoRef.current as
        (HTMLVideoElement & { webkitEnterFullscreen?: () => void }) | null;
      v?.webkitEnterFullscreen?.();
    };
    if (typeof el.requestFullscreen === "function") {
      el.requestFullscreen().catch(enterIosFullscreen);
      return;
    }
    enterIosFullscreen();
  }, []);

  // Keyboard shortcuts (skip when focus is on interactive elements).
  // D1 统一快捷键：空格播放/暂停，←/→ 快退快进 10s，↑/↓ 音量，
  // M 静音，F 全屏，C 倍速循环，S 字幕模式循环。
  // （↑/↓ 原为字幕导航，按 §D1 改为音量；字幕导航仍可在列表中点击。）
  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if (e.defaultPrevented || e.isComposing || e.metaKey || e.ctrlKey || e.altKey) return;
      const target = e.target instanceof HTMLElement ? e.target : null;
      if (
        target?.closest(
          'input, textarea, select, [contenteditable]:not([contenteditable="false"]), [role="dialog"], [role="slider"]'
        )
      )
        return;
      if (e.key === "Escape") {
        if (
          !document.fullscreenElement &&
          !document.querySelector('[role="dialog"], [aria-modal="true"]')
        )
          onExitImmersive?.();
        return;
      }
      const action = {
        a: onPreviousSentence,
        d: onNextSentence,
        r: onReplaySentence,
        t: onToggleImmersive,
      }[e.key.toLowerCase()];
      if (action) {
        e.preventDefault();
        if (!e.repeat) action();
        return;
      }
      // Buttons keep native Space/Enter and sliders keep their arrow keys.
      if (
        target?.closest("button, a") &&
        [" ", "Enter", "ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(e.key)
      )
        return;
      switch (e.key) {
        case " ":
          e.preventDefault();
          togglePlayPause();
          break;
        case "ArrowLeft":
          seekBy(-10);
          break;
        case "ArrowRight":
          seekBy(10);
          break;
        case "ArrowUp": {
          e.preventDefault();
          const v = Math.min(1, (videoRef.current?.volume ?? 1) + 0.1);
          setVolume(v);
          break;
        }
        case "ArrowDown": {
          e.preventDefault();
          const v = Math.max(0, (videoRef.current?.volume ?? 1) - 0.1);
          setVolume(v);
          break;
        }
        case "m":
        case "M":
          toggleMute();
          break;
        case "f":
        case "F":
          toggleFullscreen();
          break;
        case "c":
        case "C":
          cycleRate();
          break;
        case "s":
        case "S":
          cycleSubtitleMode();
          break;
      }
    }
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [
    onPreviousSentence,
    onNextSentence,
    onReplaySentence,
    onToggleImmersive,
    onExitImmersive,
    togglePlayPause,
    seekBy,
    setVolume,
    toggleMute,
    toggleFullscreen,
    cycleRate,
    cycleSubtitleMode,
  ]);

  // Both backends use the same guarded restore. Explicit links own the initial position.
  useEffect(() => {
    if (playbackMode !== "ready" || hasExplicitFocus) return;
    const revision = sessionRef.current.revision;
    let cancelled = false;
    void api<{ position_seconds: number | null }>(`/api/v1/learning/progress/${videoId}`)
      .then((data) => {
        if (cancelled || revision !== sessionRef.current.revision) return;
        const pos = data.position_seconds;
        if (typeof pos === "number" && Number.isFinite(pos) && pos > 0) {
          seekTo(pos, false);
          positionTouchedRef.current = false;
        }
      })
      .catch(() => {
        /* No restore is claimed on failure. */
      });
    return () => {
      cancelled = true;
    };
  }, [playbackMode, videoId, hasExplicitFocus, seekTo]);

  useEffect(() => {
    if (playbackMode !== "ready") return;
    let active = true;
    const queue = new WatchProgressQueue(
      async (position, keepalive) => {
        await api("/api/v1/learning/progress", {
          method: "PATCH",
          keepalive,
          body: JSON.stringify({ video_id: videoId, position_seconds: position }),
        });
      },
      (state) => {
        if (active) setSaveState(state);
      }
    );
    progressRef.current = queue;
    const save = () => {
      if (positionTouchedRef.current && expectedSeekRef.current === null)
        queue.enqueue(currentTime(), true);
    };
    const interval = setInterval(save, 10000);
    const hidden = () => {
      if (document.visibilityState === "hidden") save();
    };
    window.addEventListener("pagehide", save);
    document.addEventListener("visibilitychange", hidden);
    return () => {
      save();
      active = false;
      progressRef.current = null;
      clearInterval(interval);
      window.removeEventListener("pagehide", save);
      document.removeEventListener("visibilitychange", hidden);
      // Allow a serialized final write to drain after a same-tab navigation.
      setTimeout(() => queue.dispose(), 15000);
    };
  }, [playbackMode, videoId, currentTime]);

  useEffect(() => {
    if (mediaState !== "buffering") return;
    const timer = setTimeout(() => setMediaError("缓冲时间较长，请检查网络或重试"), 12000);
    return () => clearTimeout(timer);
  }, [mediaState]);

  return {
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
    currentTime,
    pauseForHelp,
    closeHelp,
    replaySentence,
    isDesktop,
    play,
    togglePlayPause,
    seekBy,
    seekTo,
    navigateSubtitle,
    retry: () => {
      markIntent();
      loadVideo();
    },
    rate,
    setRate,
    cycleRate,
    setVolume,
    muted,
    toggleMute,
    cycleSubtitleMode,
    fullscreenElRef,
    toggleFullscreen,
  };
}
