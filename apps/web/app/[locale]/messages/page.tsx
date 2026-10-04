import { redirect } from "next/navigation";

/** The recommendation inbox moved to the notifications column of the friends page. */
export default async function MessagesPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: rawLocale } = await params;
  redirect(`/${rawLocale === "en" ? "en" : "es"}/friends`);
}
