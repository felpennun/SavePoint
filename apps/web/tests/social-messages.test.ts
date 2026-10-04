import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AccountSwitcher, buildAccountTriggerLabel, buildMessagesHref } from "@/components/AccountSwitcher";
import {
  fetchSocialInbox,
  type SocialMessage,
} from "@/lib/api";
import {
  markSocialMessageRead,
  sendSocialRecommendation,
} from "@/lib/client-api";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), refresh: vi.fn() }),
  usePathname: () => "/es",
}));

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

  it("names the account messages entry, unread state and exact private route accessibly", () => {
    expect(buildMessagesHref("es")).toBe("/es/friends");
    expect(buildAccountTriggerLabel("Mi cuenta", "Mensajes de amigos", 2)).toContain("2 mensajes sin leer");
    const markup = renderToStaticMarkup(createElement(AccountSwitcher, {
      locale: "es",
      labels: {
        label: "Mi cuenta",
        editProfile: "Editar perfil",
        change: "Cambiar de cuenta",
        current: "Sesión de {alias}",
        logout: "Cerrar sesión",
        listHeading: "Tu cuenta",
        messagesLabel: "Mensajes de amigos",
        unreadLabel: (count: number) => `${count} mensajes sin leer`,
        noUnreadLabel: "Sin mensajes pendientes",
      },
    }));
    expect(markup).toContain("Mensajes de amigos");
    expect(markup).toContain('aria-controls="account-menu"');
  });
});
