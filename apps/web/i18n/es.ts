/**
 * Spanish dictionary (D-10: Spanish is the initial locale unless the
 * visitor's preference/Accept-Language says otherwise, with a persistent
 * switch and English/original-value fallback). Every key here MUST have an
 * exact counterpart in en.ts -- apps/web/tests/i18n.test.ts enforces
 * parity. See dictionary.ts for the shared shape.
 */

import type { Dictionary } from "./dictionary";

export const es: Dictionary = {
  nav: {
    home: "Inicio",
    catalogue: "Catálogo",
    collection: "Colección",
    profile: "Perfil",
    sources: "Fuentes",
    login: "Iniciar sesión",
    logout: "Cerrar sesión",
    skipToContent: "Saltar al contenido",
    openMenu: "Abrir menú",
    closeMenu: "Cerrar menú",
  },
  catalogue: {
    heading: "Catálogo",
    searchLabel: "Buscar juegos",
    clearSearch: "Borrar búsqueda",
    emptyHeading: "No encontramos juegos",
    emptyBody: "Prueba con otro título o revisa la ortografía.",
    resultCount: {
      zero: "0 resultados",
      one: "1 resultado",
      many: (count) => `${count} resultados`,
    },
  },
  collection: {
    heading: "Colección",
    emptyHeading: "Tu colección está vacía",
    emptyBody: "Añade un estado o una copia desde la ficha de un juego.",
    statusSummaryCount: {
      zero: "0",
      one: "1",
      many: (count) => `${count}`,
    },
    ownedCopyCount: {
      zero: "0 copias",
      one: "1 copia",
      many: (count) => `${count} copias`,
    },
  },
  status: {
    legend: "Estado:",
    labels: {
      pending: "Pendiente",
      playing: "Jugando",
      completed: "Completado",
      abandoned: "Abandonado",
    },
    save: "Guardar estado",
    saveSuccess: "Estado guardado",
  },
  rating: {
    unrated: "Sin valorar",
    save: "Guardar valoración",
    saveSuccess: "Valoración guardada",
  },
  errors: {
    generic: "No se pudo cargar esta información. Inténtalo de nuevo.",
    invalidCredentials: "El nombre de usuario o la contraseña no son correctos. Comprueba los datos e inténtalo de nuevo.",
    homepageSampleFailure: "No se pudo cargar la muestra del catálogo. Puedes abrir el catálogo completo.",
    openFullCatalogue: "Abrir catálogo completo",
    retryCatalogue: "Reintentar catálogo",
    retryGameDetails: "Reintentar detalles del juego",
    retrySearch: "Reintentar búsqueda",
    retryStatusSave: "Reintentar guardado del estado",
    retryRatingSave: "Reintentar guardado de la valoración",
    retrySignIn: "Reintentar inicio de sesión",
  },
  loading: {
    generic: "Cargando…",
  },
  provenance: {
    heading: "Procedencia",
    notAvailable: "No disponible",
  },
};
