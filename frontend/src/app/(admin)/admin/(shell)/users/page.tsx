"use client";

import { useState, useCallback, useEffect, useRef, type RefObject } from "react";
import { toast } from "sonner";
import { toastApiError } from "@/lib/errors";
import { usePaginatedList } from "@/hooks/usePaginatedList";
import { useAdminAuthStore } from "@/stores/adminAuthStore";
import {
  Activity,
  Ban,
  ChevronDown,
  RefreshCw,
  Shield,
  ShieldCheck,
  ShieldOff,
  UserCog,
  Users,
} from "lucide-react";

import { cn } from "@/lib/utils";
import {
  AdminPageHeader,
  AdminSearchInput,
  AdminDropdown,
  AdminConfirmDialog,
  AdminSkeleton,
  AdminEmptyState,
} from "@/components/admin/ui";
import { StatChip } from "@/components/admin/StatChip";
import { FilterPills } from "@/components/admin/FilterPills";
import { Pagination } from "@/components/admin/Pagination";
import { Badge } from "@/components/common/Badge";
import { Button } from "@/components/ui/Button";
import { Avatar } from "@/components/ui/Avatar";
import type { AdminStats, AdminUser } from "@/types";
import { getAdminStats, listUsers, promoteUser, setUserBanned } from "@/lib/adminData";
import { Card } from "@/components/ui/Card";

// ---------------------------------------------------------------------------
// Filter options
// ---------------------------------------------------------------------------

const ROLE_FILTERS = [
  { key: "", label: "全部角色" },
  { key: "admin", label: "管理员" },
  { key: "user", label: "普通用户" },
];

const PAGE_SIZE = 20;

type RowAction = "ban" | "promote";

// ---------------------------------------------------------------------------
// Stat chip (prototype 28 .stat-chip)
// ---------------------------------------------------------------------------

/** 当前筛选条件的可读描述（用于筛选后为空时的空状态）。 */
function filterSummary(roleFilter: string, keyword: string): string {
  const parts: string[] = [];
  if (roleFilter) parts.push(`角色「${ROLE_FILTERS.find((f) => f.key === roleFilter)?.label}」`);
  if (keyword.trim()) parts.push(`关键词「${keyword.trim()}」`);
  return parts.join(" · ");
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export default function AdminUsersPage() {
  const [roleFilter, setRoleFilter] = useState("");
  const [keyword, setKeyword] = useState("");
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [stats, setStats] = useState<AdminStats | null>(null);
  // 行内动作的在途保护：同一时刻只允许一个动作，按钮/菜单项在途禁用（A-07/A-36）。
  // ref 是同步闸门：同一 tick 的两次点击也会被拦下（state 要等下一次渲染才更新）。
  const busyRef = useRef(false);
  /** 行操作菜单的触发按钮；确认框关闭后把焦点还给它，而不是落到 body。 */
  const menuTriggerRef = useRef<HTMLElement | null>(null);
  const [busyAction, setBusyAction] = useState<{ id: string; kind: RowAction } | null>(null);
  const [confirmPrompt, setConfirmPrompt] = useState<{
    title: string;
    description: string;
    danger: boolean;
    confirmLabel: string;
    onConfirm: () => void;
  } | null>(null);

  const currentUserId = useAdminAuthStore((s) => s.user?.sub ?? null);

  useEffect(() => {
    getAdminStats()
      .then(setStats)
      .catch(() => undefined);
  }, []);

  const {
    items: users,
    setItems: setUsers,
    page,
    setPage,
    hasMore,
    total,
    loading,
    error,
    reload,
  } = usePaginatedList<AdminUser>({
    fetcher: (pg) =>
      listUsers({
        page: pg,
        page_size: PAGE_SIZE,
        role: roleFilter,
        keyword,
      }),
    mode: "replace",
    filters: [roleFilter, keyword],
  });

  const patchUser = useCallback(
    (id: string, patch: Partial<AdminUser>) => {
      setUsers((prev) => prev.map((u) => (u.id === id ? { ...u, ...patch } : u)));
    },
    [setUsers]
  );

  // --- Actions ---

  const withBusy = useCallback(
    async (user: AdminUser, kind: RowAction, fn: () => Promise<void>) => {
      if (busyRef.current) return;
      busyRef.current = true;
      setBusyAction({ id: user.id, kind });
      try {
        await fn();
      } finally {
        busyRef.current = false;
        setBusyAction(null);
      }
    },
    []
  );

  function doBan(user: AdminUser) {
    return withBusy(user, "ban", async () => {
      const next = !user.is_banned;
      try {
        await setUserBanned(user.id, next);
        patchUser(user.id, { is_banned: next });
        toast.success(next ? "已封禁" : "已解封");
      } catch (err) {
        toastApiError(err);
      }
    });
  }

  function doPromote(user: AdminUser) {
    return withBusy(user, "promote", async () => {
      const next = (user.role || "user") === "admin" ? "user" : "admin";
      try {
        await promoteUser(user.id, next);
        patchUser(user.id, { role: next });
        toast.success("已更新角色");
      } catch (err) {
        toastApiError(err);
      }
    });
  }

  const hasFilters = Boolean(roleFilter || keyword.trim());

  function clearFilters() {
    setRoleFilter("");
    setKeyword("");
  }

  function retryLoad() {
    reload();
  }

  /** 用户列表的「错误 / 真空 / 筛选后为空」三态（A-04）。 */
  function renderEmpty() {
    if (error) {
      return (
        <AdminEmptyState
          text="加载用户列表失败"
          description={error}
          action={
            <Button onClick={retryLoad} variant="secondary" size="sm" icon={RefreshCw}>
              重试
            </Button>
          }
        />
      );
    }
    if (hasFilters) {
      return (
        <AdminEmptyState
          text="没有匹配的用户"
          description={`当前筛选：${filterSummary(roleFilter, keyword)}`}
          action={
            <Button onClick={clearFilters} variant="secondary" size="sm">
              清除筛选
            </Button>
          }
        />
      );
    }
    return <AdminEmptyState text="暂无用户" description="还没有注册用户。" />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <AdminPageHeader
        title="用户管理"
        description={`共 ${total} 位用户`}
        actions={
          <Button
            onClick={retryLoad}
            disabled={loading}
            variant="secondary"
            size="sm"
            icon={RefreshCw}
            className={loading ? "[&_svg]:animate-spin" : ""}
          >
            刷新
          </Button>
        }
      />

      {/* Stat strip (prototype 28) */}
      <div className="flex flex-wrap gap-2.5">
        <StatChip
          icon={Users}
          value={stats ? stats.total_users.toLocaleString() : "—"}
          label="总用户"
          iconClass="bg-brand-50 text-brand-600"
        />
        <StatChip
          icon={Activity}
          value={stats ? stats.active_users_today.toLocaleString() : "—"}
          label="今日活跃"
          iconClass="bg-success-soft text-success"
        />
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-4">
        <FilterPills options={ROLE_FILTERS} value={roleFilter} onChange={setRoleFilter} />
        <AdminSearchInput
          value={keyword}
          onChange={setKeyword}
          placeholder="搜索姓名 / 手机号..."
          ariaLabel="搜索用户（姓名 / 手机号）"
          className="ml-auto w-64"
        />
      </div>

      {/* Table —— 不裁切容器（A-22）：桌面端保留圆角可见的溢出，菜单不再被 Card 裁掉；
          窄屏用横向滚动承接超宽表格。 */}
      <Card padding={0}>
        <div className="overflow-x-auto md:overflow-x-visible">
          <table className="w-full text-copy">
            <thead>
              <tr className="border-b border-hairline text-left">
                {[
                  ["用户", "text-left"],
                  ["角色", "text-left"],
                  ["学习", "text-left"],
                  ["状态", "text-left"],
                  ["注册时间", "text-left"],
                  ["操作", "text-right"],
                ].map(([h, align]) => (
                  <th
                    key={h}
                    scope="col"
                    className={cn(
                      "px-4 py-3 text-meta font-medium uppercase tracking-wider text-muted",
                      align
                    )}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-hairline">
              {loading ? (
                <AdminSkeleton.TableRows rows={5} cols={6} />
              ) : users.length === 0 ? (
                <tr>
                  <td colSpan={6} className="p-0">
                    {renderEmpty()}
                  </td>
                </tr>
              ) : (
                users.map((u) => {
                  const isExpanded = expandedId === u.id;
                  const isSelf = currentUserId === u.id;
                  const rowBusy = busyAction?.id === u.id;
                  return (
                    <UserRow
                      key={u.id}
                      user={u}
                      isExpanded={isExpanded}
                      isSelf={isSelf}
                      busy={rowBusy}
                      returnFocusRef={menuTriggerRef}
                      onToggleExpand={() => setExpandedId(isExpanded ? null : u.id)}
                      onBan={() => {
                        if (!u.is_banned) {
                          setConfirmPrompt({
                            title: "封禁用户",
                            description: `确认封禁用户「${u.name || u.phone}」？封禁后该用户将无法登录。`,
                            danger: true,
                            confirmLabel: "确认封禁",
                            onConfirm: () => doBan(u),
                          });
                        } else {
                          doBan(u);
                        }
                      }}
                      onPromote={() => {
                        const next = (u.role || "user") === "admin" ? "user" : "admin";
                        const verb = next === "admin" ? "提升为管理员" : "降级为普通用户";
                        setConfirmPrompt({
                          title: verb,
                          description: `确认将「${u.name || u.phone}」${verb}？`,
                          danger: false,
                          confirmLabel: "确认",
                          onConfirm: () => doPromote(u),
                        });
                      }}
                    />
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Pagination */}
      <Pagination
        page={page}
        hasMore={hasMore}
        total={total}
        pageSize={PAGE_SIZE}
        loading={loading}
        onPrev={() => setPage((p) => Math.max(1, p - 1))}
        onNext={() => setPage((p) => p + 1)}
      />

      {/* Confirm Dialog */}
      <AdminConfirmDialog
        open={!!confirmPrompt}
        onClose={() => setConfirmPrompt(null)}
        onConfirm={() => {
          confirmPrompt?.onConfirm();
          setConfirmPrompt(null);
        }}
        title={confirmPrompt?.title ?? ""}
        description={confirmPrompt?.description}
        confirmLabel={confirmPrompt?.confirmLabel}
        danger={confirmPrompt?.danger}
        returnFocusRef={menuTriggerRef}
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// User Row
// ---------------------------------------------------------------------------

function UserRow({
  user: u,
  isExpanded,
  isSelf,
  busy,
  onToggleExpand,
  onBan,
  onPromote,
  returnFocusRef,
}: {
  user: AdminUser;
  isExpanded: boolean;
  isSelf: boolean;
  busy: boolean;
  onToggleExpand: () => void;
  onBan: () => void;
  onPromote: () => void;
  /** 见 `AdminDropdownProps.returnFocusRef`：确认框关闭后焦点回到这里。 */
  returnFocusRef: RefObject<HTMLElement | null>;
}) {
  const detailId = `user-detail-${u.id}`;
  const displayName = u.name || u.phone || "用户";
  // 自我保护（A-36）：后端会 400 拒绝，前端把不可用动作直接置灰并说明原因。
  const selfTitle = "不能对自己执行该操作";

  return (
    <>
      <tr
        className={cn(
          "transition-colors cursor-pointer",
          isExpanded ? "bg-surface-soft/60" : "hover:bg-surface-soft/40"
        )}
        onClick={onToggleExpand}
      >
        <td className="px-4 py-3">
          <div className="flex items-center gap-3">
            {/* 行展开的唯一入口按钮：可聚焦、可键盘触发，并声明展开状态（A-15/A-38）。 */}
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onToggleExpand();
              }}
              aria-expanded={isExpanded}
              aria-controls={detailId}
              aria-label={`${displayName} 的详情`}
              className="rounded-sm p-1 text-muted-soft hover:text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
            >
              <ChevronDown
                size={14}
                aria-hidden
                className={cn("transition-transform", !isExpanded && "-rotate-90")}
              />
            </button>
            <Avatar
              src={u.avatar_url}
              name={u}
              seed={u.id}
              gender={u.gender}
              size="md"
              alt={u.name || u.phone || "用户头像"}
            />
            <div className="min-w-0">
              <p className="font-medium text-ink truncate max-w-[140px]">{u.name || "未命名"}</p>
              <p className="text-meta text-muted truncate max-w-[140px]">{u.phone || "-"}</p>
            </div>
          </div>
        </td>
        <td className="px-4 py-3">
          {(u.role || "user") === "admin" ? (
            <Badge tone="brand" icon={ShieldCheck}>
              管理员
            </Badge>
          ) : (
            <span className="text-meta text-muted">普通用户</span>
          )}
          {isSelf && <span className="ml-2 text-caption text-muted-soft">（本人）</span>}
        </td>
        <td className="px-4 py-3">
          <span className="font-mono text-copy text-body">{u.learned_words ?? 0}</span>
          <span className="text-meta text-muted"> 词 · {u.videos_watched ?? 0} 视频</span>
        </td>
        <td className="px-4 py-3">
          {u.is_banned ? (
            <Badge tone="red" icon={Ban}>
              已封禁
            </Badge>
          ) : (
            <span className="inline-flex items-center gap-1.5 text-meta text-success-text">
              <span className="h-1.5 w-1.5 rounded-full bg-success" />
              正常
            </span>
          )}
        </td>
        <td className="px-4 py-3 text-meta text-muted">
          {new Date(u.created_at).toLocaleDateString("zh-CN")}
        </td>
        <td className="px-4 py-3 text-right" onClick={(e) => e.stopPropagation()}>
          <div title={isSelf ? selfTitle : undefined} className="inline-block">
            <AdminDropdown
              label={`${displayName} 的操作`}
              returnFocusRef={returnFocusRef}
              items={[
                {
                  key: "ban",
                  label: u.is_banned ? "解封用户" : "封禁用户",
                  icon: u.is_banned ? ShieldOff : Shield,
                  danger: !u.is_banned,
                  disabled: isSelf || busy,
                  onClick: onBan,
                },
                {
                  key: "promote",
                  label: (u.role || "user") === "admin" ? "降级为普通用户" : "提升为管理员",
                  icon: UserCog,
                  disabled: isSelf || busy,
                  onClick: onPromote,
                },
              ]}
            />
          </div>
        </td>
      </tr>

      {/* Expanded detail */}
      {isExpanded && (
        <tr id={detailId} className="bg-surface-soft/40">
          <td colSpan={6} className="px-4 py-4">
            <div className="grid grid-cols-3 gap-3">
              <DetailStat label="观看视频" value={u.videos_watched ?? 0} />
              <DetailStat label="等级" value={u.level || "-"} />
              <DetailStat
                label="注册时间"
                value={new Date(u.created_at).toLocaleDateString("zh-CN")}
              />
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

// ---------------------------------------------------------------------------
// Detail Stat
// ---------------------------------------------------------------------------

function DetailStat({ label, value }: { label: string; value: string | number }) {
  return (
    <Card padding={3}>
      <p className="text-caption uppercase tracking-wider text-muted">{label}</p>
      <p className="mt-1 text-copy font-semibold text-ink">{value}</p>
    </Card>
  );
}
