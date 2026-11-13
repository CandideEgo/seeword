"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { toast } from "sonner";
import { MessageSquare, Bell } from "lucide-react";
import { toastApiError } from "@/lib/errors";
import { PASSWORD_HINT, PASSWORD_RULE_MESSAGE, isPasswordAcceptable } from "@/lib/password";
import { api } from "@/lib/api";
import { NotificationPreferences } from "@/components/notifications/NotificationPreferences";
import { AccountLifecycleSettings } from "@/components/profile/AccountLifecycleSettings";
import { ExternalConnections } from "@/components/profile/ExternalConnections";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { FormField } from "@/components/ui/FormField";
import { TargetExamSetting } from "@/components/exam/TargetExamSetting";
import { cn } from "@/lib/utils";
import type { User, UserPreferences } from "@/types";
import { InterestPicker } from "@/components/profile/InterestPicker";
import { Card } from "@/components/ui/Card";

interface SettingsTabProps {
  user: User;
  preferences: UserPreferences | null;
  onUpdatePreferences: (prefs: UserPreferences) => void;
  section?: "all" | "learning" | "account";
}

const COMMON_TIMEZONES = [
  "Asia/Shanghai",
  "Asia/Tokyo",
  "Asia/Hong_Kong",
  "Asia/Singapore",
  "America/New_York",
  "America/Los_Angeles",
  "America/Chicago",
  "Europe/London",
  "Europe/Paris",
  "Europe/Berlin",
  "Australia/Sydney",
];

const GOAL_TYPE_LABELS: Record<string, string> = {
  minutes: "学习分钟数",
  words: "复习单词数",
};

/** 数值后的量词：直接拼「复习单词数」会读成「每天 5 复习单词数」。 */
const GOAL_UNIT_LABELS: Record<string, string> = {
  minutes: "分钟",
  words: "个词",
};

/** 每日提醒时间档（设计稿 profile.html「提醒时间」的固定档位）。 */
const REMINDER_TIMES = ["07:30", "12:30", "18:00", "20:30", "22:00"];

/**
 * 设置（1B 设计减法后）：原「账户设置」「学习偏好」两个 Tab 合并为本页，
 * 分「学习」「账户」两个分组卡；学习目标/字幕/难度/时区/学习提醒共用一个
 * 底部保存，改密码因需要当前密码校验保留独立提交；通知设置默认折叠收纳。
 *
 * 学习提醒（设计稿「学习提醒」区块）：后端 UserPreferences 已有
 * reminder_enabled / reminder_time / reminder_timezone，这里补上入口，
 * 并在保存时把「提醒时区」与设置页时区写成同一个值（与设计口径一致：
 * 提醒与统计共用同一个时区）。
 */
export default function SettingsTab({
  user,
  preferences,
  onUpdatePreferences,
  section = "all",
}: SettingsTabProps) {
  const [interests, setInterests] = useState(preferences?.interest_categories ?? []);
  // Learning preferences
  const [goalType, setGoalType] = useState<UserPreferences["daily_goal_type"]>(
    preferences?.daily_goal_type === "minutes" ? "minutes" : "words"
  );
  const [goalValue, setGoalValue] = useState(preferences?.daily_goal_value || 5);
  const [subtitleMode, setSubtitleMode] = useState(
    preferences?.subtitle_mode_default || "bilingual"
  );
  const [preferredDifficulty, setPreferredDifficulty] = useState(
    preferences?.preferred_difficulty || ""
  );

  // Timezone — default follows the browser instead of assuming Shanghai.
  const browserTz =
    typeof Intl !== "undefined"
      ? Intl.DateTimeFormat().resolvedOptions().timeZone
      : "Asia/Shanghai";
  const [timezone, setTimezone] = useState(user.timezone || browserTz);

  // Learning reminder（设计稿：每日提醒开关 + 提醒时间；时区与学习设置共用）
  const [reminderEnabled, setReminderEnabled] = useState(false);
  useEffect(() => {
    let active = true;
    void api<{ vocabulary_reminder?: boolean }>("/api/v1/notifications/preferences")
      .then((p) => {
        if (active) setReminderEnabled(p.vocabulary_reminder === true);
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, []);
  const reminderTimeOptions = [
    ...new Set([preferences?.reminder_time || "20:00", ...REMINDER_TIMES]),
  ];
  const [reminderTime, setReminderTime] = useState(preferences?.reminder_time || "20:00");

  const [saving, setSaving] = useState(false);

  async function handleSave() {
    setSaving(true);
    try {
      const updated = await api<UserPreferences>("/api/v1/users/me/preferences", {
        method: "PUT",
        body: JSON.stringify({
          interest_categories: interests,
          daily_goal_type: goalType,
          daily_goal_value: goalValue,
          subtitle_mode_default: subtitleMode,
          preferred_difficulty: preferredDifficulty || null,
          reminder_enabled: reminderEnabled,
          reminder_time: reminderTime,
          // 提醒与统计共用同一个时区：与页面上的时区选择保持同步。
          reminder_timezone: timezone,
        }),
      });
      await api("/api/v1/notifications/preferences", {
        method: "PUT",
        body: JSON.stringify({ vocabulary_reminder: reminderEnabled }),
      });
      onUpdatePreferences(updated);
      if (timezone !== user.timezone) {
        await api("/api/v1/users/me", {
          method: "PATCH",
          body: JSON.stringify({ timezone }),
        });
      }
      toast.success("设置已保存");
    } catch {
      toast.error("保存失败");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="max-w-3xl space-y-6">
      {section !== "account" && (
        <>
          <Card as="section" padding={5}>
            <InterestPicker value={interests} onChange={setInterests} disabled={saving} />
          </Card>
          {/* Learning group */}
          <Card as="section" padding={5} className="space-y-4">
            <h2 className="user-sec-title">学习</h2>

            <FormField label="每日目标" hint="设置每日学习目标，养成坚持学习的好习惯">
              <div className="flex items-center gap-3">
                <Select
                  value={goalType}
                  onChange={(e) => {
                    setGoalType(e.target.value as UserPreferences["daily_goal_type"]);
                    // Reset value to sensible defaults per type
                    if (e.target.value === "minutes") setGoalValue(15);
                    else if (e.target.value === "words") setGoalValue(10);
                  }}
                  className="w-40"
                >
                  {Object.entries(GOAL_TYPE_LABELS).map(([key, label]) => (
                    <option key={key} value={key}>
                      {label}
                    </option>
                  ))}
                </Select>
                <Input
                  type="number"
                  min={1}
                  max={100}
                  value={goalValue}
                  onChange={(e) => setGoalValue(parseInt(e.target.value) || 1)}
                  className="w-24"
                />
                <span className="text-meta text-muted">
                  每天 {goalValue} {GOAL_UNIT_LABELS[goalType] ?? ""}
                </span>
              </div>
            </FormField>

            <FormField label="默认字幕模式">
              <Select
                value={subtitleMode}
                onChange={(e) =>
                  setSubtitleMode(e.target.value as "bilingual" | "english" | "chinese")
                }
                className="w-40"
              >
                <option value="bilingual">双语字幕</option>
                <option value="english">仅英文</option>
                <option value="chinese">仅中文</option>
              </Select>
            </FormField>

            {/* P1-1：目标考试固定入口。改动立即写回偏好 + watchStore，播放页高亮随之刷新。 */}
            <TargetExamSetting
              value={preferences?.target_exam ?? null}
              onSaved={onUpdatePreferences}
            />

            <FormField label="偏好难度" hint="用于推荐合适难度的视频">
              <Select
                value={preferredDifficulty}
                onChange={(e) => setPreferredDifficulty(e.target.value)}
                className="w-40"
              >
                <option value="">不限</option>
                {["A1", "A2", "B1", "B2", "C1", "C2"].map((l) => (
                  <option key={l} value={l}>
                    {l}
                  </option>
                ))}
              </Select>
            </FormField>
          </Card>

          {/* 学习提醒（设计稿「学习提醒」区块）：开关 + 时间 + 时区 + 共同时区说明 */}
          <Card as="section" padding={5} className="space-y-4">
            <div>
              <h2 className="user-sec-title">学习提醒</h2>
              <p className="user-sec-sub mt-1">
                每天最多提醒一次；提醒只提示「今天有多少词到期」，不催学习时长。
              </p>
            </div>

            <div className="flex items-center justify-between gap-3 border-t border-hairline-soft pt-4">
              <div>
                <p className="text-copy font-semibold text-ink">每日学习提醒</p>
                <p className="mt-0.5 text-meta text-muted">
                  由定时任务每小时检查一次到期词，到点推送站内通知。
                </p>
              </div>
              <div className="flex shrink-0 items-center gap-2">
                <span
                  className={cn(
                    "text-meta font-semibold",
                    reminderEnabled ? "text-brand-700" : "text-muted"
                  )}
                >
                  {reminderEnabled ? "已开启" : "已关闭"}
                </span>
                <button
                  type="button"
                  role="switch"
                  aria-checked={reminderEnabled}
                  aria-label="每日学习提醒开关"
                  onClick={() => setReminderEnabled((v) => !v)}
                  className={cn(
                    "relative inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full border-2 transition-colors duration-200",
                    reminderEnabled
                      ? "border-brand-500 bg-brand-50"
                      : "border-hairline-strong bg-surface-soft"
                  )}
                >
                  <span
                    className={cn(
                      "pointer-events-none inline-block h-4 w-4 rounded-full shadow transition-transform duration-200",
                      reminderEnabled
                        ? "translate-x-5 bg-brand-500"
                        : "translate-x-0.5 bg-canvas ring-1 ring-hairline-strong"
                    )}
                  />
                </button>
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <FormField label="提醒时间" hint="到点只发一次；当天已经复习过就不再提醒。">
                <Select
                  value={reminderTime}
                  onChange={(e) => setReminderTime(e.target.value)}
                  className="w-40"
                  disabled={!reminderEnabled}
                >
                  {reminderTimeOptions.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </Select>
              </FormField>
              <FormField label="时区" hint="影响每日统计与提醒的结算时间，默认跟随浏览器。">
                <Select
                  value={timezone}
                  onChange={(e) => setTimezone(e.target.value)}
                  className="w-56"
                >
                  {[...new Set([timezone, ...COMMON_TIMEZONES])].map((tz) => (
                    <option key={tz} value={tz}>
                      {tz}
                    </option>
                  ))}
                </Select>
              </FormField>
            </div>

            <div className="user-notice">
              <Bell size={16} className="mt-0.5 shrink-0 text-brand-700" aria-hidden />
              <div>
                <strong className="text-ink">提醒与统计共用同一个时区。</strong>
                换时区会同时改变复习提醒时刻和每天的词汇计数边界。
              </div>
            </div>
          </Card>

          {/* Unified save for learning prefs + timezone + reminder */}
          <div>
            <Button onClick={handleSave} disabled={saving}>
              {saving ? "保存中..." : "保存设置"}
            </Button>
          </div>
        </>
      )}
      {section !== "learning" && (
        <>
          {/* Account group */}
          <Card as="section" padding={5} className="space-y-4">
            <h2 className="user-sec-title">账户</h2>
            <PasswordChangeForm />
            <NotificationPreferences />
            <ExternalConnections />
            {/* P1-7：数据导出 + 30 天可撤回注销 */}
            <div className="border-t border-hairline pt-4">
              <AccountLifecycleSettings />
            </div>
            <div className="border-t border-hairline pt-2">
              <Link
                href="/contact"
                className="inline-flex items-center gap-1.5 text-meta text-muted transition-colors hover:text-brand-700"
              >
                <MessageSquare size={13} />
                意见反馈与帮助
              </Link>
            </div>
          </Card>
        </>
      )}
    </div>
  );
}

function PasswordChangeForm() {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [saving, setSaving] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      toast.error("两次输入的新密码不一致");
      return;
    }
    if (!isPasswordAcceptable(newPassword)) {
      toast.error(PASSWORD_RULE_MESSAGE);
      return;
    }
    setSaving(true);
    try {
      await api("/api/v1/auth/change-password", {
        method: "POST",
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      });
      toast.success("密码已修改");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err) {
      toastApiError(err, "修改失败");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3 border-t border-hairline pt-4">
      <p className="text-copy font-semibold text-ink">登录与安全</p>
      <p className="text-meta text-muted">
        手机号 + 短信验证码登录，没有邮箱。手机号是唯一登录凭据，更换后旧号码立即失效。
      </p>
      <div className="grid gap-3 sm:grid-cols-3">
        {/* P0-A：仅验证码注册的账户 hashed_password 为空，首设密码时不校验旧密码
            （后端首设分支也不失效当前会话）；因此这里允许留空。 */}
        <FormField label="当前密码" hint="首次设置密码可留空">
          <Input
            type="password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            className="w-full"
          />
        </FormField>
        <FormField label="新密码" hint={PASSWORD_HINT}>
          <Input
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            required
            minLength={8}
            className="w-full"
          />
        </FormField>
        <FormField label="确认新密码">
          <Input
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            minLength={8}
            className="w-full"
          />
        </FormField>
      </div>
      <div>
        <Button type="submit" variant="outline" size="sm" disabled={saving}>
          {saving ? "修改中..." : "修改密码"}
        </Button>
      </div>
    </form>
  );
}
