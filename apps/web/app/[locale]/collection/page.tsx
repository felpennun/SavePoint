import { cookies } from "next/headers";
import Link from "next/link";
import { redirect } from "next/navigation";

import { formatCount, getDictionary } from "@/i18n";
import { fetchMyLibrary } from "@/lib/api";

/** Authenticated-only per UI-SPEC; unlike the middleware's coarse
 * cookie-existence gate, this page also handles the case where the
 * cookie exists but the session has expired server-side (Django returns
 * 401), redirecting to login rather than throwing. */
export default async function CollectionPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: rawLocale } = await params;
  const locale = rawLocale === "en" ? "en" : "es";
  const dict = getDictionary(locale);

  const cookieStore = await cookies();
  if (!cookieStore.has("sessionid")) {
    redirect(`/${locale}/login?next=${encodeURIComponent(`/${locale}/collection`)}`);
  }
  const cookieHeader = cookieStore
    .getAll()
    .map((c) => `${c.name}=${c.value}`)
    .join("; ");

  let library;
  try {
    library = await fetchMyLibrary(cookieHeader);
  } catch {
    redirect(`/${locale}/login?next=${encodeURIComponent(`/${locale}/collection`)}`);
  }

  return (
    <main>
      <h1>{dict.collection.heading}</h1>
      <dl>
        {Object.entries(library.summary).map(([status, count]) => (
          <div key={status}>
            <dt>{dict.status.labels[status as keyof typeof dict.status.labels] ?? status}</dt>
            <dd>{formatCount(dict.collection.statusSummaryCount, count)}</dd>
          </div>
        ))}
      </dl>

      {library.items.length === 0 ? (
        <div>
          <p>{dict.collection.emptyHeading}</p>
          <p>{dict.collection.emptyBody}</p>
          <Link href={`/${locale}/catalogue`}>{dict.nav.catalogue}</Link>
        </div>
      ) : (
        <ul>
          {library.items.map((item) => (
            <li key={item.work_id}>
              <Link href={`/${locale}/games/${item.work_slug}`}>
                {item.work_title} — {dict.status.labels[item.status as keyof typeof dict.status.labels]} —{" "}
                {formatCount(dict.collection.ownedCopyCount, item.owned_copy_count)}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
