"use client";

import { useEffect } from "react";
import { Home } from "lucide-react";
import { ErrorState } from "@/components/common/ErrorState";
import { Button } from "@/components/ui/Button";
import { LinkButton } from "@/components/ui/LinkButton";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  const message = "页面暂时未能加载，请重试或返回首页。";

  return (
    <ErrorState
      title="页面加载失败"
      message={message}
      fullPage
      landmark
      action={
        <div className="flex flex-wrap items-center justify-center gap-3">
          <Button onClick={reset}>重试</Button>
          <LinkButton href="/" variant="outline" icon={Home}>
            回首页
          </LinkButton>
        </div>
      }
    />
  );
}
