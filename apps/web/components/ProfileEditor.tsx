"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { usePathname, useRouter } from "next/navigation";

import { CoverImage } from "@/components/CoverImage";
import { ProfileFavoritePicker, type EligibleWork } from "@/components/ProfileFavoritePicker";
import { ProfileImageCropper } from "@/components/ProfileImageCropper";
import { apiFetch, ensureCsrfToken } from "@/lib/client-api";

type Visibility = "public" | "private";
type Tab = "account" | "privacy" | "preferences" | "connections" | "security";
type AvatarMode = "image" | "url" | "preset" | "none";
type Locale = "es" | "en";

interface ProfileDto {
  bio: string;
  avatar_url: string;
  collection_visibility: Visibility;
  favorites_visibility: Visibility;
  default_list_visibility: Visibility;
  display_name: string;
  avatar_preset: number | null;
  avatar_image_url: string;
  cover_image_url: string;
  alias: string;
  username_changed: boolean;
  member_since: string;
  summary: { games: number; completed: number; playing: number; lists: number; friends: number };
}

interface FavoriteSlotDto {
  slot: number;
  work_id: string | null;
}

interface ImportReport {
  preview_sha256: string;
  valid_row_count: number;
  error_count: number;
  errors: Array<{ row: number; code: string; message: string }>;
  will_create: number;
  duplicates: number;
  conflicts: number;
  can_apply: boolean;
  applied?: boolean;
  created?: number;
}

const BIO_LIMIT = 160;
const NAME_LIMIT = 40;
const IMAGE_LIMIT_BYTES = 2 * 1024 * 1024;
const ACCEPTED_TYPES = ["image/jpeg", "image/png", "image/webp"];
const TABS: Tab[] = ["account", "privacy", "preferences", "connections", "security"];
// Built-in SavePoint avatars: the gradient hue each one starts from.
const PRESET_HUES = ["var(--color-accent-edge)", "#3f5f86", "#3d6a52", "#7a5a2d", "#6b3540"];

const COPY = {
  es: {
    tabs: { account: "Cuenta", privacy: "Privacidad", preferences: "Preferencias", connections: "Conexiones", security: "Seguridad" },
    tabsLabel: "Secciones del perfil",
    loading: "Cargando perfil…",
    loadError: "No se pudo cargar el perfil. Inténtalo de nuevo.",
    save: "Guardar cambios",
    saving: "Guardando…",
    saved: "Cambios guardados",
    saveError: "No se pudieron guardar los cambios. Inténtalo de nuevo.",
    changeCover: "Cambiar portada",
    removeCover: "Quitar portada",
    changePhoto: "Cambiar foto",
    memberSince: (date: string) => `miembro desde ${date}`,
    games: (count: number) => `${count} ${count === 1 ? "juego" : "juegos"}`,
    displayName: "Nombre completo",
    username: "Nombre de usuario",
    usernameOnce: "Solo puedes cambiarlo una vez. Con él inicias sesión y te encuentran tus amistades.",
    usernameDone: "Ya has cambiado tu nombre de usuario; no se puede volver a cambiar.",
    usernameStatus: {
      checking: "Comprobando…",
      ok: "Disponible",
      taken: "Ya está en uso. Elige otro.",
      invalid: "Usa de 3 a 30 letras, números, puntos, guiones o guiones bajos.",
      same: "",
    },
    usernameChange: "Cambiar nombre de usuario",
    usernameConfirmTitle: "¿Cambiar tu nombre de usuario?",
    usernameConfirmBody: (name: string) =>
      `Pasarás a ser @${name}. Solo puedes hacerlo una vez, así que no podrás volver a cambiarlo.`,
    usernameConfirm: "Sí, cambiarlo",
    usernameError: "No se pudo cambiar el nombre de usuario. Inténtalo de nuevo.",
    cancel: "Cancelar",
    bio: "Biografía",
    optional: "(opcional)",
    favorites: "Tus 5 favoritos",
    favoritesHint: "· solo juegos de tu colección",
    addFavorite: "Añadir favorito",
    changeFavorite: (title: string) => `Cambiar favorito: ${title}`,
    viewPhoto: "Ver foto de perfil",
    photoTitle: "Foto de perfil",
    fileError: "Usa una imagen JPG, PNG o WEBP de hasta 2 MB.",
    removePhoto: "Eliminar foto",
    close: "Cerrar",
    friendsView: "Así te ven tus amistades",
    stats: { completed: "Completados", playing: "Jugando", lists: "Listas", friends: "Amistades" },
    privacy: {
      private: "Privada",
      public: "Amistades",
      rows: {
        favorites: ["Favoritos", "Los cinco juegos que destacas en tu perfil"],
        collection: ["Colección", "Estados y valoraciones de cada juego"],
        lists: ["Listas nuevas", "Visibilidad por defecto; cada lista puede cambiarla"],
      },
      note: "Las amistades son las personas con las que has aceptado una solicitud. Nadie más ve tu colección.",
    },
    preferences: {
      theme: ["Tema oscuro", "Si está desactivado se usa el tema claro"],
      language: ["Idioma", "Idioma de la interfaz"],
    },
    connections: {
      importName: "Importar archivo",
      importHint: "Filas de colección y de copias de un CSV exportado desde SavePoint",
      upload: "Subir archivo",
      previewing: "Comprobando archivo…",
      summary: (valid: number, create: number, dup: number) =>
        `${valid} filas válidas · ${create} nuevas · ${dup} ya existentes`,
      errors: "El archivo tiene problemas (solo se importan filas de colección y copias):",
      apply: "Importar",
      applying: "Importando…",
      done: (count: number) => `Importación completada: ${count} registros nuevos.`,
      failed: "No se pudo importar el archivo.",
      cancel: "Cancelar",
    },
    security: {
      password: ["Contraseña", "Cambia la contraseña con la que inicias sesión"],
      change: "Cambiar",
      current: "Contraseña actual",
      next: "Nueva contraseña",
      repeat: "Repite la nueva contraseña",
      mismatch: "Las contraseñas nuevas no coinciden.",
      updatePassword: "Actualizar contraseña",
      passwordDone: "Contraseña actualizada.",
      passwordError: "No se pudo cambiar la contraseña. Revisa la actual y que la nueva sea segura.",
      cancel: "Cancelar",
      export: ["Exportar mis datos", "Colección, copias y valoraciones en CSV o Excel"],
      exportCsv: "CSV",
      exportXlsx: "Excel",
      delete: ["Eliminar cuenta", "Se borran tu colección, listas, comentarios y amistades. No se puede deshacer."],
      deleteButton: "Eliminar…",
      deleteTitle: "¿Eliminar tu cuenta?",
      deleteBody: "Escribe tu contraseña para confirmar. Esta acción no se puede deshacer.",
      deletePassword: "Confirma tu contraseña",
      deleteConfirm: "Eliminar cuenta",
      deleteError: "No se pudo eliminar la cuenta. Revisa la contraseña.",
    },
  },
  en: {
    tabs: { account: "Account", privacy: "Privacy", preferences: "Preferences", connections: "Connections", security: "Security" },
    tabsLabel: "Profile sections",
    loading: "Loading profile…",
    loadError: "We couldn't load the profile. Try again.",
    save: "Save changes",
    saving: "Saving…",
    saved: "Changes saved",
    saveError: "We couldn't save the changes. Try again.",
    changeCover: "Change cover",
    removeCover: "Remove cover",
    changePhoto: "Change photo",
    memberSince: (date: string) => `member since ${date}`,
    games: (count: number) => `${count} ${count === 1 ? "game" : "games"}`,
    displayName: "Full name",
    username: "Username",
    usernameOnce: "You can only change it once. You sign in with it and your friends find you by it.",
    usernameDone: "You have already changed your username; it cannot be changed again.",
    usernameStatus: {
      checking: "Checking…",
      ok: "Available",
      taken: "Already in use. Pick another.",
      invalid: "Use 3 to 30 letters, numbers, dots, hyphens or underscores.",
      same: "",
    },
    usernameChange: "Change username",
    usernameConfirmTitle: "Change your username?",
    usernameConfirmBody: (name: string) =>
      `You will become @${name}. You can only do this once, so you will not be able to change it again.`,
    usernameConfirm: "Yes, change it",
    usernameError: "The username could not be changed. Try again.",
    cancel: "Cancel",
    bio: "Biography",
    optional: "(optional)",
    favorites: "Your 5 favorites",
    favoritesHint: "· only games from your collection",
    addFavorite: "Add favorite",
    changeFavorite: (title: string) => `Change favorite: ${title}`,
    viewPhoto: "View profile photo",
    photoTitle: "Profile photo",
    fileError: "Use a JPG, PNG or WEBP image of up to 2 MB.",
    removePhoto: "Remove photo",
    close: "Close",
    friendsView: "How your friends see you",
    stats: { completed: "Completed", playing: "Playing", lists: "Lists", friends: "Friends" },
    privacy: {
      private: "Private",
      public: "Friends",
      rows: {
        favorites: ["Favorites", "The five games you highlight on your profile"],
        collection: ["Collection", "Status and ratings of every game"],
        lists: ["New lists", "Default visibility; each list can change it"],
      },
      note: "Friends are the people whose request you accepted. Nobody else sees your collection.",
    },
    preferences: {
      theme: ["Dark theme", "When off, the light theme is used"],
      language: ["Language", "Interface language"],
    },
    connections: {
      importName: "Import file",
      importHint: "Collection and copy rows from a CSV exported from SavePoint",
      upload: "Upload file",
      previewing: "Checking file…",
      summary: (valid: number, create: number, dup: number) =>
        `${valid} valid rows · ${create} new · ${dup} already present`,
      errors: "The file has problems (only collection and copy rows are imported):",
      apply: "Import",
      applying: "Importing…",
      done: (count: number) => `Import finished: ${count} new records.`,
      failed: "The file could not be imported.",
      cancel: "Cancel",
    },
    security: {
      password: ["Password", "Change the password you sign in with"],
      change: "Change",
      current: "Current password",
      next: "New password",
      repeat: "Repeat the new password",
      mismatch: "The new passwords do not match.",
      updatePassword: "Update password",
      passwordDone: "Password updated.",
      passwordError: "The password could not be changed. Check the current one and that the new one is strong.",
      cancel: "Cancel",
      export: ["Export my data", "Collection, copies and ratings as CSV or Excel"],
      exportCsv: "CSV",
      exportXlsx: "Excel",
      delete: ["Delete account", "Your collection, lists, comments and friendships are deleted. This cannot be undone."],
      deleteButton: "Delete…",
      deleteTitle: "Delete your account?",
      deleteBody: "Type your password to confirm. This cannot be undone.",
      deletePassword: "Confirm your password",
      deleteConfirm: "Delete account",
      deleteError: "The account could not be deleted. Check the password.",
    },
  },
} as const;

function initialsOf(name: string): string {
  const parts = name.split(/[\s._-]+/).filter(Boolean).slice(0, 2);
  return (parts.map((part) => part[0]?.toUpperCase() ?? "").join("") || name.slice(0, 2).toUpperCase()).slice(0, 2);
}

function PersonIcon({ size }: { size: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 256 256" fill="currentColor" aria-hidden="true">
      <path d="M208 56h-27.72l-13.63-20.44A8 8 0 0 0 160 32H96a8 8 0 0 0-6.65 3.56L75.71 56H48a24 24 0 0 0-24 24v112a24 24 0 0 0 24 24h160a24 24 0 0 0 24-24V80a24 24 0 0 0-24-24Zm8 136a8 8 0 0 1-8 8H48a8 8 0 0 1-8-8V80a8 8 0 0 1 8-8h32a8 8 0 0 0 6.66-3.56L100.28 48h55.43l13.63 20.44A8 8 0 0 0 176 72h32a8 8 0 0 1 8 8ZM128 88a44 44 0 1 0 44 44 44.05 44.05 0 0 0-44-44Zm0 72a28 28 0 1 1 28-28 28 28 0 0 1-28 28Z" />
    </svg>
  );
}

async function uploadImage(kind: "avatar" | "cover", blob: Blob): Promise<Response> {
  const csrf = await ensureCsrfToken();
  const form = new FormData();
  form.append("file", blob, `${kind}.${blob.type === "image/webp" ? "webp" : "jpg"}`);
  return fetch(`/api/accounts/me/${kind}/`, {
    method: "PUT",
    credentials: "same-origin",
    headers: csrf ? { "X-CSRFToken": csrf } : {},
    body: form,
  });
}

async function postFile(path: string, file: File, digest?: string): Promise<Response> {
  const csrf = await ensureCsrfToken();
  const form = new FormData();
  form.append("file", file);
  if (digest) form.append("preview_sha256", digest);
  return fetch(path, {
    method: "POST",
    credentials: "same-origin",
    headers: csrf ? { "X-CSRFToken": csrf } : {},
    body: form,
  });
}

/** The profile page ("Perfil y ajustes"): a header with cover, photo and name,
 * and five tabs (account, privacy, preferences, connections, security). Image
 * uploads, preferences and the security actions apply as soon as they are
 * confirmed; the rest is saved with "Guardar cambios". */
export function ProfileEditor({ locale }: { locale: Locale }) {
  const copy = COPY[locale];
  const router = useRouter();
  const pathname = usePathname();

  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  const [profile, setProfile] = useState<ProfileDto | null>(null);
  const [works, setWorks] = useState<EligibleWork[]>([]);
  const [tab, setTab] = useState<Tab>("account");

  // Draft values edited on the Account and Privacy tabs.
  const [displayName, setDisplayName] = useState("");
  const [bio, setBio] = useState("");
  const [avatarMode, setAvatarMode] = useState<AvatarMode>("none");
  const [avatarUrl, setAvatarUrl] = useState("");
  const [avatarPreset, setAvatarPreset] = useState<number | null>(null);
  const [collectionVisibility, setCollectionVisibility] = useState<Visibility>("public");
  const [favoritesVisibility, setFavoritesVisibility] = useState<Visibility>("public");
  const [listVisibility, setListVisibility] = useState<Visibility>("public");
  const [favorites, setFavorites] = useState<Array<string | null>>([null, null, null, null, null]);

  const [saving, setSaving] = useState(false);
  const [feedback, setFeedback] = useState<{ kind: "ok" | "error"; text: string } | null>(null);
  const [photoOpen, setPhotoOpen] = useState(false);
  const photoDialogRef = useRef<HTMLDialogElement>(null);

  const [cropTarget, setCropTarget] = useState<{ file: File; kind: "avatar" | "cover" } | null>(null);
  const [pickerSlot, setPickerSlot] = useState<number | null>(null);
  const [darkTheme, setDarkTheme] = useState(true);

  const photoInputRef = useRef<HTMLInputElement>(null);
  const coverInputRef = useRef<HTMLInputElement>(null);
  const importInputRef = useRef<HTMLInputElement>(null);

  // Import (Connections tab).
  const [importFile, setImportFile] = useState<File | null>(null);
  const [importReport, setImportReport] = useState<ImportReport | null>(null);
  const [importBusy, setImportBusy] = useState<"previewing" | "applying" | null>(null);
  const [importMessage, setImportMessage] = useState<string | null>(null);

  // Security tab.
  const [passwordOpen, setPasswordOpen] = useState(false);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [repeatPassword, setRepeatPassword] = useState("");
  const [passwordMessage, setPasswordMessage] = useState<{ kind: "ok" | "error"; text: string } | null>(null);
  const [usernameInput, setUsernameInput] = useState("");
  const [usernameStatus, setUsernameStatus] = useState<"idle" | "checking" | "ok" | "same" | "invalid" | "taken">("idle");
  const [usernameConfirmOpen, setUsernameConfirmOpen] = useState(false);
  const [usernameError, setUsernameError] = useState(false);
  const usernameDialogRef = useRef<HTMLDialogElement>(null);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deletePassword, setDeletePassword] = useState("");
  const [deleteError, setDeleteError] = useState(false);
  const deleteDialogRef = useRef<HTMLDialogElement>(null);

  function applyProfile(next: ProfileDto) {
    setProfile(next);
    setUsernameInput(next.alias);
    setDisplayName(next.display_name);
    setBio(next.bio);
    setCollectionVisibility(next.collection_visibility);
    setFavoritesVisibility(next.favorites_visibility);
    setListVisibility(next.default_list_visibility);
    setAvatarUrl(next.avatar_url);
    setAvatarPreset(next.avatar_preset);
    setAvatarMode(
      next.avatar_image_url ? "image" : next.avatar_url ? "url" : next.avatar_preset !== null ? "preset" : "none",
    );
  }

  useEffect(() => {
    let cancelled = false;
    setDarkTheme(document.documentElement.dataset.theme !== "light");
    Promise.all([
      apiFetch("/api/accounts/me/profile/").then((r) => (r.ok ? r.json() : null)),
      apiFetch("/api/accounts/me/favorites/").then((r) => (r.ok ? r.json() : null)),
      apiFetch("/api/library/entries/").then((r) => (r.ok ? r.json() : null)),
    ])
      .then(([profileBody, favoritesBody, libraryBody]) => {
        if (cancelled) return;
        if (!profileBody) {
          setStatus("error");
          return;
        }
        applyProfile(profileBody as ProfileDto);
        if (favoritesBody && Array.isArray(favoritesBody.slots)) {
          const next: Array<string | null> = [null, null, null, null, null];
          for (const slot of favoritesBody.slots as FavoriteSlotDto[]) next[slot.slot - 1] = slot.work_id;
          setFavorites(next);
        }
        if (libraryBody && Array.isArray(libraryBody.items)) {
          setWorks(
            libraryBody.items.map(
              (item: { work_id: string; work_title: string; work_slug: string; cover: EligibleWork["cover"] }) => ({
                work_id: item.work_id,
                work_title: item.work_title,
                work_slug: item.work_slug,
                cover: item.cover,
              }),
            ),
          );
        }
        setStatus("ready");
      })
      .catch(() => {
        if (!cancelled) setStatus("error");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // Live availability check for the username field (debounced).
  const currentAlias = profile?.alias;
  const usernameLocked = profile?.username_changed ?? true;
  useEffect(() => {
    if (usernameLocked || currentAlias === undefined) return;
    const candidate = usernameInput.trim();
    if (candidate === currentAlias || candidate === "") {
      setUsernameStatus("idle");
      return;
    }
    setUsernameStatus("checking");
    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      fetch(`/api/accounts/me/username/availability/?username=${encodeURIComponent(candidate)}`, {
        credentials: "same-origin",
        signal: controller.signal,
      })
        .then((response) => (response.ok ? response.json() : null))
        .then((body) => {
          const value = body?.status;
          setUsernameStatus(value === "ok" || value === "taken" || value === "invalid" || value === "same" ? value : "idle");
        })
        .catch(() => {});
    }, 400);
    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [usernameInput, currentAlias, usernameLocked]);

  useEffect(() => {
    const dialog = photoDialogRef.current;
    if (!dialog) return;
    if (photoOpen && !dialog.open) dialog.showModal();
    if (!photoOpen && dialog.open) dialog.close();
  }, [photoOpen]);

  useEffect(() => {
    const dialog = usernameDialogRef.current;
    if (!dialog) return;
    if (usernameConfirmOpen && !dialog.open) dialog.showModal();
    if (!usernameConfirmOpen && dialog.open) dialog.close();
  }, [usernameConfirmOpen]);

  useEffect(() => {
    const dialog = deleteDialogRef.current;
    if (!dialog) return;
    if (deleteOpen && !dialog.open) dialog.showModal();
    if (!deleteOpen && dialog.open) dialog.close();
  }, [deleteOpen]);

  const worksById = useMemo(() => new Map(works.map((work) => [work.work_id, work])), [works]);
  const shownName = displayName.trim() || profile?.alias || "";
  const memberSince = useMemo(() => {
    if (!profile) return "";
    return new Intl.DateTimeFormat(locale, { month: "short", year: "numeric" }).format(new Date(profile.member_since));
  }, [profile, locale]);

  if (status === "loading") return <p aria-live="polite">{copy.loading}</p>;
  if (status === "error" || !profile) return <p role="alert">{copy.loadError}</p>;

  const avatarImageSrc =
    avatarMode === "image" && profile.avatar_image_url
      ? profile.avatar_image_url
      : avatarMode === "url" && avatarUrl.startsWith("https://")
        ? avatarUrl
        : null;
  const avatarGradient =
    avatarMode === "preset" && avatarPreset !== null
      ? `linear-gradient(150deg, ${PRESET_HUES[avatarPreset]}, var(--pf-line))`
      : undefined;
  const hasUploadedAvatar = Boolean(profile.avatar_image_url);

  function pickImage(file: File | null | undefined, kind: "avatar" | "cover") {
    if (!file) return;
    if (!ACCEPTED_TYPES.includes(file.type) || file.size > IMAGE_LIMIT_BYTES) {
      setFeedback({ kind: "error", text: copy.fileError });
      return;
    }
    setCropTarget({ file, kind });
  }

  async function confirmCrop(blob: Blob) {
    const target = cropTarget;
    setCropTarget(null);
    if (!target) return;
    try {
      const response = await uploadImage(target.kind, blob);
      if (!response.ok) {
        setFeedback({ kind: "error", text: copy.saveError });
        return;
      }
      const body = (await response.json()) as ProfileDto;
      setProfile(body);
      if (target.kind === "avatar") setAvatarMode("image");
      window.dispatchEvent(new Event("savepoint:profile-updated"));
      router.refresh();
    } catch {
      setFeedback({ kind: "error", text: copy.saveError });
    }
  }

  async function removeCover() {
    const response = await apiFetch("/api/accounts/me/cover/", { method: "DELETE" });
    if (response.ok) setProfile((await response.json()) as ProfileDto);
  }

  async function removePhoto() {
    setPhotoOpen(false);
    try {
      if (hasUploadedAvatar) await apiFetch("/api/accounts/me/avatar/", { method: "DELETE" });
      const response = await apiFetch("/api/accounts/me/profile/", {
        method: "PATCH",
        body: { avatar_url: "", avatar_preset: null },
      });
      if (!response.ok) throw new Error("avatar");
      const next = (await response.json()) as ProfileDto;
      setProfile(next);
      setAvatarUrl("");
      setAvatarPreset(null);
      setAvatarMode("none");
      window.dispatchEvent(new Event("savepoint:profile-updated"));
      router.refresh();
    } catch {
      setFeedback({ kind: "error", text: copy.saveError });
    }
  }

  async function save() {
    setSaving(true);
    setFeedback(null);
    try {
      const response = await apiFetch("/api/accounts/me/profile/", {
        method: "PATCH",
        body: {
          display_name: displayName.trim(),
          bio,
          avatar_url: avatarMode === "url" ? avatarUrl.trim() : "",
          avatar_preset: avatarMode === "preset" ? avatarPreset : null,
          collection_visibility: collectionVisibility,
          favorites_visibility: favoritesVisibility,
          default_list_visibility: listVisibility,
        },
      });
      if (!response.ok) throw new Error("profile");
      let next = (await response.json()) as ProfileDto;
      if (avatarMode !== "image" && next.avatar_image_url) {
        const cleared = await apiFetch("/api/accounts/me/avatar/", { method: "DELETE" });
        if (cleared.ok) next = (await cleared.json()) as ProfileDto;
      }
      const slots = favorites
        .map((workId, index) => (workId ? { slot: index + 1, work_id: workId } : null))
        .filter((slot): slot is { slot: number; work_id: string } => slot !== null);
      const favoritesResponse = await apiFetch("/api/accounts/me/favorites/", { method: "PUT", body: { slots } });
      if (!favoritesResponse.ok) throw new Error("favorites");
      applyProfile(next);
      window.dispatchEvent(new Event("savepoint:profile-updated"));
      setFeedback({ kind: "ok", text: copy.saved });
      router.refresh();
    } catch {
      setFeedback({ kind: "error", text: copy.saveError });
    } finally {
      setSaving(false);
    }
  }

  async function confirmUsernameChange() {
    setUsernameConfirmOpen(false);
    setUsernameError(false);
    try {
      const response = await apiFetch("/api/accounts/me/username/", {
        method: "POST",
        body: { username: usernameInput.trim() },
      });
      if (!response.ok) {
        const body = (await response.json().catch(() => null)) as { code?: string } | null;
        if (body?.code === "taken") setUsernameStatus("taken");
        else if (body?.code === "invalid") setUsernameStatus("invalid");
        else setUsernameError(true);
        return;
      }
      const next = (await response.json()) as ProfileDto;
      setProfile(next);
      setUsernameInput(next.alias);
      setUsernameStatus("idle");
      window.dispatchEvent(new CustomEvent("savepoint:username-changed", { detail: { username: next.alias } }));
      router.refresh();
    } catch {
      setUsernameError(true);
    }
  }

  function toggleTheme() {
    const next = darkTheme ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    document.cookie = `sp-theme=${next};path=/;max-age=31536000;SameSite=Lax`;
    setDarkTheme(next === "dark");
  }

  function changeLanguage(next: Locale) {
    if (next === locale) return;
    document.cookie = `locale=${next};path=/;max-age=31536000;SameSite=Lax`;
    router.push(pathname.replace(/^\/(?:es|en)(?=\/|$)/, `/${next}`));
  }

  async function previewImport(file: File | undefined) {
    if (!file) return;
    setImportFile(file);
    setImportReport(null);
    setImportMessage(null);
    setImportBusy("previewing");
    try {
      const response = await postFile("/api/library/import/preview/", file);
      if (!response.ok) throw new Error("preview");
      setImportReport((await response.json()) as ImportReport);
    } catch {
      setImportMessage(copy.connections.failed);
      setImportFile(null);
    } finally {
      setImportBusy(null);
    }
  }

  async function applyImport() {
    if (!importFile || !importReport) return;
    setImportBusy("applying");
    try {
      const response = await postFile("/api/library/import/apply/", importFile, importReport.preview_sha256);
      if (!response.ok) throw new Error("apply");
      const body = (await response.json()) as ImportReport;
      setImportMessage(copy.connections.done(body.created ?? importReport.will_create));
      setImportReport(null);
      setImportFile(null);
      router.refresh();
    } catch {
      setImportMessage(copy.connections.failed);
    } finally {
      setImportBusy(null);
    }
  }

  async function submitPassword() {
    setPasswordMessage(null);
    if (newPassword !== repeatPassword) {
      setPasswordMessage({ kind: "error", text: copy.security.mismatch });
      return;
    }
    const response = await apiFetch("/api/accounts/me/password/", {
      method: "POST",
      body: { current_password: currentPassword, new_password: newPassword },
    });
    if (!response.ok) {
      setPasswordMessage({ kind: "error", text: copy.security.passwordError });
      return;
    }
    setPasswordMessage({ kind: "ok", text: copy.security.passwordDone });
    setCurrentPassword("");
    setNewPassword("");
    setRepeatPassword("");
    setPasswordOpen(false);
  }

  async function confirmDelete() {
    setDeleteError(false);
    const response = await apiFetch("/api/accounts/me/delete/", { method: "POST", body: { password: deletePassword } });
    if (!response.ok) {
      setDeleteError(true);
      return;
    }
    setDeleteOpen(false);
    // Full page load: the account is gone, so no per-user state may survive.
    window.location.assign(`/${locale}`);
  }

  function onTabKey(event: React.KeyboardEvent<HTMLButtonElement>, index: number) {
    const step = event.key === "ArrowRight" ? 1 : event.key === "ArrowLeft" ? -1 : 0;
    if (!step) return;
    event.preventDefault();
    const next = TABS[(index + step + TABS.length) % TABS.length];
    setTab(next);
    document.getElementById(`pf-tab-${next}`)?.focus();
  }

  const avatarFace = (
    <>
      {avatarImageSrc ? (
        // eslint-disable-next-line @next/next/no-img-element -- owner's own image (own endpoint or a typed https URL)
        <img src={avatarImageSrc} alt="" width={112} height={112} onError={() => setAvatarMode("none")} />
      ) : (
        <span>{initialsOf(shownName)}</span>
      )}
    </>
  );

  const avatar = (
    <div
      className="sp-pf-avatar"
      style={avatarGradient ? { backgroundImage: avatarGradient } : undefined}
    >
      {avatarFace}
    </div>
  );

  const segmented = (value: Visibility, onChange: (next: Visibility) => void, label: string) => (
    <div className="sp-pf-segmented" role="radiogroup" aria-label={label}>
      {(["private", "public"] as const).map((option) => (
        <button
          key={option}
          type="button"
          role="radio"
          aria-checked={value === option}
          className={value === option ? "is-on" : undefined}
          onClick={() => onChange(option)}
        >
          {copy.privacy[option]}
        </button>
      ))}
    </div>
  );

  const favoriteTiles = favorites.map((workId, index) => {
    const work = workId ? worksById.get(workId) : undefined;
    return (
      <button
        key={index}
        type="button"
        className={`sp-pf-fav${work ? " is-filled" : ""}`}
        aria-label={work ? copy.changeFavorite(work.work_title) : `${copy.addFavorite} ${index + 1}`}
        onClick={() => setPickerSlot(index + 1)}
      >
        {work ? (
          <>
            <CoverImage src={work.cover.url} alt="" title={work.work_title} missingLabel="" width={84} height={112} />
            <span className="visually-hidden">{work.work_title}</span>
          </>
        ) : (
          <span aria-hidden="true">+</span>
        )}
      </button>
    );
  });

  const headerCovers = favorites
    .map((workId) => (workId ? worksById.get(workId) : undefined))
    .filter((work): work is EligibleWork => Boolean(work))
    .slice(0, 3);

  return (
    <div className="sp-pf">
      <div className="sp-pf-card">
        <div
          className="sp-pf-banner"
          style={profile.cover_image_url ? { backgroundImage: `url(${profile.cover_image_url})` } : undefined}
        >
          <div className="sp-pf-banner-actions">
            {profile.cover_image_url ? (
              <button type="button" className="sp-pf-ghost" onClick={removeCover}>
                {copy.removeCover}
              </button>
            ) : null}
            <button type="button" className="sp-pf-ghost" onClick={() => coverInputRef.current?.click()}>
              {copy.changeCover}
            </button>
            <input
              ref={coverInputRef}
              type="file"
              accept={ACCEPTED_TYPES.join(",")}
              hidden
              onChange={(event) => {
                pickImage(event.target.files?.[0], "cover");
                event.target.value = "";
              }}
            />
          </div>
          {!profile.cover_image_url && headerCovers.length > 0 ? (
            <div className="sp-pf-banner-covers" aria-hidden="true">
              {headerCovers.map((work) => (
                <span key={work.work_id}>
                  <CoverImage src={work.cover.url} alt="" title="" missingLabel="" width={46} height={61} />
                </span>
              ))}
            </div>
          ) : null}
        </div>

        <div className="sp-pf-head">
          <div className="sp-pf-identity">
            <input
              ref={photoInputRef}
              type="file"
              accept={ACCEPTED_TYPES.join(",")}
              hidden
              onChange={(event) => {
                pickImage(event.target.files?.[0], "avatar");
                event.target.value = "";
              }}
            />
            <div className="sp-pf-avatar-wrap">
              <button type="button" className="sp-pf-avatar-btn" aria-label={copy.viewPhoto} onClick={() => setPhotoOpen(true)}>
                {avatar}
              </button>
              <button
                type="button"
                className="sp-pf-camera"
                aria-label={copy.changePhoto}
                title={copy.changePhoto}
                onClick={() => photoInputRef.current?.click()}
              >
                <PersonIcon size={16} />
              </button>
            </div>
            <div className="sp-pf-who">
              <h1>{shownName}</h1>
              <span className="sp-pf-meta">
                @{profile.alias} · {copy.memberSince(memberSince)} · {copy.games(profile.summary.games)}
              </span>
            </div>
          </div>
          <div className="sp-pf-head-actions">
          {feedback ? (
            <p
              role="status"
              data-testid="profile-feedback"
              className={`sp-pf-feedback${feedback.kind === "error" ? " is-error" : ""}`}
            >
              {feedback.text}
            </p>
          ) : null}
            <button type="button" className="sp-pf-save" onClick={save} disabled={saving}>
              {saving ? copy.saving : copy.save}
            </button>
          </div>
        </div>

        <div className="sp-pf-tabs" role="tablist" aria-label={copy.tabsLabel}>
          {TABS.map((id, index) => (
            <button
              key={id}
              id={`pf-tab-${id}`}
              type="button"
              role="tab"
              aria-selected={tab === id}
              aria-controls={`pf-panel-${id}`}
              tabIndex={tab === id ? 0 : -1}
              className={tab === id ? "is-on" : undefined}
              onClick={() => setTab(id)}
              onKeyDown={(event) => onTabKey(event, index)}
            >
              {copy.tabs[id]}
            </button>
          ))}
        </div>

        <div className="sp-pf-body">
          <div className="sp-pf-main" role="tabpanel" id={`pf-panel-${tab}`} aria-labelledby={`pf-tab-${tab}`}>
            {tab === "account" ? (
              <>
                <div className="sp-pf-two">
                  <label className="sp-pf-field">
                    <span>{copy.displayName}</span>
                    <input
                      type="text"
                      value={displayName}
                      maxLength={NAME_LIMIT}
                      onChange={(event) => setDisplayName(event.target.value)}
                    />
                  </label>
                  <div className="sp-pf-field">
                    <label htmlFor="pf-username">{copy.username}</label>
                    <div className="sp-pf-username-row">
                      <input
                        id="pf-username"
                        type="text"
                        className="is-mono"
                        value={usernameInput}
                        maxLength={30}
                        readOnly={profile.username_changed}
                        autoComplete="off"
                        spellCheck={false}
                        aria-describedby="pf-username-help"
                        onChange={(event) => setUsernameInput(event.target.value)}
                      />
                      {!profile.username_changed ? (
                        <button
                          type="button"
                          className="sp-pf-action is-accent"
                          disabled={usernameStatus !== "ok"}
                          onClick={() => setUsernameConfirmOpen(true)}
                        >
                          {copy.usernameChange}
                        </button>
                      ) : null}
                    </div>
                    <span id="pf-username-help" className="sp-pf-username-help" role="status">
                      {profile.username_changed
                        ? copy.usernameDone
                        : usernameStatus === "ok"
                          ? <span className="is-ok">{copy.usernameStatus.ok}</span>
                          : usernameStatus === "checking"
                            ? copy.usernameStatus.checking
                            : usernameStatus === "taken" || usernameStatus === "invalid"
                              ? <span className="is-error">{copy.usernameStatus[usernameStatus]}</span>
                              : copy.usernameOnce}
                      {usernameError ? <span className="is-error"> {copy.usernameError}</span> : null}
                    </span>
                  </div>
                </div>
                <label className="sp-pf-field">
                  <span>
                    {copy.bio} <em>{copy.optional}</em>
                  </span>
                  <textarea
                    rows={3}
                    value={bio}
                    maxLength={BIO_LIMIT}
                    onChange={(event) => setBio(event.target.value)}
                  />
                  <span className="sp-pf-count">
                    {bio.length} / {BIO_LIMIT}
                  </span>
                </label>
                <div className="sp-pf-field">
                  <span>
                    {copy.favorites} <em>{copy.favoritesHint}</em>
                  </span>
                  <div className="sp-pf-favs">{favoriteTiles}</div>
                </div>
              </>
            ) : null}

            {tab === "privacy" ? (
              <div className="sp-pf-rows">
                <div className="sp-pf-row">
                  <div>
                    <span className="sp-pf-row-title">{copy.privacy.rows.favorites[0]}</span>
                    <span className="sp-pf-row-hint">{copy.privacy.rows.favorites[1]}</span>
                  </div>
                  {segmented(favoritesVisibility, setFavoritesVisibility, copy.privacy.rows.favorites[0])}
                </div>
                <div className="sp-pf-row">
                  <div>
                    <span className="sp-pf-row-title">{copy.privacy.rows.collection[0]}</span>
                    <span className="sp-pf-row-hint">{copy.privacy.rows.collection[1]}</span>
                  </div>
                  {segmented(collectionVisibility, setCollectionVisibility, copy.privacy.rows.collection[0])}
                </div>
                <div className="sp-pf-row">
                  <div>
                    <span className="sp-pf-row-title">{copy.privacy.rows.lists[0]}</span>
                    <span className="sp-pf-row-hint">{copy.privacy.rows.lists[1]}</span>
                  </div>
                  {segmented(listVisibility, setListVisibility, copy.privacy.rows.lists[0])}
                </div>
                <p className="sp-pf-note">{copy.privacy.note}</p>
              </div>
            ) : null}

            {tab === "preferences" ? (
              <div className="sp-pf-rows">
                <div className="sp-pf-row">
                  <div>
                    <span className="sp-pf-row-title">{copy.preferences.theme[0]}</span>
                    <span className="sp-pf-row-hint">{copy.preferences.theme[1]}</span>
                  </div>
                  <button
                    type="button"
                    role="switch"
                    aria-checked={darkTheme}
                    aria-label={copy.preferences.theme[0]}
                    className={`sp-pf-switch${darkTheme ? " is-on" : ""}`}
                    onClick={toggleTheme}
                  >
                    <span />
                  </button>
                </div>
                <div className="sp-pf-row">
                  <div>
                    <span className="sp-pf-row-title">{copy.preferences.language[0]}</span>
                    <span className="sp-pf-row-hint">{copy.preferences.language[1]}</span>
                  </div>
                  <div className="sp-pf-segmented" role="radiogroup" aria-label={copy.preferences.language[0]}>
                    {(["es", "en"] as const).map((option) => (
                      <button
                        key={option}
                        type="button"
                        role="radio"
                        aria-checked={locale === option}
                        className={locale === option ? "is-on" : undefined}
                        onClick={() => changeLanguage(option)}
                      >
                        {option === "es" ? "Español" : "English"}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            ) : null}

            {tab === "connections" ? (
              <div className="sp-pf-conns">
                <div className="sp-pf-conn">
                  <span className="sp-pf-conn-icon">CSV</span>
                  <div>
                    <span className="sp-pf-row-title">{copy.connections.importName}</span>
                    <span className="sp-pf-row-hint">
                      {importBusy === "previewing" ? copy.connections.previewing : copy.connections.importHint}
                    </span>
                  </div>
                  <button
                    type="button"
                    className="sp-pf-action is-accent"
                    onClick={() => importInputRef.current?.click()}
                    disabled={importBusy !== null}
                  >
                    {copy.connections.upload}
                  </button>
                  <input
                    ref={importInputRef}
                    type="file"
                    accept=".csv,text/csv"
                    hidden
                    onChange={(event) => {
                      void previewImport(event.target.files?.[0]);
                      event.target.value = "";
                    }}
                  />
                </div>
                {importReport ? (
                  <div className="sp-pf-import" role="status">
                    <p>{copy.connections.summary(importReport.valid_row_count, importReport.will_create, importReport.duplicates)}</p>
                    {importReport.errors.length > 0 ? (
                      <>
                        <p>{copy.connections.errors}</p>
                        <ul>
                          {importReport.errors.slice(0, 5).map((error, index) => (
                            <li key={index}>
                              {error.row}: {error.message}
                            </li>
                          ))}
                        </ul>
                      </>
                    ) : null}
                    <div className="sp-pf-inline-actions">
                      <button
                        type="button"
                        className="sp-pf-action"
                        onClick={() => {
                          setImportReport(null);
                          setImportFile(null);
                        }}
                      >
                        {copy.connections.cancel}
                      </button>
                      <button
                        type="button"
                        className="sp-pf-action is-accent"
                        onClick={applyImport}
                        disabled={!importReport.can_apply || importBusy !== null}
                      >
                        {importBusy === "applying" ? copy.connections.applying : copy.connections.apply}
                      </button>
                    </div>
                  </div>
                ) : null}
                {importMessage ? (
                  <p role="status" className="sp-pf-note">
                    {importMessage}
                  </p>
                ) : null}
              </div>
            ) : null}

            {tab === "security" ? (
              <div className="sp-pf-rows">
                <div className="sp-pf-row">
                  <div>
                    <span className="sp-pf-row-title">{copy.security.password[0]}</span>
                    <span className="sp-pf-row-hint">{copy.security.password[1]}</span>
                  </div>
                  <button type="button" className="sp-pf-action" onClick={() => setPasswordOpen((open) => !open)}>
                    {copy.security.change}
                  </button>
                </div>
                {passwordOpen ? (
                  <form
                    className="sp-pf-password"
                    onSubmit={(event) => {
                      event.preventDefault();
                      void submitPassword();
                    }}
                  >
                    <label className="sp-pf-field">
                      <span>{copy.security.current}</span>
                      <input
                        type="password"
                        autoComplete="current-password"
                        value={currentPassword}
                        onChange={(event) => setCurrentPassword(event.target.value)}
                      />
                    </label>
                    <label className="sp-pf-field">
                      <span>{copy.security.next}</span>
                      <input
                        type="password"
                        autoComplete="new-password"
                        value={newPassword}
                        onChange={(event) => setNewPassword(event.target.value)}
                      />
                    </label>
                    <label className="sp-pf-field">
                      <span>{copy.security.repeat}</span>
                      <input
                        type="password"
                        autoComplete="new-password"
                        value={repeatPassword}
                        onChange={(event) => setRepeatPassword(event.target.value)}
                      />
                    </label>
                    <div className="sp-pf-inline-actions">
                      <button type="button" className="sp-pf-action" onClick={() => setPasswordOpen(false)}>
                        {copy.security.cancel}
                      </button>
                      <button
                        type="submit"
                        className="sp-pf-action is-accent"
                        disabled={!currentPassword || !newPassword || !repeatPassword}
                      >
                        {copy.security.updatePassword}
                      </button>
                    </div>
                  </form>
                ) : null}
                {passwordMessage ? (
                  <p
                    role="status"
                    className={`sp-pf-note${passwordMessage.kind === "error" ? " is-error" : ""}`}
                  >
                    {passwordMessage.text}
                  </p>
                ) : null}
                <div className="sp-pf-row">
                  <div>
                    <span className="sp-pf-row-title">{copy.security.export[0]}</span>
                    <span className="sp-pf-row-hint">{copy.security.export[1]}</span>
                  </div>
                  <div className="sp-pf-inline-actions">
                    <a className="sp-pf-action is-accent" href="/api/library/export/collection.csv">
                      {copy.security.exportCsv}
                    </a>
                    <a className="sp-pf-action is-accent" href={`/api/library/export/collection.xlsx?lang=${locale}`}>
                      {copy.security.exportXlsx}
                    </a>
                  </div>
                </div>
                <div className="sp-pf-danger">
                  <div>
                    <span className="sp-pf-row-title">{copy.security.delete[0]}</span>
                    <span className="sp-pf-row-hint">{copy.security.delete[1]}</span>
                  </div>
                  <button
                    type="button"
                    className="sp-pf-action is-danger"
                    onClick={() => {
                      setDeletePassword("");
                      setDeleteError(false);
                      setDeleteOpen(true);
                    }}
                  >
                    {copy.security.deleteButton}
                  </button>
                </div>
              </div>
            ) : null}
          </div>

          <aside className="sp-pf-side">
            <div className="sp-pf-panel">
              <div className="sp-pf-eyebrow">{copy.friendsView.toUpperCase()}</div>
              <div className="sp-pf-stats">
                {(
                  [
                    ["completed", profile.summary.completed],
                    ["playing", profile.summary.playing],
                    ["lists", profile.summary.lists],
                    ["friends", profile.summary.friends],
                  ] as const
                ).map(([key, value]) => (
                  <div key={key}>
                    <strong>{value}</strong>
                    <span>{copy.stats[key]}</span>
                  </div>
                ))}
              </div>
            </div>
          </aside>
        </div>
      </div>

      <dialog
        ref={photoDialogRef}
        className="sp-copy-dialog sp-pf-photo-dialog"
        aria-labelledby="pf-photo-title"
        onClose={() => setPhotoOpen(false)}
      >
        <div className="sp-copy-dialog-body">
          <h3 id="pf-photo-title">{copy.photoTitle}</h3>
          <div className="sp-pf-avatar is-large" style={avatarGradient ? { backgroundImage: avatarGradient } : undefined}>
            {avatarFace}
          </div>
          <div className="sp-copy-dialog-actions">
            {avatarMode !== "none" ? (
              <button type="button" className="sp-copy-remove" onClick={removePhoto}>
                {copy.removePhoto}
              </button>
            ) : null}
            <button type="button" className="sp-copy-cancel" onClick={() => setPhotoOpen(false)}>
              {copy.close}
            </button>
            <button
              type="button"
              className="sp-btn-primary"
              onClick={() => {
                setPhotoOpen(false);
                photoInputRef.current?.click();
              }}
            >
              {copy.changePhoto}
            </button>
          </div>
        </div>
      </dialog>

      <ProfileImageCropper
        file={cropTarget?.file ?? null}
        shape={cropTarget?.kind === "cover" ? "banner" : "circle"}
        outWidth={cropTarget?.kind === "cover" ? 1600 : 320}
        outHeight={cropTarget?.kind === "cover" ? 232 : 320}
        locale={locale}
        onCancel={() => setCropTarget(null)}
        onConfirm={confirmCrop}
      />

      <ProfileFavoritePicker
        slot={pickerSlot}
        works={works}
        takenWorkIds={favorites.filter((id): id is string => Boolean(id))}
        currentWorkId={pickerSlot !== null ? favorites[pickerSlot - 1] : null}
        locale={locale}
        onPick={(workId) => {
          if (pickerSlot !== null) {
            setFavorites((previous) => previous.map((current, index) => (index === pickerSlot - 1 ? workId : current)));
          }
          setPickerSlot(null);
        }}
        onClose={() => setPickerSlot(null)}
      />

      <dialog
        ref={usernameDialogRef}
        className="sp-copy-dialog sp-confirm-dialog"
        aria-labelledby="pf-username-title"
        onClose={() => setUsernameConfirmOpen(false)}
      >
        <div className="sp-copy-dialog-body">
          <h3 id="pf-username-title">{copy.usernameConfirmTitle}</h3>
          <p style={{ margin: 0 }}>{copy.usernameConfirmBody(usernameInput.trim())}</p>
          <div className="sp-copy-dialog-actions">
            <button type="button" className="sp-copy-cancel" onClick={() => setUsernameConfirmOpen(false)}>
              {copy.cancel}
            </button>
            <button type="button" className="sp-btn-primary" onClick={confirmUsernameChange}>
              {copy.usernameConfirm}
            </button>
          </div>
        </div>
      </dialog>

      <dialog
        ref={deleteDialogRef}
        className="sp-copy-dialog sp-confirm-dialog"
        aria-labelledby="pf-delete-title"
        onClose={() => setDeleteOpen(false)}
      >
        <div className="sp-copy-dialog-body">
          <h3 id="pf-delete-title">{copy.security.deleteTitle}</h3>
          <p style={{ margin: 0 }}>{copy.security.deleteBody}</p>
          <div className="sp-field">
            <label htmlFor="pf-delete-password">{copy.security.deletePassword}</label>
            <input
              id="pf-delete-password"
              type="password"
              autoComplete="current-password"
              value={deletePassword}
              onChange={(event) => setDeletePassword(event.target.value)}
            />
          </div>
          {deleteError ? (
            <p role="alert" style={{ margin: 0, color: "var(--color-danger)" }}>
              {copy.security.deleteError}
            </p>
          ) : null}
          <div className="sp-copy-dialog-actions">
            <button type="button" className="sp-copy-cancel" onClick={() => setDeleteOpen(false)}>
              {copy.security.cancel}
            </button>
            <button
              type="button"
              className="sp-comment-confirm-delete"
              onClick={confirmDelete}
              disabled={!deletePassword}
            >
              {copy.security.deleteConfirm}
            </button>
          </div>
        </div>
      </dialog>
    </div>
  );
}
