"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

/** Refresh the server-rendered snapshot while a background job is pending. */
export function RecommendationRefreshNotice({
  message,
}: {
  message: string;
}) {
  const router = useRouter();

  useEffect(() => {
    const interval = window.setInterval(() => router.refresh(), 3000);
    return () => window.clearInterval(interval);
  }, [router]);

  return (
    <p className="sp-muted" role="status" aria-live="polite">
      {message}
    </p>
  );
}
