/**
 * 试卷库的「科目」表 —— **唯一事实源**（后端已在 2026-10 清理中删掉同名的
 * `app/core/exam_subjects.py`，服务端不参与展示名与排序）。
 *
 * 这是一套**独立于词汇等级**（`lib/examLevels.ts`）的东西：等级表管「一个词属于哪份
 * 大纲词表」，本表管「一套卷属于哪门考试」。专四专八只有原卷 PDF、没有题库数据，
 * 所以它们在这里有科目名却不会出现在试卷列表里；`kaoyan` 只服务 PDF —— 考研题库按
 * 英语一/英语二拆成 `ky1`/`ky2`，原卷 PDF 只有「考研英语」这一个来源分类。
 *
 * 用不着像 `examLevels` 那样跑生成器：那套「Python 为源 + 生成 + CI diff 门」
 * 的代价只对词汇等级划算（那边还有 Tailwind 颜色表和 throw 检查要一起同步）。
 * 后端不消费本表，所以新增科目只改这一个文件。
 */
export const EXAM_SUBJECTS: Record<string, { label: string; order: number }> = {
  cet4: { label: "四级", order: 1 },
  cet6: { label: "六级", order: 2 },
  ky1: { label: "考研英语一", order: 3 },
  ky2: { label: "考研英语二", order: 4 },
  kaoyan: { label: "考研英语", order: 5 },
  tem4: { label: "专四", order: 6 },
  tem8: { label: "专八", order: 7 },
};

/** 表里没有的原样返回，免得新科目在界面上变成空白。 */
export function subjectLabel(key: string): string {
  return EXAM_SUBJECTS[key]?.label ?? key;
}

/** 排序用；表里没有的排最后。 */
export function subjectOrder(key: string): number {
  return EXAM_SUBJECTS[key]?.order ?? 99;
}

/** 有题库（`ExamPaper`）的科目 —— 试卷列表的分页只认这四个。 */
export const PAPER_LEVELS = ["cet4", "cet6", "ky1", "ky2"];
