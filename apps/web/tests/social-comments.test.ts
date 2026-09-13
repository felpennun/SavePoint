import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const gamePageSource = readFileSync(
  fileURLToPath(new URL("../app/[locale]/games/[id]/page.tsx", import.meta.url)),
  "utf8",
).replaceAll("\r\n", "\n");
const commentsSource = readFileSync(
  fileURLToPath(new URL("../components/GameComments.tsx", import.meta.url)),
  "utf8",
).replaceAll("\r\n", "\n");

describe("game detail social comments contract", () => {
  it("places the existing GameComments surface after game metadata", () => {
    const metadataEnd = gamePageSource.indexOf('<p className="sp-kv">{formattedReleaseDate}</p>');
    const commentsRegion = gamePageSource.indexOf('data-testid="game-comments-region"');

    expect(gamePageSource).toContain('import { GameComments } from "@/components/GameComments";');
    expect(commentsRegion).toBeGreaterThan(metadataEnd);
    expect(gamePageSource).toMatch(
      /<GameComments workId=\{game\.id\} locale=\{locale\} isAuthenticated=\{isAuthenticated\} \/>/,
    );
  });

  it("keeps comments restricted to the API allowlist and author control", () => {
    expect(commentsSource).toContain("author: string;");
    expect(commentsSource).toContain("text: string;");
    expect(commentsSource).toContain("created_at: string;");
    expect(commentsSource).toContain("is_own: boolean;");
    expect(commentsSource).toContain("comments.filter((comment) => !comment.is_own)");
    expect(commentsSource).not.toMatch(/owner_id|user_id|email|ownership|dangerouslySetInnerHTML/);
  });

  it("uses neutral accessible feedback without leaking authorization details", () => {
    expect(commentsSource).toContain('role="status"');
    expect(commentsSource).toContain("copy.error");
    expect(commentsSource).not.toMatch(/not authorized|forbidden|friendship|private comments/i);
  });
});
