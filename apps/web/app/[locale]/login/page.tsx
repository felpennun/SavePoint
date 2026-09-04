"use client";

import { useState, type FormEvent } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";

const COPY = {
  es: {
    heading: "Iniciar sesión",
    username: "Usuario",
    password: "Contraseña",
    submit: "Entrar",
    pending: "Entrando…",
    invalid: "El nombre de usuario o la contraseña no son correctos. Comprueba los datos e inténtalo de nuevo.",
    generic: "No se pudo iniciar sesión. Inténtalo de nuevo.",
  },
  en: {
    heading: "Log in",
    username: "Username",
    password: "Password",
    submit: "Log in",
    pending: "Logging in…",
    invalid: "The username or password is incorrect. Check the details and try again.",
    generic: "We couldn't log you in. Try again.",
  },
} as const;

export default function LoginPage() {
  const params = useParams<{ locale: string }>();
  const searchParams = useSearchParams();
  const router = useRouter();
  const locale = params.locale === "en" ? "en" : "es";
  const copy = COPY[locale];

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError(null);
    try {
      await fetch("/api/accounts/csrf/", { credentials: "same-origin" });
      const csrfToken = document.cookie
        .split("; ")
        .find((row) => row.startsWith("csrftoken="))
        ?.split("=")[1];

      const requestedNext = searchParams.get("next") ?? undefined;
      const response = await fetch("/api/accounts/login/", {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
          ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}),
        },
        body: JSON.stringify({ username, password, next: requestedNext }),
      });

      if (!response.ok) {
        setError(copy.invalid);
        setPassword("");
        return;
      }

      const body = (await response.json()) as { next: string };
      // Django's LoginView is locale-unaware (it has no concept of the
      // [locale] route segment) -- its own default is a bare "/catalogue".
      // Only trust its returned `next` when we actually sent an explicit,
      // already-locale-prefixed value (the middleware always constructs
      // `next` that way when redirecting an unauthenticated visitor);
      // otherwise construct the locale-aware default ourselves rather than
      // relying on the backend's locale-blind fallback.
      router.push(requestedNext ? body.next : `/${locale}/catalogue`);
    } catch {
      setError(copy.generic);
    } finally {
      setPending(false);
    }
  }

  return (
    <main>
      <h1>{copy.heading}</h1>
      {/* method="post" is a defense-in-depth fallback: if a click ever
          reaches the browser before React finishes hydrating and attaching
          onSubmit, the native submission still can't leak the password into
          a URL query string via a GET -- it POSTs to this same page (which
          has no POST handler) and safely no-ops instead. */}
      <form onSubmit={handleSubmit} method="post">
        <div>
          <label htmlFor="username">{copy.username}</label>
          <input
            id="username"
            name="username"
            type="text"
            autoComplete="username"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            required
          />
        </div>
        <div>
          <label htmlFor="password">{copy.password}</label>
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        </div>
        {error ? (
          <p role="alert" data-testid="login-error">
            {error}
          </p>
        ) : null}
        <button type="submit" disabled={pending}>
          {pending ? copy.pending : copy.submit}
        </button>
      </form>
    </main>
  );
}
