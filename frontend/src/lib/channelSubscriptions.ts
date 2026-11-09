"use client";

import { api } from "@/lib/api";
import { createSharedRequest } from "@/lib/sharedRequest";
import type { ChannelSubscriptionSummary } from "@/types/channels";

type SubscriptionsPayload = ChannelSubscriptionSummary[] | { items: ChannelSubscriptionSummary[] };

/**
 * 首页两处（右栏「正在学」、列表后的「已订阅的频道」）读同一份订阅集合。
 * 共享请求让一次页面加载只打一次 `/discovery/subscriptions`；两处各自在
 * 卸载时 `release()`，离开首页后下一次进入会重新取（订阅状态会变）。
 */
export const channelSubscriptionsRequest = createSharedRequest<ChannelSubscriptionSummary[]>(
  (signal) =>
    api<SubscriptionsPayload>("/api/v1/discovery/subscriptions", { signal }).then((data) =>
      Array.isArray(data) ? data : (data.items ?? [])
    )
);
