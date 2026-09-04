import { describe, expect, it } from "vitest";

import { en } from "@/i18n/en";
import { es } from "@/i18n/es";
import { formatCount } from "@/i18n/dictionary";

/** Recursively collects every leaf key path (dotted), treating a
 * CountCopy's `many` function as a single leaf, not an object to descend
 * into further. */
function collectKeyPaths(value: unknown, prefix = ""): string[] {
  if (typeof value === "function") return [prefix];
  if (typeof value !== "object" || value === null) return [prefix];
  const paths: string[] = [];
  for (const [key, nested] of Object.entries(value as Record<string, unknown>)) {
    paths.push(...collectKeyPaths(nested, prefix ? `${prefix}.${key}` : key));
  }
  return paths;
}

describe("i18n dictionary parity (D-10)", () => {
  it("es and en declare exactly the same set of keys", () => {
    const esKeys = collectKeyPaths(es).sort();
    const enKeys = collectKeyPaths(en).sort();
    expect(esKeys).toEqual(enKeys);
  });

  it("neither dictionary has an empty string value", () => {
    for (const [locale, dict] of [
      ["es", es],
      ["en", en],
    ] as const) {
      for (const path of collectKeyPaths(dict)) {
        const segments = path.split(".");
        let current: unknown = dict;
        for (const segment of segments) {
          current = (current as Record<string, unknown>)[segment];
        }
        if (typeof current === "string") {
          expect(current.length, `${locale}.${path} must not be empty`).toBeGreaterThan(0);
        }
      }
    }
  });
});

describe("formatCount canonical zero/one/many (Copywriting Contract)", () => {
  it("returns the exact zero form for count 0", () => {
    expect(formatCount(es.catalogue.resultCount, 0)).toBe("0 resultados");
    expect(formatCount(en.catalogue.resultCount, 0)).toBe("0 results");
  });

  it("returns the exact one form for count 1", () => {
    expect(formatCount(es.catalogue.resultCount, 1)).toBe("1 resultado");
    expect(formatCount(en.catalogue.resultCount, 1)).toBe("1 result");
  });

  it("returns the many form for count > 1", () => {
    expect(formatCount(es.catalogue.resultCount, 42)).toBe("42 resultados");
    expect(formatCount(en.catalogue.resultCount, 42)).toBe("42 results");
  });
});
