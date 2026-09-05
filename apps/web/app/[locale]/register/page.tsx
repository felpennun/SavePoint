"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";

import { getDictionary } from "@/i18n";

// The password-mismatch check is a purely client-side guard with no
// dictionary row in the Copywriting Contract; kept inline + localized.
const MISMATCH = {
  es: "Las contraseñas no coinciden.",
  en: "The passwords don't match.",
} as const;

/**
 * Registration (01.1-UI-SPEC Screen Contract 5d, D-08, NEW). This plan
 * ships the COMPLETE responsive / localized / accessible visual + form
 * contract only -- Plan 04/08 connects the controlled account API and
 * journey behaviour. The submit handler already maps the four contracted
 * error rows by response status so the backend wiring is a drop-in; with
 * no endpoint yet a submit surfaces the generic error.
 */
export default function RegisterPage() {
  const routeParams = useParams<{ locale: string }>();
  const router = useRouter();
  const locale = routeParams.locale === "en" ? "en" : "es";
  const dict = getDictionary(locale);
  const t = dict.register;
  const mismatchMsg = MISMATCH[locale];

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    if (password !== confirm) {
      setError(mismatchMsg);
      setPassword("");
      setConfirm("");
      return;
    }

    setPending(true);
    try {
      await fetch("/api/accounts/csrf/", { credentials: "same-origin" });
      const csrfToken = document.cookie
        .split("; ")
        .find((row) => row.startsWith("csrftoken="))
        ?.split("=")[1];

      const response = await fetch("/api/accounts/register/", {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json", ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}) },
        body: JSON.stringify({ username, password }),
      });

      if (response.ok) {
        router.push(`/${locale}/catalogue`);
        return;
      }
      setPassword("");
      setConfirm("");
      if (response.status === 409) setError(t.errorDuplicate);
      else if (response.status === 400) setError(t.errorWeakPassword);
      else if (response.status === 429) setError(t.errorRateLimited);
      else setError(t.errorGeneric);
    } catch {
      setError(t.errorGeneric);
    } finally {
      setPending(false);
    }
  }

  return (
    <main className="sp-page" style={{ maxWidth: "420px" }}>
      <h1 className="sp-h1">{t.heading}</h1>
      <p className="sp-lead">{t.intro}</p>

      <form onSubmit={handleSubmit} method="post" className="sp-surface" style={{ display: "flex", flexDirection: "column", gap: "var(--space-md)" }}>
        <div className="sp-field">
          <label htmlFor="username">{t.username}</label>
          <input
            id="username"
            name="username"
            type="text"
            autoComplete="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            aria-invalid={error ? true : undefined}
            aria-describedby={error ? "register-error" : undefined}
            required
          />
        </div>
        <div className="sp-field">
          <label htmlFor="password">{t.password}</label>
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="new-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            aria-describedby={error ? "register-error" : undefined}
            required
          />
        </div>
        <div className="sp-field">
          <label htmlFor="confirm-password">{t.confirmPassword}</label>
          <input
            id="confirm-password"
            name="confirm-password"
            type="password"
            autoComplete="new-password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            aria-describedby={error ? "register-error" : undefined}
            required
          />
        </div>

        {error ? (
          <p id="register-error" role="alert" data-testid="register-error" style={{ color: "var(--color-danger)", margin: 0 }}>
            {error}
          </p>
        ) : null}

        <button type="submit" className="sp-btn-primary" disabled={pending}>
          {pending ? t.pending : t.submit}
        </button>
      </form>

      <p className="sp-muted" style={{ marginTop: "var(--space-md)", textAlign: "center" }}>
        <Link href={`/${locale}/login`} className="sp-link">
          {t.haveAccount}
        </Link>
      </p>
    </main>
  );
}
