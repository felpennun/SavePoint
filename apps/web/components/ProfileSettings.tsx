"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { apiFetch } from "@/lib/client-api";

type Visibility = "public" | "private";

interface FavoriteSlotState {
  slot: number;
  work_id: string | null;
  work_slug: string | null;
  work_title: string | null;
}

interface EligibleWork {
  work_id: string;
  work_title: string;
}

const COPY = {
  es: {
    heading: "Editar perfil",
    bioLabel: "Biografía",
    bioPlaceholder: "Cuenta algo sobre ti (opcional)",
    avatarLabel: "Avatar (URL https, opcional)",
    avatarHint: "Debe ser una URL https:// válida.",
    collectionVisibility: "Visibilidad de la colección",
    favoritesVisibility: "Visibilidad de los favoritos",
    public: "Pública",
    private: "Privada",
    save: "Guardar perfil",
    saving: "Guardando…",
    saved: "Perfil guardado",
    error: "No se pudo guardar el perfil. Inténtalo de nuevo.",
    favoritesHeading: "Tus 5 favoritos",
    favoritesHint: "Solo puedes elegir juegos que ya estén en tu colección.",
    favoriteEmpty: "— vacío —",
    slotLabel: (n: number) => `Favorito ${n}`,
    favoritesSave: "Guardar favoritos",
    favoritesSaving: "Guardando favoritos…",
    favoritesSaved: "Favoritos guardados",
    favoritesError: "No se pudieron guardar los favoritos. Inténtalo de nuevo.",
    loading: "Cargando perfil…",
  },
  en: {
    heading: "Edit profile",
    bioLabel: "Biography",
    bioPlaceholder: "Say something about yourself (optional)",
    avatarLabel: "Avatar (https URL, optional)",
    avatarHint: "Must be a valid https:// URL.",
    collectionVisibility: "Collection visibility",
    favoritesVisibility: "Favorites visibility",
    public: "Public",
    private: "Private",
    save: "Save profile",
    saving: "Saving…",
    saved: "Profile saved",
    error: "We couldn't save the profile. Try again.",
    favoritesHeading: "Your 5 favorites",
    favoritesHint: "You can only pick games already in your collection.",
    favoriteEmpty: "— empty —",
    slotLabel: (n: number) => `Favorite ${n}`,
    favoritesSave: "Save favorites",
    favoritesSaving: "Saving favorites…",
    favoritesSaved: "Favorites saved",
    favoritesError: "We couldn't save the favorites. Try again.",
    loading: "Loading profile…",
  },
} as const;

/** Owner-only profile + favorites editor (PROF-01, D-02). Rendered on the
 * signed-in user's own `/profiles/<alias>` page, above the public-shaped
 * view every visitor (including the owner) sees below it. */
export function ProfileSettings({ locale }: { locale: "es" | "en" }) {
  const copy = COPY[locale];
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [bio, setBio] = useState("");
  const [avatarUrl, setAvatarUrl] = useState("");
  const [collectionVisibility, setCollectionVisibility] = useState<Visibility>("public");
  const [favoritesVisibility, setFavoritesVisibility] = useState<Visibility>("public");
  const [saving, setSaving] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);

  const [slots, setSlots] = useState<FavoriteSlotState[]>([]);
  const [eligibleWorks, setEligibleWorks] = useState<EligibleWork[]>([]);
  const [favoritesSaving, setFavoritesSaving] = useState(false);
  const [favoritesFeedback, setFavoritesFeedback] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      apiFetch("/api/accounts/me/profile/").then((r) => (r.ok ? r.json() : null)),
      apiFetch("/api/accounts/me/favorites/").then((r) => (r.ok ? r.json() : null)),
      apiFetch("/api/library/entries/").then((r) => (r.ok ? r.json() : null)),
    ]).then(([profileBody, favoritesBody, libraryBody]) => {
      if (cancelled) return;
      if (profileBody) {
        setBio(profileBody.bio ?? "");
        setAvatarUrl(profileBody.avatar_url ?? "");
        setCollectionVisibility(profileBody.collection_visibility ?? "public");
        setFavoritesVisibility(profileBody.favorites_visibility ?? "public");
      }
      if (favoritesBody && Array.isArray(favoritesBody.slots)) setSlots(favoritesBody.slots);
      if (libraryBody && Array.isArray(libraryBody.items)) {
        setEligibleWorks(
          libraryBody.items.map((item: { work_id: string; work_title: string }) => ({
            work_id: item.work_id,
            work_title: item.work_title,
          })),
        );
      }
      setLoading(false);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) return <p aria-live="polite">{copy.loading}</p>;

  async function saveProfile() {
    setSaving(true);
    setFeedback(null);
    try {
      const response = await apiFetch("/api/accounts/me/profile/", {
        method: "PATCH",
        body: { bio, avatar_url: avatarUrl, collection_visibility: collectionVisibility, favorites_visibility: favoritesVisibility },
      });
      if (!response.ok) {
        setFeedback(copy.error);
        return;
      }
      const body = await response.json();
      setBio(body.bio ?? "");
      setAvatarUrl(body.avatar_url ?? "");
      setCollectionVisibility(body.collection_visibility ?? "public");
      setFavoritesVisibility(body.favorites_visibility ?? "public");
      setFeedback(copy.saved);
      router.refresh();
    } catch {
      setFeedback(copy.error);
    } finally {
      setSaving(false);
    }
  }

  function updateSlot(slotNumber: number, workId: string) {
    setSlots((previous) => {
      const withoutDuplicate = previous.filter((slot) => slot.slot === slotNumber || slot.work_id !== workId || workId === "");
      const existing = withoutDuplicate.find((slot) => slot.slot === slotNumber);
      const work = eligibleWorks.find((item) => item.work_id === workId);
      const next = {
        slot: slotNumber,
        work_id: workId || null,
        work_slug: null,
        work_title: work?.work_title ?? null,
      };
      if (existing) {
        return withoutDuplicate.map((slot) => (slot.slot === slotNumber ? next : slot));
      }
      return [...withoutDuplicate, next];
    });
  }

  async function saveFavorites() {
    setFavoritesSaving(true);
    setFavoritesFeedback(null);
    try {
      const response = await apiFetch("/api/accounts/me/favorites/", {
        method: "PUT",
        body: {
          slots: slots
            .filter((slot) => slot.work_id)
            .map((slot) => ({ slot: slot.slot, work_id: slot.work_id })),
        },
      });
      if (!response.ok) {
        setFavoritesFeedback(copy.favoritesError);
        return;
      }
      const body = await response.json();
      if (Array.isArray(body.slots)) setSlots(body.slots);
      setFavoritesFeedback(copy.favoritesSaved);
      router.refresh();
    } catch {
      setFavoritesFeedback(copy.favoritesError);
    } finally {
      setFavoritesSaving(false);
    }
  }

  return (
    <section className="sp-library-controls sp-profile-settings" aria-label={copy.heading}>
      <h2 className="sp-library-title">{copy.heading}</h2>

      <div className="sp-library-section">
        <div className="sp-field">
          <label htmlFor="profile-bio">{copy.bioLabel}</label>
          <textarea
            id="profile-bio"
            value={bio}
            placeholder={copy.bioPlaceholder}
            onChange={(event) => setBio(event.target.value)}
            disabled={saving}
            rows={4}
          />
        </div>
        <div className="sp-field">
          <label htmlFor="profile-avatar">{copy.avatarLabel}</label>
          <input
            id="profile-avatar"
            type="url"
            value={avatarUrl}
            placeholder="https://…"
            onChange={(event) => setAvatarUrl(event.target.value)}
            disabled={saving}
          />
          <p className="sp-meta">{copy.avatarHint}</p>
        </div>
        <div className="sp-field">
          <label htmlFor="profile-collection-visibility">{copy.collectionVisibility}</label>
          <select
            id="profile-collection-visibility"
            value={collectionVisibility}
            onChange={(event) => setCollectionVisibility(event.target.value as Visibility)}
            disabled={saving}
          >
            <option value="public">{copy.public}</option>
            <option value="private">{copy.private}</option>
          </select>
        </div>
        <div className="sp-field">
          <label htmlFor="profile-favorites-visibility">{copy.favoritesVisibility}</label>
          <select
            id="profile-favorites-visibility"
            value={favoritesVisibility}
            onChange={(event) => setFavoritesVisibility(event.target.value as Visibility)}
            disabled={saving}
          >
            <option value="public">{copy.public}</option>
            <option value="private">{copy.private}</option>
          </select>
        </div>
      </div>

      <div className="sp-library-save">
        <button type="button" className="sp-btn-primary" onClick={saveProfile} disabled={saving}>
          {saving ? copy.saving : copy.save}
        </button>
        {feedback ? (
          <p role="status" data-testid="profile-feedback">
            {feedback}
          </p>
        ) : null}
      </div>

      <div className="sp-library-section">
        <div className="sp-section-heading-row">
          <h3>{copy.favoritesHeading}</h3>
        </div>
        <p className="sp-meta">{copy.favoritesHint}</p>
        <div className="sp-favorite-slots">
          {[1, 2, 3, 4, 5].map((slotNumber) => {
            const current = slots.find((slot) => slot.slot === slotNumber);
            return (
              <div className="sp-field" key={slotNumber}>
                <label htmlFor={`favorite-slot-${slotNumber}`}>{copy.slotLabel(slotNumber)}</label>
                <select
                  id={`favorite-slot-${slotNumber}`}
                  value={current?.work_id ?? ""}
                  onChange={(event) => updateSlot(slotNumber, event.target.value)}
                  disabled={favoritesSaving}
                >
                  <option value="">{copy.favoriteEmpty}</option>
                  {eligibleWorks.map((work) => (
                    <option key={work.work_id} value={work.work_id}>
                      {work.work_title}
                    </option>
                  ))}
                </select>
              </div>
            );
          })}
        </div>
      </div>

      <div className="sp-library-save">
        <button type="button" className="sp-btn-primary" onClick={saveFavorites} disabled={favoritesSaving}>
          {favoritesSaving ? copy.favoritesSaving : copy.favoritesSave}
        </button>
        {favoritesFeedback ? (
          <p role="status" data-testid="favorites-feedback">
            {favoritesFeedback}
          </p>
        ) : null}
      </div>
    </section>
  );
}
