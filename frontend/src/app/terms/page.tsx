import type { Metadata } from "next";
import { siteConfig } from "@/lib/siteConfig";
import { LegalLayout, type LegalSection } from "@/components/legal/LegalLayout";

export const metadata: Metadata = {
  robots: { index: true, follow: true },
  title: "用户协议 - SeeWord",
  description: "SeeWord 用户协议",
};

// 主体名称：已配置则显示具体名称，未配置时用中性表述（上线可用，
// 避免向最终用户暴露"待补充"这类开发态文案）。
const operatorName = siteConfig.companyName || "本站运营方";
const uscc = siteConfig.companyUscc;

const SECTIONS: LegalSection[] = [
  { id: "sec-1", title: "一、服务性质" },
  { id: "sec-2", title: "二、服务与费用" },
  { id: "sec-3", title: "三、账号" },
  { id: "sec-4", title: "四、内容与知识产权" },
  { id: "sec-5", title: "五、免责声明" },
  { id: "sec-6", title: "六、协议变更" },
];

function H2({ children }: { children: React.ReactNode }) {
  return <h2 className="text-title font-semibold text-ink">{children}</h2>;
}

export default function TermsPage() {
  return (
    <LegalLayout
      title="用户协议"
      updatedAt="2026 年 10 月 19 日"
      sections={SECTIONS}
      siblingHref="/privacy"
      siblingLabel="查看隐私政策"
    >
      <section id="sec-1" className="scroll-mt-10 space-y-3">
        <H2>一、服务性质</H2>
        <p>
          SeeWord（以下简称“本站”）由 {operatorName}
          {uscc ? `（统一社会信用代码：${uscc}）` : ""}{" "}
          运营，是面向中文用户的英语学习工具，提供视频字幕、词汇学习、原声重听与阅读练习等服务。
        </p>
      </section>

      <section id="sec-2" className="scroll-mt-10 space-y-3">
        <H2>二、服务与费用</H2>
        <p>
          本站面向登录用户免费开放全部现有功能（视频字幕、词汇学习、听力与试卷练习等），
          不提供付费会员或其他收费项目，站内也不设购买入口。
        </p>
        <p>
          本站为非经营性工具展示平台，不进行在线支付。如未来推出收费服务，会先在站内公示价格与服务条款，
          不会在本协议未更新的情况下开始收费。
        </p>
      </section>

      <section id="sec-3" className="scroll-mt-10 space-y-3">
        <H2>三、账号</H2>
        <p>
          用户应使用真实信息注册账号，妥善保管账号与密码。因账号保管不善造成的损失由用户自行承担。
          本站有权对违反法律法规或本协议的账号采取限制或封禁措施。
        </p>
      </section>

      <section id="sec-4" className="scroll-mt-10 space-y-3">
        <H2>四、内容与知识产权</H2>
        <p>
          本站引用的视频内容来源自第三方平台，相关权利归原作者所有，供英语学习使用。
          用户在本站产生的学习数据归用户本人所有。未经授权，不得复制、转载或商用本站的原创内容。
        </p>
      </section>

      <section id="sec-5" className="scroll-mt-10 space-y-3">
        <H2>五、免责声明</H2>
        <p>
          本站提供的翻译、词汇标注、AI 词汇注释等功能仅供参考学习，不构成专业语言评判。
          因网络、设备或第三方服务原因导致的功能中断，本站不承担责任。
        </p>
      </section>

      <section id="sec-6" className="scroll-mt-10 space-y-3">
        <H2>六、协议变更</H2>
        <p>
          本站可根据法律法规及运营需要更新本协议，更新后将在本页面公示。继续使用即视为接受变更。
        </p>
      </section>
    </LegalLayout>
  );
}
