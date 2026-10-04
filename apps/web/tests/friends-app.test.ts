import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { FriendsApp } from "@/components/FriendsApp";

describe("friends page", () => {
  it("renders a polite loading state before the social data arrives", () => {
    const markup = renderToStaticMarkup(createElement(FriendsApp, { locale: "es", initialAlias: "" }));
    expect(markup).toContain("Cargando amistades");
    expect(markup).toContain('aria-live="polite"');
  });

  it("uses the English copy for the English locale", () => {
    const markup = renderToStaticMarkup(createElement(FriendsApp, { locale: "en", initialAlias: "" }));
    expect(markup).toContain("Loading friends");
  });
});
