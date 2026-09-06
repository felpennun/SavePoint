import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const css = readFileSync(fileURLToPath(new URL("../globals.css", import.meta.url)), "utf8");

// Balanced braces keep nested media rules intact instead of stopping at the
// first closing brace (which could silently miss a motion override).
function block(source: string, selector: string): string {
  const start = source.indexOf(`${selector} {`);
  expect(start, `Missing CSS rule: ${selector}`).toBeGreaterThanOrEqual(0);
  const opening = source.indexOf("{", start);
  let depth = 1;
  let end = opening + 1;
  for (; end < source.length && depth > 0; end++) {
    if (source[end] === "{") depth++;
    if (source[end] === "}") depth--;
  }
  expect(depth, `Unclosed CSS rule: ${selector}`).toBe(0);
  return source.slice(opening + 1, end - 1);
}

function value(source: string, property: string): string {
  const match = source.match(new RegExp(`${property}:\\s*([^;]+);`));
  expect(match, `Missing CSS declaration: ${property}`).not.toBeNull();
  return match![1].trim();
}

describe("shared product polish tokens", () => {
  it("defines distinct overlay shadows for dark and light themes", () => {
    const dark = value(block(css, "@theme"), "--shadow-overlay");
    const light = value(block(css, ':root[data-theme="light"]'), "--shadow-overlay");
    expect(dark, "Dark overlay shadow must differ from light").not.toBe(light);
  });

  it("uses existing surface colors for the skeleton", () => {
    const theme = block(css, "@theme");
    expect(value(theme, "--color-skeleton-base")).toBe("var(--color-surface-overlay)");
    expect(value(theme, "--color-skeleton-sheen")).toBe("var(--color-surface-raised)");
    expect(value(block(css, ".sp-skeleton"), "background")).toBe("var(--color-skeleton-base)");
  });

  it("explicitly disables skeleton animation with reduced motion", () => {
    const reduced = block(css, "@media (prefers-reduced-motion: reduce)");
    expect(value(block(reduced, ".sp-skeleton"), "animation")).toMatch(/^none(?: !important)?$/);
    expect(value(block(reduced, ".sp-skeleton::after"), "animation")).toMatch(/^none(?: !important)?$/);
  });

  it("gives facet summaries a 44px target and removes native markers", () => {
    const summary = block(css, ".sp-facet > summary");
    expect(value(summary, "min-height")).toBe("2.75rem");
    expect(value(summary, "list-style")).toBe("none");
    expect(value(block(css, ".sp-facet > summary::-webkit-details-marker"), "display")).toBe("none");
  });

  it("keeps polish utilities neutral without new accent references", () => {
    const utilities = css.match(/\/\* Phase 2 product polish utilities[\s\S]*$/)?.[0];
    expect(utilities, "Missing phase 2 polish utilities").toBeDefined();
    expect(utilities).not.toContain("--color-accent");
    expect(block(css, ".sp-contrib-table")).toContain("var(--space-md)");
    expect(block(css, ".sp-facet[open] > summary .sp-facet-chevron")).toContain("rotate(180deg)");
  });
});
