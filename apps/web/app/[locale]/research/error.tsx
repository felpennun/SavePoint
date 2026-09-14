"use client";

import { useParams } from "next/navigation";

import { getDictionary } from "@/i18n";

export default function ResearchError({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  const params = useParams<{ locale: string }>();
  const dict = getDictionary(params.locale);
  return (
    <main className="sp-page sp-research-page">
      <section className="sp-empty sp-empty--error" role="alert">
        <h1 className="sp-h1">{dict.research.errorHeading}</h1>
        <p>{dict.research.errorBody}</p>
        <button type="button" className="sp-btn-primary" onClick={reset}>{dict.research.retry}</button>
      </section>
    </main>
  );
}
