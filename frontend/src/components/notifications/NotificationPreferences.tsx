"use client";

import { useState, useEffect } from "react";
import { toast } from "sonner";
import { toastApiError } from "@/lib/errors";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import { type LucideIcon, Bell, ChevronDown, Loader2, Save } from "lucide-react";
import { Card } from "@/components/ui/Card";

interface NotificationType {
  id: string;
  label: string;
  description: string;
  icon: LucideIcon;
}

// 与后端 `NotificationPreferencesUpdate` 的字段一一对应（PUT 只认这几个 key，
// 传别的会被 Pydantic 丢掉、看起来“保存成功”其实什么都没存）。社区类
// community_updates / new_follower / comment_reply 已随 ADR-0012 休眠，不展示。
const NOTIFICATION_TYPES: NotificationType[] = [
  { id: "push_notifications", label: "推送通知", description: "站内消息提醒总开关", icon: Bell },
  {
    id: "vocabulary_reminder",
    label: "词汇复习提醒",
    description: "按你设置的时间提醒复习，可随时关闭",
    icon: Bell,
  },
];

interface Preferences {
  [key: string]: boolean;
}

/**
 * 通知偏好（1B 设计减法后）：默认折叠收纳，标题行显示开启数量；
 * 展开后是开关列表＋保存。设置一次后几乎不再碰，不占设置页主视觉。
 */
export function NotificationPreferences() {
  const [preferences, setPreferences] = useState<Preferences>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    loadPreferences();
  }, []);

  async function loadPreferences() {
    setLoading(true);
    try {
      const data = await api<Preferences>("/api/v1/notifications/preferences");
      setPreferences(data);
    } catch (err) {
      toastApiError(err, "通知设置加载失败");
    } finally {
      setLoading(false);
    }
  }

  function togglePreference(id: string) {
    setPreferences((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  }

  async function handleSave() {
    setSaving(true);
    try {
      await api("/api/v1/notifications/preferences", {
        method: "PUT",
        body: JSON.stringify(preferences),
      });
      toast.success("通知偏好已保存");
    } catch (err) {
      toastApiError(err, "保存失败");
    } finally {
      setSaving(false);
    }
  }

  const enabledCount = NOTIFICATION_TYPES.filter((t) => preferences[t.id] !== false).length;

  return (
    <div className="border-t border-hairline pt-4">
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className="flex items-center justify-between w-full text-left"
        aria-expanded={expanded}
      >
        <div>
          <p className="text-copy font-semibold text-ink">通知设置</p>
          <p className="text-meta text-muted mt-0.5">
            {loading ? "加载中…" : `已开启 ${enabledCount} / ${NOTIFICATION_TYPES.length} 项`}
          </p>
        </div>
        <ChevronDown
          size={16}
          className={cn("text-muted transition-transform", expanded && "rotate-180")}
        />
      </button>

      {expanded && (
        <div className="mt-3 space-y-3">
          <Card padding={0} className="divide-y divide-hairline">
            {NOTIFICATION_TYPES.map((type) => {
              const enabled = preferences[type.id] !== false;
              return (
                <div key={type.id} className="flex items-center justify-between px-4 py-3">
                  <div className="flex items-start gap-3">
                    <div className="mt-0.5 flex h-7 w-7 items-center justify-center rounded-lg bg-surface-soft">
                      <type.icon className="h-3.5 w-3.5 text-brand-500" />
                    </div>
                    <div>
                      <div className="text-copy font-medium text-ink">{type.label}</div>
                      <div className="text-meta text-muted">{type.description}</div>
                    </div>
                  </div>
                  <button
                    onClick={() => togglePreference(type.id)}
                    className={cn(
                      "relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-brand-500/15 focus:ring-offset-2",
                      enabled ? "bg-brand-500" : "bg-hairline"
                    )}
                    role="switch"
                    aria-checked={enabled}
                    // 按钮旁边那行 label 只是兄弟节点，不构成可访问名；
                    // 屏幕阅读器只会念「开关，已选中」。用 aria-label 给出
                    // 具体是哪一项（其余四个同类开关都有名字）。
                    aria-label={type.label}
                  >
                    <span
                      className={cn(
                        "pointer-events-none inline-block h-5 w-5 transform rounded-full bg-on-primary shadow ring-0 transition duration-200 ease-in-out",
                        enabled ? "translate-x-5" : "translate-x-0"
                      )}
                    />
                  </button>
                </div>
              );
            })}
          </Card>
          <div className="flex justify-end">
            <Button
              size="sm"
              variant="outline"
              icon={saving ? Loader2 : Save}
              onClick={handleSave}
              disabled={saving}
            >
              {saving ? "保存中..." : "保存通知设置"}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
