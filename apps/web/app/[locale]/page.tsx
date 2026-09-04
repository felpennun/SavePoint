import Link from "next/link";

/**
 * Minimal homepage stub -- Plan 01-04's tracer scope is session -> catalogue
 * -> state, not the full UI-SPEC homepage (value blocks, footer, etc.),
 * which belongs to the later UI-focused waves. This exists only so
 * /{locale} resolves to something rather than 404ing, with a working path
 * into the two flows this plan actually proves.
 */
export default async function HomePage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  const isEs = locale === "es";

  return (
    <main>
      <h1>SavePoint</h1>
      <p>
        {isEs
          ? "Catálogo de videojuegos personal, controlado y reproducible."
          : "A controlled, reproducible personal video-game catalogue."}
      </p>
      <nav>
        <Link href={`/${locale}/login`}>{isEs ? "Iniciar sesión" : "Log in"}</Link>
        {" · "}
        <Link href={`/${locale}/catalogue`}>{isEs ? "Ver catálogo" : "Browse catalogue"}</Link>
      </nav>
    </main>
  );
}
