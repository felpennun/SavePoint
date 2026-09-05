"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";

const COPY = {
  es: {
    heading: "Iniciar sesión",
    intro: "Inicia sesión en una cuenta simulada de la demo.",
    username: "Usuario",
    password: "Contraseña",
    submit: "Entrar",
    pending: "Entrando…",
    invalid: "El nombre de usuario o la contraseña no son correctos. Comprueba los datos e inténtalo de nuevo.",
    generic: "No se pudo iniciar sesión. Inténtalo de nuevo.",
    noAccount: "¿No tienes cuenta? Crear una cuenta simulada",
  },
  en: {
    heading: "Log in",
    intro: "Sign in to a simulated demo account.",
    username: "Username",
    password: "Password",
    submit: "Log in",
    pending: "Logging in…",
    invalid: "The username or password is incorrect. Check the details and try again.",
    generic: "We couldn't log you in. Try again.",
    noAccount: "No account yet? Create a simulated account",
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
      // Django's LoginView is locale-unaware; only trust its returned
      // `next` when we sent an explicit, already-locale-prefixed value.
      router.push(requestedNext ? body.next : `/${locale}/catalogue`);
    } catch {
      setError(copy.generic);
    } finally {
      setPending(false);
    }
  }

  return (
    <main className="sp-page" style={{ maxWidth: "420px" }}>
      <h1 className="sp-h1">{copy.heading}</h1>
      <p className="sp-lead">{copy.intro}</p>
      {/* method="post" is defense-in-depth: a pre-hydration click POSTs to
          this same page (no POST handler) instead of leaking the password
          into a GET query string. */}
      <form
        onSubmit={handleSubmit}
        method="post"
        className="sp-surface"
        style={{ display: "flex", flexDirection: "column", gap: "var(--space-md)" }}
      >
        <div className="sp-field">
          <label htmlFor="username">{copy.username}</label>
          <input
            id="username"
            name="username"
            type="text"
            autoComplete="username"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            aria-describedby={error ? "login-error" : undefined}
            required
          />
        </div>
        <div className="sp-field">
          <label htmlFor="password">{copy.password}</label>
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            aria-describedby={error ? "login-error" : undefined}
            required
          />
        </div>
        {error ? (
          <p id="login-error" role="alert" data-testid="login-error" style={{ color: "var(--color-danger)", margin: 0 }}>
            {error}
          </p>
        ) : null}
        <button type="submit" className="sp-btn-primary" disabled={pending}>
          {pending ? copy.pending : copy.submit}
        </button>
      </form>

      <p className="sp-muted" style={{ marginTop: "var(--space-md)", textAlign: "center" }}>
        <Link href={`/${locale}/register`} className="sp-link">
          {copy.noAccount}
        </Link>
      </p>
    </main>
  );
}
