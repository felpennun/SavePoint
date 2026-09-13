import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SocialInbox } from "@/components/SocialInbox";
import {
  fetchSocialInbox,
  type SocialMessage,
} from "@/lib/api";
import {
  markSocialMessageRead,
  sendSocialRecommendation,
} from "@/lib/client-api";

const message: SocialMessage = {
  id: "message-private-id",
  sender_alias: "alice",
  recipient_alias: "bob",
  work: {
    id: "work-private-id",
    title: "Signal Drift",
    cover: { url: null, is_placeholder: true, alt: "Signal Drift" },
  },
  text: "Te gustaría este juego.",
  date: "2026-09-13T10:00:00+00:00",
  read: false,
};

describe("private social messages contract", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("fetches only the authenticated inbox DTO with the session cookie and no-store", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ messages: [{ ...message, private_field: "hidden" }] }), { status: 200 }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const inbox = await fetchSocialInbox("sessionid=bob");

    expect(inbox?.messages).toEqual([message]);
    expect(fetchMock.mock.calls[0][1]).toMatchObject({
      cache: "no-store",
      headers: { Cookie: "sessionid=bob" },
    });
  });

  it("uses the recipient-scoped read endpoint and preserves cooldown authority from the API", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ message }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ detail: "recommendation_cooldown" }), {
        status: 429,
        headers: { "Retry-After": "86400" },
      }));
    vi.stubGlobal("fetch", fetchMock);
    vi.stubGlobal("document", { cookie: "csrftoken=csrf-token" });

    expect(await markSocialMessageRead(message.id)).toBe(true);
    expect(fetchMock.mock.calls[0][0]).toBe(`/api/social/messages/${message.id}/read/`);

    const result = await sendSocialRecommendation({
      recipient_alias: "alice",
      work_id: message.work.id,
      text: message.text,
    });
    expect(result).toEqual({ kind: "cooldown", retryAfterSeconds: 86400 });
  });

  it("renders sender, game, cover placeholder, optional text and date without exposing private IDs", () => {
    const markup = renderToStaticMarkup(createElement(SocialInbox, {
      locale: "es",
      initialMessages: [message],
      friends: [{ alias: "alice", relationship: "friend" }],
      catalogue: [{ id: message.work.id, slug: "signal-drift", title: message.work.title, year: null, platform_summary: "", cover: message.work.cover }],
    }));

    expect(markup).toContain("alice");
    expect(markup).toContain("Signal Drift");
    expect(markup).toContain("Te gustaría este juego.");
    expect(markup).toContain('aria-live="polite"');
    expect(markup).not.toContain(message.id);
  });
});
