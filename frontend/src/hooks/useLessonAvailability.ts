"use client";

import { useEffect, useState } from "react";
import { getLessonAvailability } from "@/lib/lessons";

export function useLessonAvailability(active = true, admin = false) {
  const [enabled, setEnabled] = useState(false);
  useEffect(() => {
    if (!active) return;
    let live = true;
    getLessonAvailability(admin).then(
      (status) => {
        if (live) setEnabled(status.enabled);
      },
      () => {
        if (live) setEnabled(false);
      }
    );
    return () => {
      live = false;
    };
  }, [active, admin]);
  return enabled;
}
