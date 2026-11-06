/**
 * 站点级合规与运营配置（构建时注入，前端可见）。
 *
 * NEXT_PUBLIC_* 在镜像构建时注入；可选公示信息缺失时不显示占位。
 */
export const siteConfig = {
  /** 产品品牌名（构建期固定常量，非 env 注入）。UI 品牌显示一律引用此常量。 */
  brandName: "SeeWord",
  siteUrl: process.env.NEXT_PUBLIC_SITE_URL || "https://seeword.top",
  /** 个体工商户名称。 */
  companyName: process.env.NEXT_PUBLIC_COMPANY_NAME || "",
  /** 统一社会信用代码。 */
  companyUscc: process.env.NEXT_PUBLIC_COMPANY_USCC || "",
  /** ICP 备案号，如"京ICP备2025000001号"。 */
  icpBeian: process.env.NEXT_PUBLIC_ICP_BEIAN || "",
  /** 公安网安备案号，如"京公网安备11000000000001号"。 */
  policeBeian: process.env.NEXT_PUBLIC_POLICE_BEIAN || "",
} as const;

/** 是否已有任意备案/主体信息可公示。 */
export const hasComplianceInfo = Boolean(
  siteConfig.companyName || siteConfig.icpBeian || siteConfig.policeBeian
);
