import type { Metadata } from "next";
import { AstryxProvider } from "@/components/common/AstryxProvider";

export const metadata: Metadata = {
  title: "我的词汇 — SeeWord",
  description: "复习生词，管理你的词库。",
};

export default function Layout({ children }: { children: React.ReactNode }) {
  return <AstryxProvider>{children}</AstryxProvider>;
}
