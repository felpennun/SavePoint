"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { ContentRecommendationShelf } from "@/components/ContentRecommendationShelf";
import { OwnedGamesDlcShelf } from "@/components/OwnedGamesDlcShelf";
import { RecommendationShelf } from "@/components/RecommendationShelf";
import { getDictionary } from "@/i18n";
import {
  primaryTagRecommendationShelf,
  type OwnedDlcResult,
  type RecommendationSnapshotResult,
} from "@/lib/api";
import { CONTENT_RECOMMENDATION_SECTIONS } from "@/lib/recommendation-sections";

const SNAPSHOT_CACHE_PREFIX = "savepoint:recommendation-snapshot:";

function cacheKey(username: string): string {
  return `${SNAPSHOT_CACHE_PREFIX}${encodeURIComponent(username)}`;
}

function readCachedSnapshot(username: string): RecommendationSnapshotResult | null {
  try {
    const raw = window.sessionStorage.getItem(cacheKey(username));
    return raw ? (JSON.parse(raw) as RecommendationSnapshotResult) : null;
  } catch {
    return null;
  }
}

function writeCachedSnapshot(username: string, snapshot: RecommendationSnapshotResult): void {
  try {
    window.sessionStorage.setItem(cacheKey(username), JSON.stringify(snapshot));
  } catch {
    // The API result remains usable when browser storage is unavailable.
  }
}

async function fetchSnapshot(): Promise<RecommendationSnapshotResult | null> {
  const response = await fetch("/api/recommendations/snapshot/", { cache: "no-store" });
  return response.ok ? (response.json() as Promise<RecommendationSnapshotResult>) : null;
}

async function fetchOwnedDlc(): Promise<OwnedDlcResult> {
  const response = await fetch("/api/catalogue/owned-dlc/", { cache: "no-store" });
  return response.ok ? (response.json() as Promise<OwnedDlcResult>) : { groups: [] };
}

async function fetchUsername(): Promise<string | null> {
  const response = await fetch("/api/accounts/me/", { cache: "no-store" });
  if (!response.ok) return null;
  const body = (await response.json()) as { username?: unknown };
  return typeof body.username === "string" ? body.username : null;
}

/**
 * Paint a previously published snapshot immediately, then refresh it without
 * blocking navigation. The cache is keyed by the authenticated username so a
 * different account can never receive another account's recommendations.
 */
export function RecommendationsClient({ locale }: { locale: string }) {
  const dict = getDictionary(locale);
  const r = dict.recommendations;
  const [snapshot, setSnapshot] = useState<RecommendationSnapshotResult | null>(null);
  const [dlc, setDlc] = useState<OwnedDlcResult>({ groups: [] });
  const [loaded, setLoaded] = useState(false);
  const [loadFailed, setLoadFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    let interval: number | undefined;

    const publishSnapshot = (username: string, value: RecommendationSnapshotResult) => {
      if (cancelled) return;
      writeCachedSnapshot(username, value);
      setSnapshot(value);
    };

    const start = async () => {
      const usernameRequest = fetchUsername();
      const snapshotRequest = fetchSnapshot();
      const dlcRequest = fetchOwnedDlc();
      const username = await usernameRequest;
      if (cancelled) return;
      if (username === null) {
        setLoaded(true);
        setLoadFailed(true);
        return;
      }

      const cached = readCachedSnapshot(username);
      if (cached) setSnapshot(cached);

      const [freshSnapshot, freshDlc] = await Promise.all([snapshotRequest, dlcRequest]);
      if (cancelled) return;
      setDlc(freshDlc);
      setLoaded(true);
      if (freshSnapshot === null) {
        if (!cached) setLoadFailed(true);
        return;
      }
      publishSnapshot(username, freshSnapshot);

      if (freshSnapshot.status === "building" || freshSnapshot.status === "stale") {
        interval = window.setInterval(async () => {
          const next = await fetchSnapshot();
          if (cancelled || next === null) return;
          publishSnapshot(username, next);
          if (next.status !== "building" && next.status !== "stale" && interval !== undefined) {
            window.clearInterval(interval);
          }
        }, 3000);
      }
    };

    void start();
    return () => {
      cancelled = true;
      if (interval !== undefined) window.clearInterval(interval);
    };
  }, []);

  const tagData = snapshot?.sections?.tags ?? null;
  const contentData = snapshot?.sections?.content ?? {};
  const tagShelf = tagData && !tagData.insufficient_history
    ? primaryTagRecommendationShelf(tagData)
    : null;
  const hasContentRecommendations = Object.values(contentData).some(
    (result) => result.results.length > 0,
  );
  const hasRecommendations = hasContentRecommendations || tagShelf !== null || dlc.groups.length > 0;
  const isRefreshing = snapshot?.status === "building" || snapshot?.status === "stale";
  const needsCollectionChange = snapshot?.status === "needs_refresh";

  return (
    <main className="sp-page">
      <h1 className="sp-h1">{r.nav}</h1>
      {isRefreshing || needsCollectionChange ? (
        <div className="sp-notice-row">
          {isRefreshing ? (
            <span className="sp-notice sp-notice--info" role="status" aria-live="polite">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                <rect x="4" y="4" width="16" height="16" rx="2" />
              </svg>
              {snapshot?.status === "building" ? r.refreshPreparing : r.refreshUpdating}
            </span>
          ) : null}
          {needsCollectionChange ? (
            <span className="sp-notice sp-notice--warn" role="status" aria-live="polite">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                <path d="M12 3l9 9-9 9-9-9 9-9Z" />
              </svg>
              {r.refreshNeedsCollectionChange}
            </span>
          ) : null}
        </div>
      ) : null}
      {!hasRecommendations && loadFailed ? (
        <div className="sp-empty" role="alert">
          <p className="sp-lead" style={{ marginInline: "auto" }}>{r.error}</p>
          <Link href={`/${locale}/recommendations`} className="sp-btn-primary">{dict.common.retry}</Link>
        </div>
      ) : hasRecommendations ? (
        <div className="sp-recommendation-shelves">
          {CONTENT_RECOMMENDATION_SECTIONS.map(([algorithmId, copyKey]) => {
            const section = contentData[algorithmId];
            if (!section) return null;
            const copy = r.contentSections[copyKey];
            return (
              <ContentRecommendationShelf
                key={algorithmId}
                items={section.results}
                locale={locale}
                heading={copy.heading}
                description={copy.description}
                sectionId={`${algorithmId}-heading`}
                algorithmId={algorithmId}
              />
            );
          })}
          {tagShelf ? (
            <RecommendationShelf
              shelf={tagShelf}
              locale={locale}
              description={r.tagDescription}
            />
          ) : null}
          <OwnedGamesDlcShelf
            groups={dlc.groups}
            locale={locale}
            labels={r.dlc}
            status={dlc.groups.length > 0 ? "populated" : "empty"}
          />
        </div>
      ) : (
        <div className="sp-empty">
          <p className="sp-h2" style={{ margin: 0 }}>
            {!loaded || snapshot?.status === "building" ? r.refreshPreparing : (
              snapshot?.status === "needs_refresh" ? r.refreshNeedsCollectionChange : r.emptyHeading
            )}
          </p>
          <p className="sp-lead" style={{ marginInline: "auto" }}>{r.emptyBody}</p>
          <Link href={`/${locale}/catalogue`} className="sp-btn-primary">{r.emptyCta}</Link>
        </div>
      )}
    </main>
  );
}
