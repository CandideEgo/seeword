"use client";

import { Theme } from "@astryxdesign/core/theme";
import { neutralTheme } from "@astryxdesign/theme-neutral/built";
import { useThemeContext } from "@/components/common/ThemeProvider";

/** Route-scoped adoption; the existing app provider still owns theme preference. */
export function AstryxProvider({ children }: { children: React.ReactNode }) {
  const { theme, mounted } = useThemeContext();

  return (
    <Theme theme={neutralTheme} mode={mounted ? theme : "system"}>
      {children}
    </Theme>
  );
}
