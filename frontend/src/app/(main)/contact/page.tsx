"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";
import { PageHeader } from "@/components/ui/PageHeader";
import { PageTransition } from "@/components/common/PageTransition";
import { Button } from "@/components/ui/Button";
import { Textarea, Input } from "@/components/ui/Input";
import { Card } from "@/components/ui/Card";
import { Badge, type BadgeTone } from "@/components/common/Badge";
import { FullPageSpinner } from "@/components/common/Spinner";
import { ErrorState } from "@/components/common/ErrorState";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/ToggleGroup";
import {
  Megaphone,
  Send,
  MessageSquare,
  CheckCircle2,
  ChevronDown,
  ArrowRight,
  HelpCircle,
} from "lucide-react";
import { relativeTime } from "@/lib/date";

interface Announcement {
  id: string;
  type: string;
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
}

interface Feedback {
  id: string;
  category: string;
  content: string;
  contact: string | null;
  status: string;
  admin_reply: string | null;
  created_at: string;
}

const CATEGORIES = [
  { key: "suggestion", label: "建议" },
  { key: "bug", label: "使用问题" },
  { key: "other", label: "其他" },
] as const;

const STATUS_LABEL: Record<string, { tone: BadgeTone; text: string }> = {
  open: { tone: "brand", text: "待处理" },
  in_progress: { tone: "amber", text: "处理中" },
  resolved: { tone: "green", text: "已解决" },
};

interface FaqItem {
  q: string;
  body: string[];
  link?: { href: string; label: string };
}

/** 设计稿 contact.html 的常见问题；口径按产品现状改写（全站功能免费开放）。 */
const FAQ: FaqItem[] = [
  {
    q: "今天到期的词是怎么算出来的？",
    body: [
      "到期时间由间隔复习的排期决定：每次复习后按你答得怎么样，把下一次复习的间隔推远或拉近，答错的词会更早回来。",
      "词汇页能看到词库总量、今天到期与已掌握的数量；今天到期之外的词已经排进之后几天，不用今天处理。",
    ],
    link: { href: "/vocabulary", label: "去词汇页" },
  },
  {
    q: "点词加入词库之后，去哪儿复习？",
    body: [
      "加入的词会进词汇页，按到期时间排队；也可以直接看词库总量、已掌握数量与到期分布。",
      "看完一个视频想顺手复习，可以在词汇页当天到期队列里过一遍。",
    ],
    link: { href: "/vocabulary", label: "去词汇页" },
  },
  {
    q: "换手机号以后，学习记录和词库还在吗？",
    body: [
      "都在。换绑只改登录用的手机号，词汇、词库与学习记录都跟着账号走。",
      "换绑入口在「我的 → 个人资料 → 手机号 → 更换」，需要新手机号的短信验证码与当前密码。",
    ],
    link: { href: "/profile", label: "去个人资料" },
  },
  {
    q: "视频里的单词点不动，或字幕和声音不同步怎么办？",
    body: [
      "先刷新页面再点一次；如果仍然不对，请把视频标题、句子位置（如「第 12 句，4:01」）和设备浏览器写进反馈，我们按段重新对齐字幕。",
      "遇到字幕缺失或错位，可以附上视频名称和时间点，方便我们核查。",
    ],
  },
  {
    q: "注销账户后，我的数据会怎样？",
    body: [
      "提交后有 30 天冷静期，期间仍可登录、继续学习，也能随时撤销；到期会删除个人数据与上传的媒体原件，手机号随之释放，词汇与学习记录不可恢复。",
      "需要留档请先在「我的 → 账号」里「导出我的数据」。如有未处理的订单问题，请在注销前联系支持。",
    ],
    link: { href: "/profile?tab=account", label: "去账号页" },
  },
  {
    q: "问题不在上面这些里，怎么反馈最快？",
    body: [
      "类型选「其他」，正文写清三步：你在哪一页、点了什么、看到什么（期望什么）。账单、发票问题请附订单号，处理会快很多。",
      "也可以直接发邮件到 support@seeword.top；附件（截图/录屏）走这条路径。",
    ],
  },
];

export default function ContactPage() {
  // 公开页（proxy.ts PUBLIC_PATHS）：未登录也能看到开发者联系方式，不跳登录。
  // 需要会话的部分（公告拉取、反馈表单）按 isAuthenticated 分段渲染。
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const isLoading = useAuthStore((s) => s.isLoading);
  const [category, setCategory] = useState<(typeof CATEGORIES)[number]["key"]>("suggestion");
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [contact, setContact] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [myFeedback, setMyFeedback] = useState<Feedback[]>([]);
  const [announcementsFailed, setAnnouncementsFailed] = useState(false);
  const [feedbackFailed, setFeedbackFailed] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [retry, setRetry] = useState(0);
  const faqRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (isLoading) return;
    if (!isAuthenticated) {
      setAnnouncements([]);
      setMyFeedback([]);
      return;
    }
    let cancelled = false;
    setHistoryLoading(true);
    Promise.allSettled([
      api<{ items: Announcement[] }>("/api/v1/notifications?page=1&page_size=50"),
      api<Feedback[]>("/api/v1/feedback/mine"),
    ]).then(([notifications, feedback]) => {
      if (cancelled) return;
      setAnnouncementsFailed(notifications.status === "rejected");
      setFeedbackFailed(feedback.status === "rejected");
      if (notifications.status === "fulfilled")
        setAnnouncements(notifications.value.items.filter((n) => n.type === "announcement"));
      if (feedback.status === "fulfilled") setMyFeedback(feedback.value);
      setHistoryLoading(false);
    });
    return () => {
      cancelled = true;
    };
  }, [isAuthenticated, isLoading, retry]);

  if (isLoading) return <FullPageSpinner />;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (content.trim().length < 5) {
      toast.error("反馈内容至少 5 个字");
      return;
    }
    const feedbackContent = title.trim() ? `${title.trim()}\n\n${content.trim()}` : content.trim();
    if (feedbackContent.length > 5000) {
      toast.error("标题和反馈内容合计最多 5000 个字");
      return;
    }
    setSubmitting(true);
    try {
      const fb = await api<Feedback>("/api/v1/feedback", {
        method: "POST",
        body: JSON.stringify({
          category,
          content: feedbackContent,
          contact: contact.trim() || null,
        }),
      });
      setMyFeedback((prev) => [fb, ...prev]);
      setTitle("");
      setContent("");
      setContact("");
      toast.success("反馈已提交，感谢！");
    } catch {
      toast.error("提交失败，请稍后重试");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <PageTransition>
      <div className="user-page">
        <PageHeader
          crumb="帮助"
          title="帮助与反馈"

          actions={
            <Button
              variant="outline"
              icon={HelpCircle}
              onClick={() => faqRef.current?.scrollIntoView({ behavior: "smooth", block: "start" })}
            >
              看常见问题
            </Button>
          }
        />

        <div className="user-page-layout has-aside">
          <div className="user-page-main">
            {/* 联系我们 */}
            <section>
              <div className="user-sec-head">
                <div>
                  <h2 className="user-sec-title">联系我们</h2>
                </div>
              </div>
              <Card padding={5} className="mt-4">
                <div className="flex flex-wrap items-center gap-x-3 gap-y-2 text-copy">
                  <MessageSquare size={16} className="text-brand-700" aria-hidden />
                  <span className="text-muted">邮箱</span>
                  <span className="select-all font-mono text-ink">support@seeword.top</span>
                  <span className="ml-auto text-meta text-muted">账单、发票问题请附上订单号。</span>
                </div>
              </Card>
            </section>

            {/* 公告（需登录拉取，未登录整段隐藏） */}
            {isAuthenticated && (
              <section>
                <div className="user-sec-head">
                  <h2 className="user-sec-title">公告</h2>
                </div>
                {historyLoading ? (
                  <p role="status" className="mt-4 text-meta text-muted">
                    正在加载公告…
                  </p>
                ) : announcementsFailed ? (
                  <ErrorState
                    title="公告暂时未能加载"
                    onRetry={() => setRetry((v) => v + 1)}
                    className="py-4"
                  />
                ) : announcements.length === 0 ? (
                  <p className="mt-4 flex items-center gap-2 text-copy text-muted">
                    <Megaphone size={16} className="text-brand-700" aria-hidden />
                    暂无新公告
                  </p>
                ) : (
                  <div className="mt-4 space-y-2">
                    {announcements.map((a) => (
                      <Card key={a.id} padding={4} className={a.is_read ? "" : "border-brand-200"}>
                        <div className="flex items-center justify-between gap-2 mb-1.5">
                          <h3 className="text-copy font-semibold text-ink truncate">{a.title}</h3>
                          <span className="text-caption text-muted shrink-0">
                            {relativeTime(a.created_at)}
                          </span>
                        </div>
                        {a.message && (
                          <p className="text-copy text-body leading-relaxed whitespace-pre-wrap">
                            {a.message}
                          </p>
                        )}
                      </Card>
                    ))}
                  </div>
                )}
              </section>
            )}

            {/* 提交反馈（提交接口需要会话，未登录给登录入口） */}
            <section>
              <div className="user-sec-head">
                <div>
                  <h2 className="user-sec-title">提交反馈</h2>
                </div>
              </div>
              {isAuthenticated ? (
                <form
                  className="mt-4 space-y-4 rounded-md border border-hairline bg-canvas p-5"
                  onSubmit={handleSubmit}
                >
                  <div>
                    <span className="block text-copy font-medium text-ink">反馈类型</span>
                    <ToggleGroup
                      value={category}
                      onValueChange={setCategory}
                      className="mt-2"
                      aria-label="反馈类型"
                    >
                      {CATEGORIES.map((c) => (
                        <ToggleGroupItem key={c.key} value={c.key}>
                          {c.label}
                        </ToggleGroupItem>
                      ))}
                    </ToggleGroup>
                  </div>
                  <label className="block text-copy font-medium text-ink">
                    反馈标题（可选）
                    <Input
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                      maxLength={100}
                      placeholder="一句话说明问题或建议"
                      className="mt-2"
                    />
                    <span className="mt-1 block text-meta text-muted">
                      标题会并入正文首行提交；标题与正文合计最多 5000 字。
                    </span>
                  </label>
                  <Textarea
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    placeholder="说说你遇到的问题或建议（至少 5 个字）..."
                    rows={5}
                    maxLength={5000}
                    required
                    aria-label="反馈正文"
                  />
                  <div className="user-notice">
                    <MessageSquare
                      size={16}
                      className="mt-0.5 shrink-0 text-brand-700"
                      aria-hidden
                    />
                    <div>
                      <strong className="text-ink">当前不支持上传附件。</strong>
                      如需提供截图或录屏，请发送到
                      support@seeword.top，并在正文里写清对应的现象；或者用文字描述复现步骤。
                    </div>
                  </div>
                  <Input
                    type="text"
                    value={contact}
                    onChange={(e) => setContact(e.target.value)}
                    placeholder="联系方式（可选，填邮箱或微信，方便我们回复你）"
                    maxLength={200}
                    aria-label="联系方式（可选）"
                  />
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <span className="text-meta text-muted">
                      至少填写 5 个字，提交后可在本页查看处理进度
                    </span>
                    <Button
                      type="submit"
                      disabled={submitting}
                      icon={submitting ? undefined : Send}
                    >
                      {submitting ? "提交中..." : "提交反馈"}
                    </Button>
                  </div>
                </form>
              ) : (
                <Card padding={5} className="mt-4 text-center">
                  <p className="text-copy text-muted leading-relaxed">
                    登录后可以直接提交反馈，我们会尽快查看并回复。
                  </p>
                  <Link
                    href="/login?next=/contact"
                    className="mt-3 inline-block text-copy font-semibold text-brand-700 hover:underline"
                  >
                    去登录
                  </Link>
                </Card>
              )}
            </section>

            {/* My feedback history */}
            {isAuthenticated && feedbackFailed && (
              <ErrorState
                title="反馈记录暂时未能加载"
                onRetry={() => setRetry((v) => v + 1)}
                className="py-4"
              />
            )}
            {myFeedback.length > 0 && (
              <section>
                <div className="user-sec-head">
                  <h2 className="user-sec-title">我的反馈</h2>
                </div>
                <div className="mt-4 space-y-2">
                  {myFeedback.map((f) => {
                    const st = STATUS_LABEL[f.status] ?? STATUS_LABEL.open;
                    return (
                      <Card key={f.id} padding={4}>
                        <div className="flex items-center justify-between gap-2 mb-2">
                          <Badge tone={st.tone}>{st.text}</Badge>
                          <span className="text-caption text-muted">
                            {relativeTime(f.created_at)}
                          </span>
                        </div>
                        <p className="text-copy text-ink leading-relaxed whitespace-pre-wrap">
                          {f.content}
                        </p>
                        {f.admin_reply && (
                          <div className="mt-2.5 pt-2.5 border-t border-hairline flex items-start gap-2">
                            <CheckCircle2 size={14} className="text-success-text shrink-0 mt-0.5" />
                            <div>
                              <p className="text-caption text-muted mb-0.5">回复</p>
                              <p className="text-copy text-ink leading-relaxed whitespace-pre-wrap">
                                {f.admin_reply}
                              </p>
                            </div>
                          </div>
                        )}
                      </Card>
                    );
                  })}
                </div>
              </section>
            )}

            {/* 常见问题：8 条可折叠（设计稿 contact.html「常见问题」） */}
            <section ref={faqRef} id="faq" className="scroll-mt-24">
              <div className="user-sec-head">
                <div>
                  <h2 className="user-sec-title">常见问题</h2>
                </div>
              </div>
              <div className="mt-4 border-t border-hairline-soft">
                {FAQ.map((item) => (
                  <details key={item.q} className="group border-b border-hairline-soft">
                    <summary className="flex cursor-pointer list-none items-center justify-between gap-4 py-4 text-copy font-semibold text-ink [&::-webkit-details-marker]:hidden">
                      <span>{item.q}</span>
                      <ChevronDown
                        size={16}
                        className="shrink-0 text-muted transition-transform group-open:rotate-180"
                        aria-hidden
                      />
                    </summary>
                    <div className="space-y-2 pb-4 text-meta leading-relaxed text-muted">
                      {item.body.map((p, j) => (
                        <p key={j}>{p}</p>
                      ))}
                      {item.link && (
                        <p>
                          <Link
                            href={item.link.href}
                            className="inline-flex items-center gap-1 font-semibold text-brand-700 hover:underline"
                          >
                            {item.link.label}
                            <ArrowRight size={13} />
                          </Link>
                        </p>
                      )}
                    </div>
                  </details>
                ))}
              </div>
            </section>
          </div>

          <aside className="user-page-aside">
            <section className="user-aside-sec">
              <h2 className="user-aside-title">提交之后会发生什么</h2>
              <ol className="space-y-3">
                {[
                  "反馈进入处理队列，状态从「待处理」开始。",
                  "我们回复后会变成「处理中」，修好标记为「已解决」并附一条回复。",
                  "进度随时能在本页「我的反馈」里回看。",
                ].map((text, i) => (
                  <li key={text} className="flex gap-3">
                    <span className="mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-pill bg-surface-soft text-caption font-semibold text-ink">
                      {i + 1}
                    </span>
                    <span className="text-meta leading-relaxed text-muted">{text}</span>
                  </li>
                ))}
              </ol>
            </section>

            <section className="user-aside-sec">
              <h2 className="user-aside-title">填写提示</h2>
              <ul className="user-kv">
                <li className="user-kv-row">
                  <span className="user-kv-key">类型</span>
                  <span className="user-kv-val">建议 / 使用问题 / 其他</span>
                </li>
                <li className="user-kv-row">
                  <span className="user-kv-key">正文</span>
                  <span className="user-kv-val">≥ 5 字，≤ 5000 字</span>
                </li>
                <li className="user-kv-row">
                  <span className="user-kv-key">标题</span>
                  <span className="user-kv-val">可选</span>
                </li>
                <li className="user-kv-row">
                  <span className="user-kv-key">附件</span>
                  <span className="user-kv-val">截图或录屏可通过邮件发送</span>
                </li>
                <li className="user-kv-row">
                  <span className="user-kv-key">回复</span>
                  <span className="user-kv-val">提交后可查看处理进度</span>
                </li>
              </ul>
            </section>

            <section className="user-aside-sec">
              <h2 className="user-aside-title">相关页面</h2>
              <ul className="space-y-2">
                <li>
                  <Link
                    href="/profile?tab=account"
                    className="inline-flex items-center gap-1 text-copy font-semibold text-brand-700 hover:underline"
                  >
                    账户与数据导出
                    <ArrowRight size={14} />
                  </Link>
                </li>
                <li>
                  <Link
                    href="/terms"
                    className="inline-flex items-center gap-1 text-copy font-semibold text-brand-700 hover:underline"
                  >
                    用户协议
                    <ArrowRight size={14} />
                  </Link>
                </li>
              </ul>
            </section>
          </aside>
        </div>
      </div>
    </PageTransition>
  );
}
