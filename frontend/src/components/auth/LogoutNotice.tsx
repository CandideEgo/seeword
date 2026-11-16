"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { ShieldAlert } from "lucide-react";

function RevocationWarning() {
  const params = useSearchParams();
  if (params.get("revocation") !== "unconfirmed") return null;
  return (
    <p
      role="alert"
      className="mt-5 flex items-start gap-2 rounded-md border border-warning/30 bg-warning-soft p-3 text-meta leading-relaxed text-warning-text"
    >
      <ShieldAlert size={17} className="mt-0.5 shrink-0" aria-hidden />
      <span>你已退出本机。服务端未能确认撤销，原会话可能在到期前仍有效。</span>
    </p>
  );
}

export function LogoutNotice() {
  return (
    <Suspense fallback={null}>
      <RevocationWarning />
    </Suspense>
  );
}
