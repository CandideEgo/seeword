"use client";

import Link from "next/link";
import { ArrowUpRight, BookOpen } from "lucide-react";
import { useLessonAvailability } from "@/hooks/useLessonAvailability";

/** A real, flag-gated route into courses; never an invented recommendation. */
export function LessonEntry() {
  const enabled = useLessonAvailability();
  if (!enabled) return null;
  return (
    <Link href="/lessons" className="learning-course-entry">
      <BookOpen size={21} aria-hidden />
      <span className="min-w-0 flex-1 text-copy font-semibold">视频课程</span>
      <ArrowUpRight size={18} aria-hidden />
    </Link>
  );
}
