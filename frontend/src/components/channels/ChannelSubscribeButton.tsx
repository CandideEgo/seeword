"use client";
import { useEffect, useState } from "react";
import { BookmarkPlus, Check } from "lucide-react";
import { api } from "@/lib/api";
import { toastApiError } from "@/lib/errors";
import {
  SUBSCRIPTION_EVENT,
  publishSubscription,
  type SubscriptionChange,
} from "@/lib/subscriptionEvents";
import { Button } from "@/components/ui/Button";

interface Subscription {
  id: string;
  slug: string;
  name: string;
}
/** 频道主操作：订阅/已订阅。设计稿里是唯一的橙色主按钮（btn-primary）。 */
export function ChannelSubscribeButton({ slug }: { slug: string }) {
  const [subscribed, setSubscribed] = useState<boolean | null>(null);
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setFailed(false);
    api<Subscription[]>("/api/v1/discovery/subscriptions", { signal: controller.signal })
      .then((items) => setSubscribed(items.some((c) => c.slug === slug)))
      .catch((err) => {
        if (!controller.signal.aborted) {
          setFailed(true);
          toastApiError(err, "订阅状态读取失败");
        }
      });
    return () => controller.abort();
  }, [slug, attempt]);
  useEffect(() => {
    const listener = (event: Event) => {
      const change = (event as CustomEvent<SubscriptionChange>).detail;
      if (change.slug === slug) setSubscribed(change.subscribed);
    };
    window.addEventListener(SUBSCRIPTION_EVENT, listener);
    return () => window.removeEventListener(SUBSCRIPTION_EVENT, listener);
  }, [slug, attempt]);
  async function toggle() {
    if (busy || subscribed === null) return;
    setBusy(true);
    try {
      const result = await api<{ subscribed: boolean }>(
        `/api/v1/discovery/subscriptions/${encodeURIComponent(slug)}`,
        { method: subscribed ? "DELETE" : "PUT" }
      );
      setSubscribed(result.subscribed);
      publishSubscription({ slug, subscribed: result.subscribed });
    } catch (err) {
      toastApiError(err, "订阅操作失败，请重试");
    } finally {
      setBusy(false);
    }
  }
  return (
    <Button
      variant={subscribed === true ? "outline" : "primary"}
      icon={subscribed === true ? Check : BookmarkPlus}
      disabled={busy || (subscribed === null && !failed)}
      onClick={failed && subscribed === null ? () => setAttempt((n) => n + 1) : toggle}
      aria-pressed={subscribed === true}
    >
      {failed && subscribed === null
        ? "重试读取订阅状态"
        : subscribed === null
          ? "读取订阅状态…"
          : subscribed
            ? "已订阅 · 取消"
            : "订阅频道"}
    </Button>
  );
}
