import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { ProfileEditor } from "@/components/ProfileEditor";

/** The signed-in user's own profile page ("Editar perfil" in the account
 * menu). Anonymous visitors are sent to the login page. */
export default async function ProfilePage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: rawLocale } = await params;
  const locale = rawLocale === "en" ? "en" : "es";
  const cookieStore = await cookies();
  if (!cookieStore.has("sessionid")) redirect(`/${locale}/login`);

  return (
    <main className="sp-page sp-pf-page">
      <ProfileEditor locale={locale} />
    </main>
  );
}
