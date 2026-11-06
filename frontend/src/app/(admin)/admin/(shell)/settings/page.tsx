"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import {
  AlertCircle,
  AlertTriangle,
  Loader2,
  RefreshCw,
  Save,
  Settings2,
  ShieldCheck,
  UserCog,
  Zap,
} from "lucide-react";

import { AdminEmptyState, AdminPageHeader, AdminSkeleton } from "@/components/admin/ui";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";
import { apiErrorMessage } from "@/lib/errors";
import { ApiClientError } from "@/lib/createApiClient";
import type { AdminAccount, AdminSettings } from "@/types";
import { getAdminSettings, listAdminAccounts, saveAdminSettings } from "@/lib/adminData";
import { useAdminAuthStore } from "@/stores/adminAuthStore";
import { Card } from "@/components/ui/Card";

// ---------------------------------------------------------------------------
// Field ids — 每行标题用 <label htmlFor> 关联控件（A-13），描述用 aria-describedby
// ---------------------------------------------------------------------------

interface FieldIds {
  control: string;
  label: string;
  description: string;
}

function fieldIds(key: string): FieldIds {
  return {
    control: `admin-setting-${key}`,
    label: `admin-setting-${key}-label`,
    description: `admin-setting-${key}-desc`,
  };
}

const IDS = {
  siteName: fieldIds("site-name"),
  registrationEnabled: fieldIds("registration-enabled"),
  qualityBlockEnabled: fieldIds("quality-block-enabled"),
  qualityBlockThreshold: fieldIds("quality-block-threshold"),
  qualityWarnThreshold: fieldIds("quality-warn-threshold"),
  hallucinationDetectionEnabled: fieldIds("hallucination-detection-enabled"),
  translateTimeout: fieldIds("translate-timeout"),
  downloadTimeout: fieldIds("download-timeout"),
  downloadAutoRetry: fieldIds("download-auto-retry"),
  watchdog: fieldIds("watchdog"),
} as const;

/** A-21：这些字段/开关只写库，运行时没有任何消费者——在 UI 上如实标注。 */
const STORED_ONLY_NOTE = "仅登记，运行时未读取";

/** 后端阈值契约是 0–1 的比例；界面按百分比 0–100 展示/输入（A-06）。 */
function ratioToPercentText(ratio: number): string {
  return String(Number((ratio * 100).toFixed(2)));
}

function parsePercentText(raw: string): number | null {
  if (raw.trim() === "") return null;
  const value = Number(raw);
  return Number.isFinite(value) ? value : null;
}

function isPercentInRange(value: number | null): value is number {
  return value !== null && value >= 0 && value <= 100;
}

/** VALIDATION_ERROR 的 pydantic 原文是英文，阈值保存失败时给中文口径（A-06）。 */
function settingsErrorMessage(err: unknown, fallback: string): string {
  if (err instanceof ApiClientError && err.code === "VALIDATION_ERROR") {
    return "保存失败：质量阈值必须是 0–1 的比例（界面按百分比 0–100 输入，例如 60% 即 0.6）。请修正后重试。";
  }
  return apiErrorMessage(err, fallback);
}

// ---------------------------------------------------------------------------
// Toggle Switch (prototype 32 .switch)
// ---------------------------------------------------------------------------

function Toggle({
  id,
  on,
  onChange,
  labelledBy,
  describedBy,
}: {
  id: string;
  on: boolean;
  onChange: (v: boolean) => void;
  labelledBy: string;
  describedBy?: string;
}) {
  return (
    <button
      id={id}
      type="button"
      role="switch"
      aria-checked={on}
      aria-labelledby={labelledBy}
      aria-describedby={describedBy}
      onClick={() => onChange(!on)}
      className={cn(
        "relative h-6 w-[42px] shrink-0 rounded-full transition-colors",
        on ? "bg-brand-500" : "border border-hairline bg-surface-card"
      )}
    >
      <span
        aria-hidden
        className={cn(
          "absolute top-1/2 h-[18px] w-[18px] -translate-y-1/2 rounded-full shadow-sm transition-all",
          on ? "left-[20px] bg-on-primary" : "left-[2px] bg-canvas"
        )}
      />
    </button>
  );
}

// ---------------------------------------------------------------------------
// Setting row (prototype 32 .row)
// ---------------------------------------------------------------------------

function Row({
  field,
  title,
  description,
  note,
  children,
}: {
  field: FieldIds;
  title: string;
  description?: string;
  note?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-hairline-soft py-3.5 last:border-b-0">
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
          <label
            htmlFor={field.control}
            id={field.label}
            className="text-copy font-semibold text-ink"
          >
            {title}
          </label>
          {note && (
            <span className="rounded-pill bg-warning-soft px-2 py-0.5 text-caption font-medium text-warning-text">
              {note}
            </span>
          )}
        </div>
        {description && (
          <p id={field.description} className="mt-0.5 text-meta leading-relaxed text-muted">
            {description}
          </p>
        )}
      </div>
      <div className="shrink-0">{children}</div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Section card (prototype 32 .section)
// ---------------------------------------------------------------------------

function Section({
  icon: Icon,
  title,
  description,
  children,
}: {
  icon: typeof Settings2;
  title: string;
  description?: string;
  children: React.ReactNode;
}) {
  return (
    <Card padding={0} className="overflow-hidden">
      <div className="flex items-center gap-2.5 border-b border-hairline px-5 py-4">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-600">
          <Icon size={16} aria-hidden />
        </div>
        <div>
          <h2 className="text-copy-lg font-bold text-ink">{title}</h2>
          {description && <p className="mt-px text-meta text-muted">{description}</p>}
        </div>
      </div>
      <div className="px-5 py-2">{children}</div>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Inputs (prototype 32 .input / .input-suffix)
// ---------------------------------------------------------------------------

function TextInput({
  id,
  value,
  onChange,
  describedBy,
  mono,
  wide,
  placeholder,
}: {
  id: string;
  value: string;
  onChange: (v: string) => void;
  describedBy?: string;
  mono?: boolean;
  wide?: boolean;
  placeholder?: string;
}) {
  return (
    <input
      id={id}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      aria-describedby={describedBy}
      className={cn(
        "h-9 rounded-lg border border-hairline bg-canvas px-3 text-copy text-ink outline-none transition-all",
        "placeholder:text-muted-soft focus:border-brand-400 focus:ring-[3px] focus:ring-brand-500/12",
        mono && "font-mono",
        wide ? "min-w-[220px]" : "min-w-[140px]"
      )}
    />
  );
}

function NumberSuffixInput({
  id,
  value,
  onChange,
  suffix,
  describedBy,
  invalid,
  width = 90,
  step,
  min,
  max,
}: {
  id: string;
  value: string;
  onChange: (v: string) => void;
  suffix: string;
  describedBy?: string;
  invalid?: boolean;
  width?: number;
  step?: string;
  min?: number;
  max?: number;
}) {
  return (
    <span className="inline-flex items-center">
      <input
        id={id}
        type="number"
        step={step}
        min={min}
        max={max}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        aria-describedby={describedBy}
        aria-invalid={invalid || undefined}
        style={{ width }}
        className={cn(
          "h-9 rounded-l-lg border border-hairline bg-canvas px-3 font-mono text-copy text-ink outline-none transition-all",
          "focus:border-brand-400 focus:ring-[3px] focus:ring-brand-500/12",
          invalid && "border-error"
        )}
      />
      <span
        aria-hidden
        className="inline-flex h-9 items-center rounded-r-lg border border-hairline border-l-0 bg-surface-card px-2.5 text-copy text-muted"
      >
        {suffix}
      </span>
    </span>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

const MASK_PHONE = (phone: string | null) =>
  phone ? `${phone.slice(0, 3)}****${phone.slice(-4)}` : "—";

export default function AdminSettingsPage() {
  const currentUserId = useAdminAuthStore((s) => s.user?.sub);
  const [saved, setSaved] = useState<AdminSettings | null>(null);
  const [form, setForm] = useState<AdminSettings | null>(null);
  const [admins, setAdmins] = useState<AdminAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  // 阈值输入用字符串草稿，允许「清空/输入中」的中间态；提交时再换算成比例。
  const [blockPercent, setBlockPercent] = useState("");
  const [warnPercent, setWarnPercent] = useState("");

  const syncThresholdDrafts = useCallback((settings: AdminSettings) => {
    setBlockPercent(ratioToPercentText(settings.quality_block_threshold));
    setWarnPercent(ratioToPercentText(settings.quality_warn_threshold));
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const [settings, accounts] = await Promise.all([
        getAdminSettings(),
        listAdminAccounts().catch(() => [] as AdminAccount[]),
      ]);
      setSaved(settings);
      setForm(settings);
      syncThresholdDrafts(settings);
      setAdmins(accounts);
    } catch (err) {
      setLoadError(apiErrorMessage(err, "加载设置失败，请稍后重试"));
    } finally {
      setLoading(false);
    }
  }, [syncThresholdDrafts]);

  useEffect(() => {
    void load();
  }, [load]);

  const dirty = useMemo(() => {
    if (!saved || !form) return false;
    return JSON.stringify(saved) !== JSON.stringify({ ...form, updated_at: saved.updated_at });
  }, [saved, form]);

  const blockPercentValue = parsePercentText(blockPercent);
  const warnPercentValue = parsePercentText(warnPercent);

  const thresholdError = useMemo(() => {
    if (!isPercentInRange(blockPercentValue) || !isPercentInRange(warnPercentValue)) {
      const errors: string[] = [];
      if (!isPercentInRange(blockPercentValue)) {
        errors.push("阻塞阈值需为 0–100 的百分比（例如 60 表示比例 0.6）");
      }
      if (!isPercentInRange(warnPercentValue)) {
        errors.push("警告阈值需为 0–100 的百分比（例如 80 表示比例 0.8）");
      }
      return errors.join("；");
    }
    if (warnPercentValue < blockPercentValue) {
      return "警告阈值不能低于阻塞阈值（警告值应 ≥ 阻塞值）";
    }
    return null;
  }, [blockPercentValue, warnPercentValue]);

  function patch(p: Partial<AdminSettings>) {
    setForm((prev) => (prev ? { ...prev, ...p } : prev));
  }

  function handleBlockPercentChange(raw: string) {
    setBlockPercent(raw);
    const percent = parsePercentText(raw);
    if (isPercentInRange(percent)) patch({ quality_block_threshold: percent / 100 });
  }

  function handleWarnPercentChange(raw: string) {
    setWarnPercent(raw);
    const percent = parsePercentText(raw);
    if (isPercentInRange(percent)) patch({ quality_warn_threshold: percent / 100 });
  }

  async function handleSave() {
    if (!form || thresholdError) return;
    setSaving(true);
    try {
      const { updated_at: _omit, ...payload } = form;
      const next = await saveAdminSettings(payload);
      setSaved(next);
      setForm(next);
      syncThresholdDrafts(next);
      toast.success("设置已保存");
    } catch (err) {
      toast.error(settingsErrorMessage(err, "保存失败"));
    } finally {
      setSaving(false);
    }
  }

  function handleDiscard() {
    if (!saved) return;
    setForm(saved);
    syncThresholdDrafts(saved);
  }

  return (
    <div className="mx-auto max-w-[860px] space-y-[18px] pb-20">
      {/* Header 始终渲染：加载失败时页面仍有标题与出口（A-03） */}
      <AdminPageHeader title="系统设置" description="平台配置 · 质量门禁 · 管理员账户" />

      {loading ? (
        <div className="space-y-3" aria-busy="true">
          <p className="sr-only" role="status">
            正在加载系统设置…
          </p>
          {[0, 1, 2].map((i) => (
            <Card key={i} padding={5}>
              <AdminSkeleton.Base className="h-4 w-32" />
              <AdminSkeleton.Base className="mt-4 h-10 w-full" />
              <AdminSkeleton.Base className="mt-3 h-10 w-full" />
            </Card>
          ))}
        </div>
      ) : loadError || !form ? (
        <Card padding={5}>
          <AdminEmptyState
            icon={<AlertTriangle size={28} className="text-warning" />}
            text="无法加载系统设置"
            description={loadError ?? "设置数据为空，请重试"}
            action={
              <Button onClick={() => void load()} variant="secondary" size="sm" icon={RefreshCw}>
                重试
              </Button>
            }
          />
        </Card>
      ) : (
        <>
          {/* 通用配置 */}
          <Section icon={Settings2} title="通用配置" description="站点名称与注册开关">
            <Row
              field={IDS.siteName}
              title="站点名称"
              description="历史字段：当前没有消费者，导航栏与邮件都不读取此值（真实站点名称在构建期环境变量中固定）"
              note={STORED_ONLY_NOTE}
            >
              <TextInput
                id={IDS.siteName.control}
                describedBy={IDS.siteName.description}
                value={form.site_name}
                onChange={(v) => patch({ site_name: v })}
              />
            </Row>
            <Row
              field={IDS.registrationEnabled}
              title="新用户注册"
              description="允许新用户通过手机号注册"
            >
              <Toggle
                id={IDS.registrationEnabled.control}
                labelledBy={IDS.registrationEnabled.label}
                describedBy={IDS.registrationEnabled.description}
                on={form.registration_enabled}
                onChange={(v) => patch({ registration_enabled: v })}
              />
            </Row>
          </Section>

          {/* 质量门禁 */}
          <Section icon={ShieldCheck} title="质量门禁" description="翻译/转录质量阈值与阻塞开关">
            <Row
              field={IDS.qualityBlockEnabled}
              title="翻译质量阻塞"
              description="覆盖率低于阻塞阈值时标记 error，阻止上线"
            >
              <Toggle
                id={IDS.qualityBlockEnabled.control}
                labelledBy={IDS.qualityBlockEnabled.label}
                describedBy={IDS.qualityBlockEnabled.description}
                on={form.quality_block_enabled}
                onChange={(v) => patch({ quality_block_enabled: v })}
              />
            </Row>
            <Row
              field={IDS.qualityBlockThreshold}
              title="阻塞阈值"
              description="覆盖率低于此百分比 -> quality_blocked（百分比 0–100；60% = 后端比例 0.6）"
            >
              <NumberSuffixInput
                id={IDS.qualityBlockThreshold.control}
                describedBy={IDS.qualityBlockThreshold.description}
                invalid={!!thresholdError && !isPercentInRange(blockPercentValue)}
                step="0.1"
                min={0}
                max={100}
                value={blockPercent}
                suffix="%"
                onChange={handleBlockPercentChange}
              />
            </Row>
            <Row
              field={IDS.qualityWarnThreshold}
              title="警告阈值"
              description="覆盖率低于此百分比（且 ≥ 阻塞阈值）-> quality_warning（百分比 0–100）"
            >
              <NumberSuffixInput
                id={IDS.qualityWarnThreshold.control}
                describedBy={IDS.qualityWarnThreshold.description}
                invalid={!!thresholdError && !isPercentInRange(warnPercentValue)}
                step="0.1"
                min={0}
                max={100}
                value={warnPercent}
                suffix="%"
                onChange={handleWarnPercentChange}
              />
            </Row>
            <Row
              field={IDS.hallucinationDetectionEnabled}
              title="转录幻觉检测"
              description="仅登记到数据库；转录回调里的重复/无意义/时长异常/空段检测当前无条件执行，不受此开关控制"
              note={STORED_ONLY_NOTE}
            >
              <Toggle
                id={IDS.hallucinationDetectionEnabled.control}
                labelledBy={IDS.hallucinationDetectionEnabled.label}
                describedBy={IDS.hallucinationDetectionEnabled.description}
                on={form.hallucination_detection_enabled}
                onChange={(v) => patch({ hallucination_detection_enabled: v })}
              />
            </Row>
            {thresholdError && (
              <div
                role="alert"
                className="flex items-center gap-2 py-2.5 text-meta text-error-text"
              >
                <AlertCircle size={14} aria-hidden />
                {thresholdError}
              </div>
            )}
          </Section>

          {/* 视频管线 */}
          <Section icon={Zap} title="视频管线" description="超时、重试、Watchdog">
            <Row
              field={IDS.translateTimeout}
              title="翻译步超时"
              description="单步卡死超此时间由 Watchdog 标记失败"
            >
              <NumberSuffixInput
                id={IDS.translateTimeout.control}
                describedBy={IDS.translateTimeout.description}
                value={String(form.translate_timeout_sec)}
                suffix="秒"
                onChange={(v) => {
                  const n = parseInt(v, 10);
                  if (!Number.isNaN(n)) patch({ translate_timeout_sec: n });
                }}
              />
            </Row>
            <Row field={IDS.downloadTimeout} title="下载步超时" description="yt-dlp 下载超时">
              <NumberSuffixInput
                id={IDS.downloadTimeout.control}
                describedBy={IDS.downloadTimeout.description}
                value={String(form.download_timeout_sec)}
                suffix="秒"
                onChange={(v) => {
                  const n = parseInt(v, 10);
                  if (!Number.isNaN(n)) patch({ download_timeout_sec: n });
                }}
              />
            </Row>
            <Row
              field={IDS.downloadAutoRetry}
              title="下载失败自动重试"
              description="每日 beat 任务重试失败下载，最多 3 次"
            >
              <Toggle
                id={IDS.downloadAutoRetry.control}
                labelledBy={IDS.downloadAutoRetry.label}
                describedBy={IDS.downloadAutoRetry.description}
                on={form.download_auto_retry_enabled}
                onChange={(v) => patch({ download_auto_retry_enabled: v })}
              />
            </Row>
            <Row field={IDS.watchdog} title="Watchdog 轮询" description="每 10 分钟检测全管线卡死">
              <Toggle
                id={IDS.watchdog.control}
                labelledBy={IDS.watchdog.label}
                describedBy={IDS.watchdog.description}
                on={form.watchdog_enabled}
                onChange={(v) => patch({ watchdog_enabled: v })}
              />
            </Row>
          </Section>

          {/* 管理员账户 */}
          <Section icon={UserCog} title="管理员账户" description="拥有后台访问权限的账户">
            <div className="flex flex-col gap-2.5 py-3.5">
              {admins.length === 0 ? (
                <p className="py-2 text-center text-meta text-muted">暂无管理员账户</p>
              ) : (
                admins.map((a) => (
                  <div
                    key={a.id}
                    className="flex items-center gap-3 rounded-md border border-hairline px-3.5 py-2.5"
                  >
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-brand-500 to-brand-400 text-copy font-semibold text-white">
                      {(a.name || "管").slice(0, 1)}
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-copy font-semibold text-ink">
                        {a.name || "管理员"}
                        {a.id === currentUserId && (
                          <span className="ml-1.5 text-meta text-muted">(我)</span>
                        )}
                      </p>
                      <p className="mt-0.5 text-meta text-muted">
                        {MASK_PHONE(a.phone)} · 最近活跃{" "}
                        {a.last_active_at
                          ? new Date(a.last_active_at).toLocaleString("zh-CN", {
                              month: "numeric",
                              day: "numeric",
                              hour: "2-digit",
                              minute: "2-digit",
                            })
                          : "—"}
                      </p>
                    </div>
                    <span className="inline-flex items-center rounded-full bg-brand-50 px-2 py-0.5 text-caption font-semibold text-brand-600">
                      管理员
                    </span>
                  </div>
                ))
              )}
            </div>
          </Section>

          {/* Save bar (prototype 32 .save-bar) */}
          {dirty && (
            <div className="sticky bottom-4 z-20 flex items-center justify-between gap-3 rounded-lg bg-ink px-[18px] py-3 text-canvas shadow-xl">
              <div className="flex items-center gap-2 text-copy">
                <AlertCircle size={15} className="text-warning" aria-hidden />
                有未保存的更改
              </div>
              <div className="flex gap-2">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={handleDiscard}
                  disabled={saving}
                  className="border-canvas/20 bg-transparent text-canvas hover:bg-canvas/10"
                >
                  放弃
                </Button>
                <Button size="sm" onClick={handleSave} disabled={saving || !!thresholdError}>
                  {saving ? (
                    <>
                      <Loader2 size={14} className="animate-spin" />
                      保存中...
                    </>
                  ) : (
                    <>
                      <Save size={14} />
                      保存更改
                    </>
                  )}
                </Button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
