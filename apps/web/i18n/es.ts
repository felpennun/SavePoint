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
    recommendations: "Recomendaciones",
    profile: "Perfil",
    sources: "Fuentes",
    login: "Iniciar sesión",
    loginAria: "Iniciar sesión",
    logout: "Cerrar sesión",
    account: "Cuenta",
    skipToContent: "Saltar al contenido",
    openMenu: "Abrir menú",
    closeMenu: "Cerrar menú",
    search: "Buscar por nombre",
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
    gamesCount: {
      zero: "0 juegos",
      one: "1 juego",
      many: (count) => `${count} juegos`,
    },
    filteredCount: {
      zero: "0 juegos coinciden",
      one: "1 juego coincide",
      many: (count) => `${count} juegos coinciden`,
    },
    viewFull: "Vista filtrada — {n} de {total} juegos",
    filters: {
      heading: "Filtros",
      platform: "Plataforma",
      genre: "Género",
      yearFrom: "Año desde",
      yearTo: "Año hasta",
      minRating: "Valoración IGDB mínima",
      anyOption: "Cualquiera",
      apply: "Aplicar filtros",
      clearAll: "Borrar todos los filtros",
      mobileToggle: "Filtros ({n} activos)",
      unavailable: "Algunos filtros no están disponibles ahora mismo. La búsqueda sigue funcionando.",
      activeLabel: {
        zero: "Sin filtros",
        one: "1 filtro",
        many: (count) => `${count} filtros`,
      },
      emptyHeading: "Ningún juego coincide con estos filtros",
      emptyBody: "Quita un filtro o amplía tu búsqueda.",
    },
    facet: {
      selectedCount: {
        zero: "Cualquiera",
        one: "1 seleccionado",
        many: (count) => `${count} seleccionados`,
      },
      clear: "Quitar",
      searchInList: "Filtrar esta lista",
    },
    chip: {
      genre: "Género: {value}",
      platform: "Plataforma: {value}",
    },
  },
  card: {
    score: {
      label: "Valoración",
      aria: "Valoración {n} de 100",
      none: "Sin valoración",
    },
    rating: {
      aria: "Tu valoración: {n} de 5",
    },
  },
  detail: {
    synopsis: {
      heading: "Sinopsis",
      showMore: "Mostrar más",
      showLess: "Mostrar menos",
    },
    ratingBreakdown: "Basada en la valoración de {igdb} usuarios de IGDB y {savepoint} de SavePoint.",
    ratingBreakdownExternalOnly: "Basada en la valoración de {igdb} usuarios de IGDB.",
    ratingBreakdownLocalOnly: "Basada en la valoración de {savepoint} usuarios de SavePoint.",
    summary: "Sinopsis",
    summaryUnavailable: "No hay una sinopsis disponible en español para este juego.",
    ratings: "Valoraciones",
    releases: "Lanzamientos y ediciones",
    editions: "Ediciones",
    relatedContent: "Contenido relacionado",
    dlc: "DLC",
    expansion: "Expansión",
    igdbRating: "Valoración IGDB",
    genres: "Géneros",
    platforms: "Plataformas",
    releaseDate: "Fecha de lanzamiento",
    addToCollection: "Añadir a la colección",
    inCollection: "En tu colección",
    attribution: "Datos de IGDB.com",
    seeSources: "Ver todas las fuentes",
  },
  recommendations: {
    nav: "Recomendaciones",
    heading: "Recomendaciones según tus géneros y valoraciones",
    intro:
      "Generado a partir de los géneros de los juegos que has valorado y completado, priorizando los mejor valorados del catálogo. No es el ranking de popularidad de la demo.",
    excludedNote: "No se muestran los juegos que ya están en tu colección.",
    methodHeading: "Cómo se generan",
    methodAlgorithm:
      "Algoritmo: {id} — una heurística determinista de géneros que ordena por valoración del catálogo, no el ranking de popularidad de la demo ni un modelo entrenado.",
    shelfHeading: "Porque juegas mucho a {genre}",
    shelfEvidence:
      "Estos juegos comparten el género {genre} con títulos que has valorado o a los que has puesto un estado.",
    cardEvidence: "Comparte tus géneros: {genres}",
    contentCardEvidence: "Coincide contigo en {reasons}.",
    emptyHeading: "Aún no hay suficiente actividad",
    emptyBody: "Añade juegos a tu colección y, si quieres, valóralos o marca su estado para empezar a recibir recomendaciones.",
    emptyCta: "Explorar el catálogo",
    error: "No se pudieron cargar tus recomendaciones. Inténtalo de nuevo.",
    retry: "Cargar recomendaciones",
    contentHeading: "Recomendado para ti",
    contentSections: {
      weighted: {
        heading: "Afinidad por contenido",
        description: "Combina similitud de contenido, tus valoraciones y señales de calidad y popularidad.",
      },
      multiplicative: {
        heading: "Afinidad equilibrada",
        description: "Combina las señales para que ninguna compense por completo una afinidad muy baja en otra.",
      },
      twoStage: {
        heading: "Afinidad en dos etapas",
        description: "Primero encuentra obras afines por contenido y después las ordena con señales escalares.",
      },
      negative: {
        heading: "Afinidad con tus preferencias en cuenta",
        description: "Refuerza lo que valoras y reduce géneros que has valorado negativamente varias veces.",
      },
      weightedPop: {
        heading: "Afinidad por contenido y popularidad",
        description: "Combina contenido, rating-confidence y PopScore; la falta de PopScore usa el mínimo.",
      },
      multiplicativePop: {
        heading: "Afinidad equilibrada con popularidad",
        description: "Multiplica afinidad y calidad, y ajusta la popularidad entre una penalización y un refuerzo del 15 %.",
      },
      twoStagePop: {
        heading: "Afinidad en dos etapas con popularidad",
        description: "La similitud decide la banda; dentro de ella ordenan rating-confidence y PopScore.",
      },
      negativePop: {
        heading: "Afinidad con preferencias y popularidad",
        description: "Refuerza tus preferencias y la actividad del catálogo, manteniendo la penalización de similitud negativa.",
      },
      recency: {
        heading: "Novedades afines a ti",
        description: "Usa las mismas señales personalizadas y añade la novedad de la fecha de lanzamiento.",
      },
      mmr: {
        heading: "Afinidad diversa por contenido",
        description: "Parte de Weighted y reduce la repetición entre juegos demasiado parecidos.",
      },
      mmrPop: {
        heading: "Afinidad diversa con popularidad",
        description: "Parte de Weighted-Pop y equilibra relevancia, PopScore y variedad.",
      },
      collaborative: {
        heading: "Coincidencia con usuarios similares",
        description: "Aprende de usuarios con valoraciones parecidas y prioriza juegos que ellos han valorado positivamente.",
      },
      hybrid: {
        heading: "Afinidad híbrida",
        description: "Combina la afinidad de contenido Weighted con las valoraciones de usuarios similares.",
      },
      hybridMmr: {
        heading: "Afinidad híbrida diversa",
        description: "Combina contenido y colaboración con MMR para reducir repeticiones entre juegos muy parecidos.",
      },
    },
    genreDescription: "Heurística basada en los géneros de tu actividad y en la valoración del catálogo.",
    refreshPreparing: "Estamos preparando tus recomendaciones.",
    refreshUpdating: "Estamos actualizando tus recomendaciones; mientras tanto ves la versión anterior.",
    refreshNeedsCollectionChange: "Modifica tu colección para actualizar tus recomendaciones.",
    dlc: {
      heading: "Para tus juegos",
      intro: "Contenido descargable de juegos que ya tienes en tu colección.",
      baseGameLabel: "DLC de {game}",
    },
  },
  collection: {
    heading: "Colección",
    subheading: "Todos los juegos que has marcado, valorado o de los que tienes una copia.",
    emptyHeading: "Tu colección está vacía",
    emptyBody: "Explora el catálogo para añadir juegos.",
    emptyCta: "Explorar el catálogo",
    count: {
      zero: "0 juegos en tu colección",
      one: "1 juego en tu colección",
      many: (count) => `${count} juegos en tu colección`,
    },
    filterByStatus: "Estado",
    allStatuses: "Todos",
    filterByCopy: "Copias",
    allCopyStates: "Con y sin copia",
    withCopy: "Con copia",
    withoutCopy: "Sin copia",
    statusEmptyGroup: "Ningún juego marcado como {status}.",
    showAll: "Mostrar todos",
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
    sort: {
      label: "Ordenar por",
      recentlyUpdated: "Actualizado recientemente",
      ratingDesc: "Tu valoración (mayor a menor)",
      titleAsc: "Título A–Z",
      releaseYear: "Año de lanzamiento (más reciente)",
    },
  },
  account: {
    switcher: {
      label: "Cuenta simulada",
      change: "Cambiar de cuenta",
      current: "Sesión de {alias} (simulada)",
    },
    banner: "Cuenta simulada — esta es una demo controlada, no una cuenta de usuario real.",
    list: {
      heading: "Elige una cuenta simulada",
      intro: "Cada cuenta tiene su propia colección y valoraciones precargadas.",
    },
  },
  register: {
    heading: "Crear una cuenta simulada",
    intro:
      "Crea una cuenta funcional dentro de la demo controlada. No es una cuenta pública de producción.",
    username: "Usuario",
    password: "Contraseña",
    passwordHint:
      "Al menos 8 caracteres. Evita contraseñas habituales, que sean solo números o que se parezcan a tu usuario. Se admite cualquier carácter, incluidos espacios y símbolos.",
    confirmPassword: "Confirmar contraseña",
    submit: "Crear cuenta simulada",
    pending: "Creando…",
    haveAccount: "¿Ya tienes una cuenta? Inicia sesión",
    errorDuplicate: "Ese usuario ya existe. Prueba con otro.",
    errorWeakPassword: "Elige una contraseña más segura e inténtalo de nuevo.",
    weakPasswordIntro: "La contraseña no cumple los requisitos:",
    errorGeneric: "No se pudo crear la cuenta. Inténtalo de nuevo.",
    errorRateLimited: "Demasiados intentos. Espera un minuto e inténtalo de nuevo.",
  },
  home: {
    valueProposition:
      "Catálogo de videojuegos personal, controlado y reproducible, con recomendaciones explicables.",
    sampleHeading: "Una muestra del catálogo",
    newReleases: {
      heading: "Novedades",
      explainer: "Juegos del corpus gobernado lanzados recientemente.",
    },
    signedIn: {
      greeting: "Hola de nuevo, {alias}",
      continueHeading: "Retoma donde lo dejaste",
      recommendationsCta: "Ver tus recomendaciones por género",
    },
    loggedOut: {
      secondaryCta: "Explorar el catálogo",
      registerCta: "Crear una cuenta simulada",
    },
  },
  theme: {
    toggle: {
      label: "Tema",
      dark: "Oscuro",
      light: "Claro",
      switchToDark: "Cambiar al tema oscuro",
      switchToLight: "Cambiar al tema claro",
    },
  },
  common: {
    retry: "Reintentar",
    showMore: "Mostrar más",
    showLess: "Mostrar menos",
    coverMissing: "Carátula no disponible",
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
