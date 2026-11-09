"use client";

import { BookOpen, GraduationCap, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * 学习动作 —— 与视频级动作（点赞 / 收藏 / 笔记）分开：
 * 桌面住在当前句卡的动作带里，移动端住在 ⋯ 面板里。
 *
 * 点击一律 `stopPropagation`：句卡根节点是播放/暂停热区，学习动作不能顺带切播放。
 */
export function LearningActions({
  compact,
  vocabSet,
  addingVocabSet,
  onVocabSet,
  onDrill,
}: {
  /** true = 移动端 ⋯ 面板的 44px 图标档；false = 桌面动作带的带文字档。 */
  compact: boolean;
  vocabSet: { id: string } | null;
  addingVocabSet: boolean;
  onVocabSet: () => void;
  onDrill: () => void;
}) {
  const box = compact ? "w-11 h-11 justify-center" : "h-9 px-3 gap-1.5";

  return (
    <div data-testid="learning-actions" className="flex shrink-0 items-center gap-1">
      <button
        type="button"
        className={cn(
          "inline-flex items-center rounded-md transition-colors cursor-pointer",
          box,
          vocabSet ? "text-brand-700" : "text-muted hover:bg-surface-card hover:text-ink"
        )}
        onClick={(e) => {
          e.stopPropagation();
          onVocabSet();
        }}
        aria-label={vocabSet ? "已加入学习，查看词汇集合" : "把本视频单词加入学习"}
        title={vocabSet ? "已加入学习" : "加入学习"}
        disabled={addingVocabSet}
      >
        {addingVocabSet ? (
          <Loader2 size={18} className="animate-spin" />
        ) : (
          <GraduationCap size={18} className={cn(vocabSet && "fill-current")} />
        )}
        {!compact && (
          <span className="text-meta font-semibold">{vocabSet ? "已加入学习" : "加入学习"}</span>
        )}
      </button>
      <button
        type="button"
        className={cn(
          "inline-flex items-center rounded-md text-muted transition-colors hover:bg-surface-card hover:text-ink cursor-pointer",
          box
        )}
        onClick={(e) => {
          e.stopPropagation();
          onDrill();
        }}
        aria-label="单词训练"
        title="单词训练"
      >
        <BookOpen size={18} />
        {!compact && <span className="text-meta font-semibold">单词训练</span>}
      </button>
    </div>
  );
}
