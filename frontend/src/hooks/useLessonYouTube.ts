"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  createYouTubePlayer,
  destroyYouTubePlayer,
  ensureYouTubeApi,
  type YTPlayerInstance,
} from "@/lib/youtubePlayer";

type PlayerState = "idle" | "loading" | "paused" | "playing" | "ended" | "failed";

export function useLessonYouTube(videoId: string | null) {
  const containerRef = useRef<HTMLDivElement>(null);
  const playerRef = useRef<YTPlayerInstance | null>(null);
  const playerReady = useRef(false);
  const pendingSeek = useRef<number | null>(null);
  const [attempt, setAttempt] = useState(0);
  const [state, setState] = useState<PlayerState>("idle");
  const [position, setPosition] = useState<number | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!videoId || !attempt || !container) return;
    let active = true;
    let ready = false;
    const mount = document.createElement("div");
    container.replaceChildren(mount);

    function fail() {
      if (!active) return;
      active = false;
      ready = false;
      playerReady.current = false;
      destroyYouTubePlayer(playerRef.current);
      playerRef.current = null;
      container?.replaceChildren();
      setPosition(null);
      setState("failed");
    }

    const timeout = setTimeout(fail, 9000);
    void ensureYouTubeApi()
      .then(() => {
        if (!active) return;
        playerRef.current = createYouTubePlayer(mount, videoId, {
          onReady: () => {
            if (!active) return;
            clearTimeout(timeout);
            ready = true;
            playerReady.current = true;
            if (pendingSeek.current !== null) {
              playerRef.current?.seekTo(pendingSeek.current / 1000, true);
              pendingSeek.current = null;
            }
            setState("paused");
          },
          onStateChange: ({ data }) => {
            if (!active || !ready) return;
            setState(data === 1 ? "playing" : data === 0 ? "ended" : "paused");
          },
          onError: fail,
        });
        if (!playerRef.current) fail();
      })
      .catch(fail);

    const clock = setInterval(() => {
      if (!active || !ready) return;
      const seconds = playerRef.current?.getCurrentTime();
      if (typeof seconds === "number" && Number.isFinite(seconds) && seconds >= 0) {
        setPosition(Math.floor(seconds * 1000));
      }
    }, 250);

    return () => {
      active = false;
      clearTimeout(timeout);
      clearInterval(clock);
      destroyYouTubePlayer(playerRef.current);
      playerRef.current = null;
      playerReady.current = false;
      container.replaceChildren();
    };
  }, [attempt, videoId]);

  const start = useCallback(() => {
    setState("loading");
    setAttempt((count) => count + 1);
  }, []);

  const seek = useCallback((positionMs: number) => {
    if (playerRef.current && playerReady.current) {
      playerRef.current.seekTo(positionMs / 1000, true);
      setPosition(positionMs);
    } else {
      pendingSeek.current = positionMs;
    }
  }, []);

  return { containerRef, state, position, seek, start };
}
