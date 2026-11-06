import { describe, expect, it } from "vitest";

import {
  ACTIVE_SCOPE,
  MAIN_NAV,
  SECONDARY_NAV,
  navigationActive,
  type NavItem,
} from "@/lib/navigation";

const ALL_NAV: NavItem[] = [...MAIN_NAV, ...SECONDARY_NAV];

/** 所有导航项里，认领这条 pathname 的那些 href。 */
function activeHrefs(pathname: string): string[] {
  return ALL_NAV.filter((item) => navigationActive(pathname, item.href)).map((item) => item.href);
}

/** 归属表里的全部 scope 前缀（去掉重复的同一个 href 组内重复）。 */
function allScopes(): string[] {
  return Object.values(ACTIVE_SCOPE).flat();
}

describe("导航项：一级 5 项 + 资料库 3 项", () => {
  it("MAIN_NAV 恰好 5 项，href 顺序固定", () => {
    expect(MAIN_NAV).toHaveLength(5);
    expect(MAIN_NAV.map((item) => item.href)).toEqual([
      "/",
      "/channels",
      "/practice",
      "/vocabulary",
      "/profile",
    ]);
  });

  it("SECONDARY_NAV 恰好 3 项，href 顺序固定", () => {
    expect(SECONDARY_NAV).toHaveLength(3);
    expect(SECONDARY_NAV.map((item) => item.href)).toEqual([
      "/favorites",
      "/history",
      "/notifications",
    ]);
  });

  it("两组 href 无重复，合计 8 项", () => {
    const hrefs = ALL_NAV.map((item) => item.href);
    expect(new Set(hrefs).size).toBe(8);
    expect(hrefs).toHaveLength(8);
  });

  it("label 非空且不重复", () => {
    const labels = ALL_NAV.map((item) => item.label);
    expect(labels.every((label) => label.trim().length > 0)).toBe(true);
    expect(new Set(labels).size).toBe(8);
  });

  it("每项 icon 非空", () => {
    for (const item of ALL_NAV) {
      expect(item.icon, `${item.href} 缺 icon`).toBeTruthy();
    }
  });

  it("shortcut 只属于一级，且恰为 1~5", () => {
    expect(MAIN_NAV.map((item) => item.shortcut)).toEqual(["1", "2", "3", "4", "5"]);
    expect(SECONDARY_NAV.every((item) => item.shortcut === undefined)).toBe(true);
  });

  it("showBadge 只在 /vocabulary", () => {
    expect(ALL_NAV.filter((item) => item.showBadge).map((item) => item.href)).toEqual([
      "/vocabulary",
    ]);
  });
});

describe("归属表 ACTIVE_SCOPE", () => {
  it("键恰好是 9 个导航项 href", () => {
    expect(Object.keys(ACTIVE_SCOPE).sort()).toEqual(ALL_NAV.map((item) => item.href).sort());
  });

  it("每个 href 的 scope 第一项就是它自己", () => {
    for (const item of ALL_NAV) {
      expect(ACTIVE_SCOPE[item.href][0], `${item.href} 的 scope 未含自身`).toBe(item.href);
    }
  });

  it("首页组是显式清单，不含裸前缀", () => {
    expect(ACTIVE_SCOPE["/"]).toEqual(["/", "/watch", "/rankings"]);
  });

  it("跨组 scope 前缀两两不相交（保证最多命中一项）", () => {
    const scopes = allScopes();
    expect(new Set(scopes).size, "同一个前缀出现在两组里").toBe(scopes.length);
    for (const a of scopes) {
      for (const b of scopes) {
        if (a === b) continue;
        const nested = b === a || b.startsWith(`${a}/`);
        expect(nested, `scope ${b} 被 ${a} 吞掉`).toBe(false);
      }
    }
  });
});

describe("navigationActive：归属", () => {
  const ATTRIBUTION: Array<[string, string]> = [
    ["/", "/"],
    ["/watch", "/"],
    ["/watch/abc", "/"],
    ["/rankings", "/"],
    ["/channels", "/channels"],
    ["/channels/ted", "/channels"],
    ["/practice", "/practice"],
    ["/practice/daily", "/practice"],
    ["/practice/exams/redo", "/practice"],
    ["/vocabulary", "/vocabulary"],
    ["/vocabulary/sets/1", "/vocabulary"],
    ["/vocabulary/drill", "/vocabulary"],
    ["/profile", "/profile"],
    ["/contact", "/profile"],
    ["/favorites", "/favorites"],
    ["/history", "/history"],
    ["/notifications", "/notifications"],
  ];

  it.each(ATTRIBUTION)("%s 归属 %s", (pathname, href) => {
    expect(activeHrefs(pathname)).toEqual([href]);
  });

  it("归属表里每个目标 href 都是真实导航项", () => {
    const hrefs = ALL_NAV.map((item) => item.href);
    for (const [, href] of ATTRIBUTION) {
      expect(hrefs).toContain(href);
    }
  });
});

describe("navigationActive：不双高亮", () => {
  const PATHNAMES = [
    "/",
    "/watch/abc",
    "/rankings",
    "/channels",
    "/channels/ted",
    "/practice/daily",
    "/practice/exams/redo",
    "/vocabulary/sets/1",
    "/vocabulary/drill",
    "/profile",
    "/contact",
    "/favorites",
    "/history",
    "/notifications",
  ];

  it.each(PATHNAMES)("%s 最多命中一项", (pathname) => {
    expect(activeHrefs(pathname).length).toBeLessThanOrEqual(1);
  });

  it("无归属路径命中 0 项", () => {
    for (const pathname of ["/search"]) {
      expect(activeHrefs(pathname), `${pathname} 不该高亮`).toEqual([]);
    }
  });

  it("首页组不吞前缀：/practice、/channels 不命中「/」", () => {
    expect(navigationActive("/practice", "/")).toBe(false);
    expect(navigationActive("/channels", "/")).toBe(false);
    expect(navigationActive("/favorites", "/")).toBe(false);
    expect(navigationActive("/notifications", "/")).toBe(false);
  });
});

describe("navigationActive：斜杠边界", () => {
  it("/watch 认自己与子路径，不认 /watchlist", () => {
    expect(navigationActive("/watch", "/")).toBe(true);
    expect(navigationActive("/watch/1", "/")).toBe(true);
    expect(navigationActive("/watchlist", "/")).toBe(false);
  });

  it("/notifications 不认 /notifications-archive", () => {
    expect(navigationActive("/notifications", "/notifications")).toBe(true);
    expect(navigationActive("/notifications-archive", "/notifications")).toBe(false);
  });

  it("表里没有的 href 回退到「自己认领自己」", () => {
    expect(navigationActive("/search", "/search")).toBe(true);
    expect(navigationActive("/search/deep", "/search")).toBe(true);
    expect(navigationActive("/searching", "/search")).toBe(false);
  });
});
