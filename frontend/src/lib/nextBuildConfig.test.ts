import { readFileSync } from "node:fs";
import { runInNewContext } from "node:vm";
import { describe, expect, it } from "vitest";

const source = readFileSync(new URL("../../next.config.js", import.meta.url), "utf8");
function load(value?: string) {
  const module = {
    exports: {} as { experimental: { cpus?: number; optimizePackageImports: string[] } },
  };
  runInNewContext(source, {
    module,
    process: { env: value === undefined ? {} : { NEXT_BUILD_CPUS: value } },
  });
  return module.exports;
}

describe("optional build resource limit", () => {
  it("preserves the framework default when no local limit is requested", () => {
    expect(load().experimental.cpus).toBeUndefined();
    expect(load().experimental.optimizePackageImports).toEqual(["recharts", "lucide-react"]);
  });
  it("can run the same build with a single page worker", () => {
    expect(load("1").experimental.cpus).toBe(1);
  });
  it.each(["0", "-1", "1.5", "NaN", "Infinity", "9007199254740992", ""])(
    "rejects invalid limits instead of silently ignoring %s",
    (value) => {
      expect(() => load(value)).toThrow("NEXT_BUILD_CPUS must be a positive safe integer");
    }
  );
});
