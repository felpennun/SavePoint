import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  getSocialActionDescriptors,
  type SocialActionRelationship,
} from "@/components/SocialActions";
import {
  buildSocialSearchUrl,
  SOCIAL_SECTIONS,
  SocialHub,
} from "@/components/SocialHub";

const relationships: SocialActionRelationship[] = ["pending_received", "friend", "blocked"];

describe("social hub contract", () => {
  afterEach(() => vi.restoreAllMocks());

  it("exposes three explicit sections and an exact alias search URL", () => {
    expect(SOCIAL_SECTIONS).toEqual(["received", "sent", "friends"]);
    expect(buildSocialSearchUrl("  Alice.Exact  ")).toBe("/api/social/search/?alias=Alice.Exact");
    expect(buildSocialSearchUrl("Alice.Exact other")).toContain("alias=Alice.Exact+other");
  });

  it("keeps accept/reject/remove/block/unblock as distinct API actions", () => {
    expect(getSocialActionDescriptors("pending_received", "es").map((action) => action.key)).toEqual([
      "accept",
      "reject",
    ]);
    expect(getSocialActionDescriptors("friend", "es").map((action) => action.key)).toEqual([
      "remove",
      "block",
    ]);
    expect(getSocialActionDescriptors("blocked", "es").map((action) => action.key)).toEqual(["unblock"]);
  });

  it("renders named sections, live feedback, and a non-autocomplete search control", () => {
    const markup = renderToStaticMarkup(createElement(SocialHub, {
      locale: "es",
      initialRequests: {
        received: [{ id: "r1", sender_alias: "alice", receiver_alias: "me", status: "pending", created_at: "2026-09-13" }],
        sent: [],
      },
      initialFriends: { friends: [{ alias: "bob", relationship: "friend" }] },
    }));
    expect(markup).toContain("Solicitudes recibidas");
    expect(markup).toContain("Solicitudes enviadas");
    expect(markup).toContain("Amistades");
    expect(markup).toContain('aria-live="polite"');
    expect(markup).toContain('autocomplete="off"');
    expect(markup).not.toContain("<datalist");
  });

  it.each(relationships)("uses a relationship-specific action surface for %s", (relationship) => {
    expect(getSocialActionDescriptors(relationship, "en").every((action) => action.label.length > 0)).toBe(true);
  });
});
