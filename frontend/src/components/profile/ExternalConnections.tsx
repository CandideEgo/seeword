"use client";

import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { api, ApiError } from "@/lib/api";
import { formatCount } from "@/lib/format";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { ConnectionResourcePicker } from "@/components/profile/ConnectionResourcePicker";
import { PendingLearningIntents } from "@/components/profile/PendingLearningIntents";
import {
  needsLearningResources,
  toggleConnectionScope,
  type LearningResourceLimits,
} from "@/lib/learningConnections";
import {
  EXTERNAL_SCOPES,
  type ExternalConnection,
  type ExternalCredentialCreated,
} from "@/types/teaching";

export function ExternalConnections() {
  const [connections, setConnections] = useState<ExternalConnection[]>([]);
  const [available, setAvailable] = useState<boolean | null>(null);
  const [canCreate, setCanCreate] = useState(false);
  const [host, setHost] = useState("Codex");
  const [scopes, setScopes] = useState<string[]>(["materials:read"]);
  const [resourceLimits, setResourceLimits] = useState<LearningResourceLimits>({
    lesson_ids: [],
    word_ids: [],
  });
  const needsResources = needsLearningResources(scopes);
  const hasResources = resourceLimits.lesson_ids.length > 0 || resourceLimits.word_ids.length > 0;
  const [busy, setBusy] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [error, setError] = useState("");
  const [credential, setCredential] = useState<ExternalCredentialCreated | null>(null);
  const [revoke, setRevoke] = useState<ExternalConnection | null>(null);
  const [endpoint, setEndpoint] = useState("");
  const load = useCallback(async () => {
    try {
      const data = await api<{ items: ExternalConnection[]; can_create: boolean }>(
        "/api/v1/external-connections"
      );
      setConnections(data.items);
      setCanCreate(data.can_create === true);
      setAvailable(true);
      setError("");
    } catch (err) {
      if (
        err instanceof ApiError &&
        ([403, 404].includes(err.status) || err.code === "SERVICE_UNAVAILABLE")
      ) {
        setAvailable(false);
        return;
      }
      setError("AI 连接暂时无法读取，请稍后重试。");
    }
  }, []);
  useEffect(() => {
    void load();
    setEndpoint(`${window.location.origin}/api/v1/mcp/`);
  }, [load]);
  const create = async () => {
    if (busy) return;
    setBusy(true);
    setError("");
    setCredential(null);
    try {
      const result = await api<ExternalCredentialCreated>("/api/v1/external-connections", {
        method: "POST",
        body: JSON.stringify({
          host_label: host,
          audience: "model",
          granted_scopes: scopes,
          ...(needsResources ? { resource_limits: resourceLimits } : {}),
        }),
      });
      setCredential(result);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "创建连接失败。");
    } finally {
      setBusy(false);
    }
  };
  const rotate = async (connection: ExternalConnection) => {
    if (busy) return;
    setBusy(true);
    setCredential(null);
    setError("");
    try {
      setCredential(
        await api<ExternalCredentialCreated>(
          `/api/v1/external-connections/${encodeURIComponent(connection.id)}/rotate`,
          { method: "POST" }
        )
      );
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "更新凭据失败。");
    } finally {
      setBusy(false);
    }
  };
  const revokeConnection = async () => {
    if (!revoke || busy) return;
    setBusy(true);
    setError("");
    try {
      await api(`/api/v1/external-connections/${encodeURIComponent(revoke.id)}/revoke`, {
        method: "POST",
      });
      if (credential?.connection.id === revoke.id) setCredential(null);
      setRevoke(null);
      await load();
      toast.success("连接已撤销");
    } catch (err) {
      setError(err instanceof Error ? err.message : "撤销失败，请重试。");
    } finally {
      setBusy(false);
    }
  };
  const copy = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      toast.success("已复制");
    } catch {
      setError("复制失败，请选择文本手动复制。");
    }
  };
  if (available === false) return null;
  if (available === null && !error) return null;
  if (available && !canCreate && !connections.length) return null;
  return (
    <section className="space-y-4 border-t border-hairline pt-4" aria-label="已连接 AI">
      <div>
        <h3 className="text-copy font-semibold text-ink">已连接 AI</h3>
      </div>
      {error && (
        <div role="alert" className="space-y-2">
          <p className="text-meta text-error-text">{error}</p>
          <Button variant="outline" size="sm" onClick={() => void load()}>
            重新读取
          </Button>
        </div>
      )}
      <PendingLearningIntents
        refreshKey={connections
          .map((connection) => `${connection.id}:${connection.revoked_at ?? ""}`)
          .join("|")}
      />
      {!!connections.length && (
        <ul className="divide-y divide-hairline">
          {connections.map((c) => {
            const inactive = !!c.revoked_at || new Date(c.expires_at).getTime() <= Date.now();
            return (
              <li key={c.id} className="space-y-2 py-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="text-copy font-semibold text-ink">{c.host_label}</span>
                  <span className="text-meta text-muted">
                    {c.revoked_at
                      ? "已撤销"
                      : inactive
                        ? "已到期"
                        : `有效至 ${new Date(c.expires_at).toLocaleString()}`}
                  </span>
                </div>
                <p className="text-caption text-muted">
                  {EXTERNAL_SCOPES.filter(([scope]) => c.granted_scopes.includes(scope))
                    .map(([, label]) => label)
                    .join(" · ")}
                </p>
                {c.audience === "application" && (
                  <p className="text-meta text-body">用途：第三方应用，不含向模型披露的授权</p>
                )}
                {c.resource_limits?.lesson_ids && c.resource_limits?.word_ids && (
                  <p className="text-meta text-body">
                    资料范围：{formatCount(c.resource_limits.lesson_ids.length)} 门课程，
                    {formatCount(c.resource_limits.word_ids.length)} 个词语
                  </p>
                )}
                {!inactive && (
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={busy || !canCreate}
                      onClick={() => void rotate(c)}
                    >
                      更新凭据
                    </Button>
                    <Button variant="ghost" size="sm" disabled={busy} onClick={() => setRevoke(c)}>
                      撤销连接
                    </Button>
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      )}
      {credential && (
        <div
          className="space-y-3 rounded-sm border border-brand-500 bg-brand-50 p-4"
          role="region"
          aria-label="新连接凭据"
        >
          <p className="text-copy font-semibold text-ink">凭据只在此处显示一次</p>
          <p className="text-meta text-body">
            仅填写到宿主的安全 MCP 配置中。关闭后无法再次查看；更新凭据会让旧凭据失效。
          </p>
          <label htmlFor="external-endpoint" className="block text-meta text-body">
            MCP 服务地址
          </label>
          <Input id="external-endpoint" readOnly value={endpoint} className="w-full" />
          <Button variant="outline" size="sm" onClick={() => void copy(endpoint)}>
            复制服务地址
          </Button>
          <label htmlFor="external-token" className="block text-meta text-body">
            Bearer 凭据
          </label>
          <Input
            id="external-token"
            type="password"
            autoComplete="off"
            readOnly
            value={credential.token}
            className="w-full"
          />
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" size="sm" onClick={() => void copy(credential.token)}>
              复制凭据
            </Button>
            <Button variant="ghost" size="sm" onClick={() => setCredential(null)}>
              已保存，关闭显示
            </Button>
          </div>
          <p className="text-caption text-muted">请勿粘贴到普通聊天、代码仓库或共享文档中。</p>
        </div>
      )}
      {available && canCreate && (
        <details
          className="rounded-sm border border-hairline p-3"
          onToggle={(event) => setCreateOpen(event.currentTarget.open)}
        >
          <summary className="cursor-pointer text-copy font-semibold text-ink">
            添加 AI 连接
          </summary>
          <div className="mt-3 space-y-3">
            <label htmlFor="external-host" className="block text-meta text-body">
              宿主
            </label>
            <Select id="external-host" value={host} onChange={(e) => setHost(e.target.value)}>
              <option>Codex</option>
              <option>Claude Code</option>
              <option>Claude</option>
              <option>DeepSeek Harness</option>
              <option>WorkBuddy</option>
            </Select>
            <p className="text-caption text-muted">
              各宿主需要支持自定义远程 MCP；豆包 App 与网页接入能力仍在探测。
            </p>
            <fieldset className="space-y-2">
              <legend className="mb-2 text-meta font-semibold text-ink">允许的操作</legend>
              {EXTERNAL_SCOPES.map(([scope, label]) => (
                <label key={scope} className="flex items-start gap-2 text-meta text-body">
                  <input
                    type="checkbox"
                    checked={scopes.includes(scope)}
                    onChange={(e) =>
                      setScopes((current) =>
                        toggleConnectionScope(current, scope, e.target.checked)
                      )
                    }
                    className="mt-0.5 accent-action-primary"
                  />
                  <span>{label}</span>
                </label>
              ))}
            </fieldset>
            {createOpen && needsResources && (
              <ConnectionResourcePicker
                value={resourceLimits}
                onChange={setResourceLimits}
                disabled={busy}
              />
            )}
            <p className="text-meta text-muted">连接 7 日后到期；未选择的资料不会授权。</p>
            <Button
              size="sm"
              loading={busy}
              disabled={!scopes.length || !!credential || (needsResources && !hasResources)}
              onClick={() => void create()}
            >
              创建限时连接
            </Button>
          </div>
        </details>
      )}
      <ConfirmDialog
        open={!!revoke}
        onClose={() => setRevoke(null)}
        title={`撤销 ${revoke?.host_label ?? "AI"} 连接？`}
        message="撤销后该宿主不能再访问学习数据或提交作答。已经保存的学习记录会保留。"
        confirmLabel="撤销连接"
        cancelLabel="保留连接"
        busy={busy}
        onConfirm={() => void revokeConnection()}
      />
    </section>
  );
}
