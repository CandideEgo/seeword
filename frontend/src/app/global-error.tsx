"use client";

import { useEffect } from "react";
import { ErrorState } from "@/components/common/ErrorState";
import { Button } from "@/components/ui/Button";

/**
 * Root-layout error boundary — the last-resort catch for errors that escape
 * segment-level error.tsx files (including failed first-time chunk loads
 * after a deploy, which otherwise leave a permanently white page until the
 * user manually refreshes).
 *
 * Must render its own <html>/<body> — it replaces the root layout.
 * Recovery is a hard reload rather than reset(): a stale/missing JS chunk
 * won't be fixed by re-rendering the same broken module graph.
 */
export default function GlobalError({ error }: { error: Error & { digest?: string } }) {
  useEffect(() => {
    // 根错误边界没有更上层的上报通道，只能把原始错误留在控制台便于排查。
    console.error(error);
  }, [error]);

  return (
    <html lang="zh-CN">
      <body>
        <ErrorState
          title="页面加载失败"
          message="资源加载出错，请刷新重试"
          fullPage
          landmark
          action={
            <Button onClick={() => window.location.reload()} className="mt-5">
              刷新页面
            </Button>
          }
        />
      </body>
    </html>
  );
}
