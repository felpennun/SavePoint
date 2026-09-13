import { afterEach, describe, expect, it, vi } from "vitest";

import {
  fetchPublicProfile,
  fetchSharedCollection,
  fetchSharedList,
  type ProtectedPublicProfile,
} from "@/lib/api";
import { buildProfileNavigation } from "@/app/[locale]/profiles/[alias]/page";

const protectedProfile: ProtectedPublicProfile = {
  kind: "protected",
  alias: "alice",
  bio: "A short bio",
  avatar_url: "",
  activity: [],
  summary: { pending: 0, playing: 0, completed: 0, abandoned: 0 },
  favorites: [null, null, null, null, null],
  comments: [],
  lists: [],
};

describe("protected profile SSR contract", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("discriminates the basic projection and forwards the incoming session cookie", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          alias: "alice",
          avatar_url: "",
          bio: "A short bio",
          action: "send_friend_request",
        }),
        { status: 200 },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    const profile = await fetchPublicProfile("alice", "sessionid=owner; csrftoken=csrf");

    expect(profile).toMatchObject({ kind: "basic", alias: "alice", action: "send_friend_request" });
    expect(profile && "activity" in profile).toBe(false);
    expect(fetchMock.mock.calls[0][1]).toMatchObject({
      headers: { Cookie: "sessionid=owner; csrftoken=csrf" },
    });
  });

  it("loads protected collection/list projections only as explicit follow-up fetches", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(new Response(JSON.stringify(protectedProfile), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ items: [] }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ name: "Backlog", items: [] }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    const profile = await fetchPublicProfile("alice", "sessionid=owner");
    const collection = await fetchSharedCollection("alice", "sessionid=owner");
    const list = await fetchSharedList("alice", "backlog", "sessionid=owner");

    expect(profile).toEqual(protectedProfile);
    expect(collection).toEqual({ items: [] });
    expect(list).toEqual({ name: "Backlog", items: [] });
    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(fetchMock.mock.calls[1][1]).toMatchObject({ headers: { Cookie: "sessionid=owner" } });
    expect(fetchMock.mock.calls[2][1]).toMatchObject({ headers: { Cookie: "sessionid=owner" } });
  });

  it("maps profile/list 404 responses to null without exposing a partial resource", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: "Not found." }), { status: 404 })));

    await expect(fetchPublicProfile("hidden", "sessionid=visitor")).resolves.toBeNull();
    await expect(fetchSharedList("hidden", "private", "sessionid=visitor")).resolves.toBeNull();
  });

  it("builds an accessible local navigation with one current route", () => {
    expect(buildProfileNavigation("es", "alice", "profile")).toEqual([
      { href: "/es/profiles/alice", label: "Perfil", current: true },
      { href: "/es/profiles/alice#collection", label: "Colección", current: false },
      { href: "/es/profiles/alice/lists", label: "Listas", current: false },
    ]);
    expect(buildProfileNavigation("en", "alice", "list")[2]).toMatchObject({ current: true });
  });
});
