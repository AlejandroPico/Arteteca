<script lang="ts">
  import { onMount } from 'svelte';
  import {
    ArrowDownAZ,
    Check,
    Dices,
    Filter,
    Info,
    Menu,
    Moon,
    Search,
    SlidersHorizontal,
    Sun,
    X,
  } from '@lucide/svelte';
  import AboutModal from './components/AboutModal.svelte';
  import ArtworkCard from './components/ArtworkCard.svelte';
  import ArtworkModal from './components/ArtworkModal.svelte';
  import InventoryModal from './components/InventoryModal.svelte';
  import { loadCatalog, normalizeForSearch, shuffle } from './lib/catalog';
  import {
    applyThemeToDocument,
    readStoredCoordinates,
    readStoredTheme,
    storeCoordinates,
    storeTheme,
    themePeriodLabel,
    type ThemeCoordinates,
    type ThemePeriod,
  } from './lib/solarTheme';
  import type { Catalogo, ObraResumen, OrdenCatalogo, Tema } from './lib/types';

  const BATCH_SIZE = 18;
  let catalog: Catalogo | null = null;
  let orderedWorks: ObraResumen[] = [];
  let loading = true;
  let error = '';
  let query = '';
  let selectedTypes: string[] = [];
  let selectedPeriods: string[] = [];
  let selectedArtists: string[] = [];
  let order: OrdenCatalogo = 'azar';
  let limit = BATCH_SIZE;
  let activeArtwork: ObraResumen | null = null;
  let artworkImmersive = false;
  let filtersOpen = false;
  type FilterFacet = 'tipo' | 'periodo' | 'artista';
  let filterFacet: FilterFacet = 'tipo';
  let filterQuery = '';
  let orderOpen = false;
  let searchOpen = false;
  let aboutOpen = false;
  let inventoryOpen = false;
  let mobileMenuOpen = false;
  let theme: Tema = 'auto';
  let resolvedTheme: ThemePeriod = 'afternoon';
  let themeCoordinates: ThemeCoordinates | null = null;
  let themeTimer = 0;
  let geolocationRequested = false;
  let sentinel: HTMLElement;
  let introVisible = true;
  let introLeaving = false;

  function refreshTheme() {
    resolvedTheme = applyThemeToDocument(theme, new Date(), themeCoordinates).period;
  }

  function requestThemeCoordinates() {
    if (theme !== 'auto' || geolocationRequested || !('geolocation' in navigator)) return;
    geolocationRequested = true;
    navigator.geolocation.getCurrentPosition(
      (position) => {
        themeCoordinates = storeCoordinates({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        });
        refreshTheme();
      },
      () => refreshTheme(),
      { enableHighAccuracy: false, maximumAge: 21_600_000, timeout: 8_000 },
    );
  }

  function applyTheme(next: Tema, persist = true) {
    theme = next;
    if (persist) storeTheme(next);
    refreshTheme();
    if (next === 'auto') requestThemeCoordinates();
  }

  function cycleTheme() {
    const themes: Tema[] = ['auto', 'claro', 'oscuro'];
    applyTheme(themes[(themes.indexOf(theme) + 1) % themes.length]);
  }

  function themeDescription(mode: Tema, period: ThemePeriod): string {
    if (mode === 'auto') return `automático · ${themePeriodLabel(period)}`;
    return mode;
  }

  function reshuffle() {
    orderedWorks = shuffle(catalog?.obras ?? []);
    order = 'azar';
    limit = BATCH_SIZE;
  }

  function setOrder(next: OrdenCatalogo) {
    order = next;
    orderOpen = false;
    limit = BATCH_SIZE;
    if (next === 'azar') reshuffle();
  }

  function resetFilters() {
    selectedTypes = [];
    selectedPeriods = [];
    selectedArtists = [];
    filterQuery = '';
    limit = BATCH_SIZE;
  }

  function setFacetSelection(facet: FilterFacet, values: string[]) {
    if (facet === 'tipo') selectedTypes = values;
    else if (facet === 'periodo') selectedPeriods = values;
    else selectedArtists = values;
  }

  function selectFilter(value: string) {
    if (value === 'Todos') {
      setFacetSelection(filterFacet, []);
      limit = BATCH_SIZE;
      return;
    }

    const next = selectedFilterValues.includes(value)
      ? selectedFilterValues.filter((selected) => selected !== value)
      : [...selectedFilterValues, value];
    setFacetSelection(filterFacet, next);
    limit = BATCH_SIZE;
  }

  function filterOptionCount(facet: FilterFacet, value: string) {
    return (catalog?.obras ?? []).filter((work) => {
      if (facet !== 'tipo' && selectedTypes.length && !selectedTypes.includes(work.tipo)) return false;
      if (facet !== 'periodo' && selectedPeriods.length && !selectedPeriods.includes(work.periodo)) return false;
      if (facet !== 'artista' && selectedArtists.length && !selectedArtists.includes(work.autor)) return false;
      if (value === 'Todos') return true;
      if (facet === 'tipo') return work.tipo === value;
      if (facet === 'periodo') return work.periodo === value;
      return work.autor === value;
    }).length;
  }

  type ArtworkHistoryLayer = 'mosaic' | 'artwork' | 'viewer';

  interface ArtworkHistoryState {
    artetecaLayer?: ArtworkHistoryLayer;
    artworkId?: string;
  }

  function baseUrl() {
    return `${location.pathname}${location.search}`;
  }

  function artworkUrl(id: string, viewer = false) {
    const params = new URLSearchParams({ obra: id });
    if (viewer) params.set('visor', '1');
    return `${baseUrl()}#${params.toString()}`;
  }

  function openArtwork(work: ObraResumen) {
    activeArtwork = work;
    artworkImmersive = false;
    history.pushState(
      { artetecaLayer: 'artwork', artworkId: work.id } satisfies ArtworkHistoryState,
      '',
      artworkUrl(work.id),
    );
  }

  function closeArtwork() {
    const layer = (history.state as ArtworkHistoryState | null)?.artetecaLayer;
    if (layer === 'viewer') {
      history.go(-2);
      return;
    }
    if (layer === 'artwork') {
      history.back();
      return;
    }
    activeArtwork = null;
    artworkImmersive = false;
    history.replaceState({ artetecaLayer: 'mosaic' } satisfies ArtworkHistoryState, '', baseUrl());
  }

  function changeArtworkViewer(next: boolean) {
    if (!activeArtwork || next === artworkImmersive) return;
    if (next) {
      artworkImmersive = true;
      history.pushState(
        { artetecaLayer: 'viewer', artworkId: activeArtwork.id } satisfies ArtworkHistoryState,
        '',
        artworkUrl(activeArtwork.id, true),
      );
      return;
    }

    if ((history.state as ArtworkHistoryState | null)?.artetecaLayer === 'viewer') {
      history.back();
      return;
    }
    artworkImmersive = false;
    history.replaceState(
      { artetecaLayer: 'artwork', artworkId: activeArtwork.id } satisfies ArtworkHistoryState,
      '',
      artworkUrl(activeArtwork.id),
    );
  }

  function moveArtwork(direction: -1 | 1) {
    if (!activeArtwork || filteredWorks.length < 2) return;
    const current = filteredWorks.findIndex((work) => work.id === activeArtwork?.id);
    const next = (current + direction + filteredWorks.length) % filteredWorks.length;
    const work = filteredWorks[next];
    activeArtwork = work;
    artworkImmersive = false;
    history.replaceState(
      { artetecaLayer: 'artwork', artworkId: work.id } satisfies ArtworkHistoryState,
      '',
      artworkUrl(work.id),
    );
  }

  function updateArtworkRoute() {
    const params = new URLSearchParams(location.hash.replace(/^#/, ''));
    const id = params.get('obra');
    activeArtwork = id ? catalog?.obras.find((work) => work.id === id) ?? null : null;
    artworkImmersive = Boolean(activeArtwork && params.get('visor') === '1');
  }

  function prepareInitialArtworkHistory() {
    const params = new URLSearchParams(location.hash.replace(/^#/, ''));
    const id = params.get('obra');
    const viewer = Boolean(id && params.get('visor') === '1');
    history.replaceState({ artetecaLayer: 'mosaic' } satisfies ArtworkHistoryState, '', baseUrl());
    if (!id) return;

    history.pushState(
      { artetecaLayer: 'artwork', artworkId: id } satisfies ArtworkHistoryState,
      '',
      artworkUrl(id),
    );
    if (viewer) {
      history.pushState(
        { artetecaLayer: 'viewer', artworkId: id } satisfies ArtworkHistoryState,
        '',
        artworkUrl(id, true),
      );
    }
  }

  function closeHeaderPanels() {
    filtersOpen = false;
    orderOpen = false;
  }

  function toggleSearch() {
    searchOpen = !searchOpen;
    closeHeaderPanels();
    if (searchOpen) {
      requestAnimationFrame(() => document.querySelector<HTMLInputElement>('#site-search')?.focus());
    }
  }

  $: normalizedQuery = normalizeForSearch(query);
  $: filteredWorks = orderedWorks
    .filter((work) => {
      if (selectedTypes.length && !selectedTypes.includes(work.tipo)) return false;
      if (selectedPeriods.length && !selectedPeriods.includes(work.periodo)) return false;
      if (selectedArtists.length && !selectedArtists.includes(work.autor)) return false;
      if (!normalizedQuery) return true;
      const haystack = normalizeForSearch(
        [work.titulo, work.tituloOriginal, work.autor, work.fecha, work.tipo, work.periodo, ...work.etiquetas]
          .filter(Boolean)
          .join(' '),
      );
      return haystack.includes(normalizedQuery);
    })
    .sort((a, b) => {
      if (order === 'titulo') return a.titulo.localeCompare(b.titulo, 'es');
      if (order === 'antiguas') return (a.fechaOrden ?? 0) - (b.fechaOrden ?? 0);
      if (order === 'recientes') return (b.fechaOrden ?? 0) - (a.fechaOrden ?? 0);
      return 0;
    });
  $: visibleWorks = filteredWorks.slice(0, limit);
  $: activeFilters = selectedTypes.length + selectedPeriods.length + selectedArtists.length;
  $: normalizedFilterQuery = normalizeForSearch(filterQuery);
  $: currentFilterOptions =
    (filterFacet === 'tipo' ? catalog?.tipos : filterFacet === 'periodo' ? catalog?.periodos : catalog?.artistas) ?? [];
  $: visibleFilterOptions = currentFilterOptions.filter((option) =>
    normalizedFilterQuery ? normalizeForSearch(option).includes(normalizedFilterQuery) : true,
  );
  $: selectedFilterValues =
    filterFacet === 'tipo' ? selectedTypes : filterFacet === 'periodo' ? selectedPeriods : selectedArtists;
  $: filterFacetLabel = filterFacet === 'tipo' ? 'tipo de obra' : filterFacet === 'periodo' ? 'periodo' : 'artista';
  $: filterFacetPlural = filterFacet === 'tipo' ? 'tipos' : filterFacet === 'periodo' ? 'periodos' : 'artistas';

  onMount(() => {
    prepareInitialArtworkHistory();
    theme = readStoredTheme();
    themeCoordinates = readStoredCoordinates();
    applyTheme(theme, false);
    themeTimer = window.setInterval(refreshTheme, 60_000);
    const refreshVisibleTheme = () => {
      if (document.visibilityState === 'visible') refreshTheme();
    };
    document.addEventListener('visibilitychange', refreshVisibleTheme);
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    let introLeaveTimer = 0;
    let introRemoveTimer = 0;

    if (reducedMotion) {
      introVisible = false;
    } else {
      introLeaveTimer = window.setTimeout(() => (introLeaving = true), 1200);
      introRemoveTimer = window.setTimeout(() => (introVisible = false), 1850);
    }

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting && limit < filteredWorks.length) {
          limit += BATCH_SIZE;
        }
      },
      { rootMargin: '700px 0px' },
    );
    if (sentinel) observer.observe(sentinel);
    window.addEventListener('popstate', updateArtworkRoute);

    void (async () => {
      try {
        catalog = await loadCatalog();
        orderedWorks = shuffle(catalog.obras);
        updateArtworkRoute();
      } catch (reason) {
        error = reason instanceof Error ? reason.message : 'No se pudo cargar Arteteca.';
      } finally {
        loading = false;
      }
    })();

    return () => {
      window.clearTimeout(introLeaveTimer);
      window.clearTimeout(introRemoveTimer);
      window.clearInterval(themeTimer);
      observer.disconnect();
      window.removeEventListener('popstate', updateArtworkRoute);
      document.removeEventListener('visibilitychange', refreshVisibleTheme);
    };
  });
</script>

<svelte:head>
  <meta property="og:title" content="Arteteca — El arte sin pasillos" />
  <meta
    property="og:description"
    content="Pintura, escultura, fotografía, grabado, manuscritos y arte rupestre en una colección abierta."
  />
</svelte:head>

<header class="site-header">
  <a class="brand" href="./" aria-label="Arteteca, inicio">
    <span class="brand__mark">A</span>
    <span class="brand__name">ARTETECA</span>
  </a>

  <nav
    class:open={mobileMenuOpen}
    class:search-open={searchOpen}
    class="site-nav"
    aria-label="Herramientas de la colección"
  >
    <div class:open={searchOpen} class="header-search">
      <input
        id="site-search"
        type="search"
        placeholder="Obra, autor, técnica o época…"
        aria-label="Buscar en la colección"
        bind:value={query}
        oninput={() => (limit = BATCH_SIZE)}
      />
      {#if query && searchOpen}
        <button class="header-search__clear" type="button" aria-label="Borrar búsqueda" onclick={() => (query = '')}>
          <X size={15} />
        </button>
      {/if}
      <button
        class="header-action header-search__trigger"
        class:active={searchOpen || Boolean(query)}
        type="button"
        aria-label={searchOpen ? 'Cerrar búsqueda' : 'Abrir búsqueda'}
        aria-expanded={searchOpen}
        title="Buscar"
        onclick={toggleSearch}
      >
        {#if searchOpen}<X size={18} />{:else}<Search size={18} />{/if}
      </button>
    </div>

    <button class="header-action header-action--shuffle" type="button" title="Redescubrir la colección" onclick={reshuffle}>
      <Dices size={18} />
      <span>Redescubrir</span>
    </button>

    <div class="header-control">
      <button
        class:active={activeFilters > 0 || filtersOpen}
        class="header-action"
        type="button"
        aria-expanded={filtersOpen}
        title="Filtros"
        onclick={() => {
          filtersOpen = !filtersOpen;
          orderOpen = false;
          searchOpen = false;
          if (filtersOpen) filterQuery = '';
        }}
      >
        <SlidersHorizontal size={18} />
        <span>Filtros</span>
        {#if activeFilters}<b>{activeFilters}</b>{/if}
      </button>

      {#if filtersOpen}
        <div class="header-popover header-popover--filters" role="dialog" aria-label="Filtrar la colección">
          <header class="filter-browser__header">
            <div>
              <span class="eyebrow">Explorar el catálogo</span>
              <h2>Filtrar la colección</h2>
            </div>
            <button
              class="filter-browser__close"
              type="button"
              aria-label="Cerrar filtros"
              onclick={() => (filtersOpen = false)}
            >
              <X size={18} />
            </button>
          </header>

          <nav class="filter-browser__facets" aria-label="Categorías de filtro">
            <button
              class:active={filterFacet === 'tipo'}
              type="button"
              onclick={() => {
                filterFacet = 'tipo';
                filterQuery = '';
              }}
            >
              <span>Tipo</span>
              <small>{catalog?.tipos.length ?? 0}</small>
              {#if selectedTypes.length}<i>{selectedTypes.length === 1 ? selectedTypes[0] : `${selectedTypes.length} seleccionados`}</i>{/if}
            </button>
            <button
              class:active={filterFacet === 'periodo'}
              type="button"
              onclick={() => {
                filterFacet = 'periodo';
                filterQuery = '';
              }}
            >
              <span>Periodo</span>
              <small>{catalog?.periodos.length ?? 0}</small>
              {#if selectedPeriods.length}<i>{selectedPeriods.length === 1 ? selectedPeriods[0] : `${selectedPeriods.length} seleccionados`}</i>{/if}
            </button>
            <button
              class:active={filterFacet === 'artista'}
              type="button"
              onclick={() => {
                filterFacet = 'artista';
                filterQuery = '';
              }}
            >
              <span>Artista</span>
              <small>{catalog?.artistas.length ?? 0}</small>
              {#if selectedArtists.length}<i>{selectedArtists.length === 1 ? selectedArtists[0] : `${selectedArtists.length} seleccionados`}</i>{/if}
            </button>
          </nav>

          <label class="filter-browser__search">
            <Search size={16} />
            <input
              type="search"
              placeholder={`Buscar ${filterFacetLabel}…`}
              bind:value={filterQuery}
            />
            {#if filterQuery}
              <button type="button" aria-label="Borrar búsqueda de filtros" onclick={() => (filterQuery = '')}>
                <X size={14} />
              </button>
            {/if}
          </label>

          <div
            class="filter-browser__list"
            role="listbox"
            aria-label={`Filtro por ${filterFacetLabel}`}
            aria-multiselectable="true"
          >
            {#if !normalizedFilterQuery}
              <button
                class:active={selectedFilterValues.length === 0}
                type="button"
                role="option"
                aria-selected={selectedFilterValues.length === 0}
                onclick={() => selectFilter('Todos')}
              >
                <span>{selectedFilterValues.length === 0 ? 'Toda la colección' : `Todos los ${filterFacetPlural}`}</span>
                <strong>{filterOptionCount(filterFacet, 'Todos')}</strong>
                {#if selectedFilterValues.length === 0}<Check size={15} />{/if}
              </button>
            {/if}

            {#each visibleFilterOptions as option}
              <button
                class:active={selectedFilterValues.includes(option)}
                type="button"
                role="option"
                aria-selected={selectedFilterValues.includes(option)}
                onclick={() => selectFilter(option)}
              >
                <span>{option}</span>
                <strong>{filterOptionCount(filterFacet, option)}</strong>
                {#if selectedFilterValues.includes(option)}<Check size={15} />{/if}
              </button>
            {:else}
              <p class="filter-browser__empty">No hay coincidencias para «{filterQuery}».</p>
            {/each}
          </div>

          <footer class="filter-browser__footer">
            <div>
              <strong>{filteredWorks.length}</strong>
              <span>{filteredWorks.length === 1 ? 'obra visible' : 'obras visibles'}</span>
            </div>
            {#if activeFilters}
              <button class="clear-filters" type="button" onclick={resetFilters}>Limpiar {activeFilters}</button>
            {/if}
            <button class="filter-browser__apply" type="button" onclick={() => (filtersOpen = false)}>
              Ver colección
            </button>
          </footer>
        </div>
      {/if}
    </div>

    <div class="header-control">
      <button
        class:active={orderOpen || order !== 'azar'}
        class="header-action"
        type="button"
        aria-expanded={orderOpen}
        title="Ordenar"
        onclick={() => {
          orderOpen = !orderOpen;
          filtersOpen = false;
          searchOpen = false;
        }}
      >
        <ArrowDownAZ size={18} />
        <span>Orden</span>
      </button>

      {#if orderOpen}
        <div class="header-popover header-popover--order" role="menu" aria-label="Orden de las obras">
          {#each [
            ['azar', 'Al azar'],
            ['antiguas', 'Más antiguas'],
            ['recientes', 'Más recientes'],
            ['titulo', 'Título A–Z'],
          ] as option}
            <button
              class:active={order === option[0]}
              type="button"
              role="menuitem"
              onclick={() => setOrder(option[0] as OrdenCatalogo)}
            >
              <span>{option[1]}</span>
              {#if order === option[0]}<Check size={15} />{/if}
            </button>
          {/each}
        </div>
      {/if}
    </div>

    <button
      class="header-action"
      type="button"
      title="Acerca de Arteteca"
      onclick={(event) => {
        if (event.altKey) {
          inventoryOpen = true;
        } else {
          aboutOpen = true;
        }
        mobileMenuOpen = false;
        closeHeaderPanels();
      }}
    >
      <Info size={18} />
      <span>Acerca de</span>
    </button>

    <button
      class="theme-switch"
      type="button"
      data-period={resolvedTheme}
      onclick={cycleTheme}
      aria-label={`Tema: ${themeDescription(theme, resolvedTheme)}`}
      title={`Tema: ${themeDescription(theme, resolvedTheme)}`}
    >
      {#if theme === 'claro'}
        <Sun size={18} />
      {:else if theme === 'oscuro'}
        <Moon size={18} />
      {:else}
        <span class="theme-switch__auto"><Sun size={15} /><Moon size={15} /></span>
      {/if}
    </button>
  </nav>

  <button
    class="mobile-menu"
    type="button"
    aria-label="Abrir menú"
    aria-expanded={mobileMenuOpen}
    onclick={() => (mobileMenuOpen = !mobileMenuOpen)}
  >
    {#if mobileMenuOpen}<X size={22} />{:else}<Menu size={22} />{/if}
  </button>
</header>

{#if introVisible}
  <section class:intro--leaving={introLeaving} class="intro" aria-labelledby="intro-title">
    <div class="intro__kicker"><span></span> Colección abierta de arte universal</div>
    <h1 id="intro-title">
      El arte,<br />
      <em>sin pasillos.</em>
    </h1>
    <p>
      Una exposición viva donde conviven lienzos, piedra, papel, muros y miradas.
    </p>
  </section>
{/if}

<main>
  <section class="collection" id="coleccion" aria-label="Colección de obras">
    {#if loading}
      <div class="mosaic mosaic--loading" aria-label="Cargando colección">
        {#each Array(10) as _, index}
          <div class:wide={index % 4 === 0} class="skeleton-card"><span></span><i></i><i></i></div>
        {/each}
      </div>
    {:else if error}
      <div class="empty-state">
        <Filter size={32} strokeWidth={1.25} />
        <h3>No hemos podido abrir la colección</h3>
        <p>{error}</p>
        <button type="button" onclick={() => location.reload()}>Intentarlo de nuevo</button>
      </div>
    {:else if visibleWorks.length}
      <div class="mosaic">
        {#each visibleWorks as work (work.id)}
          <ArtworkCard obra={work} abrir={openArtwork} />
        {/each}
      </div>
    {:else}
      <div class="empty-state">
        <Search size={32} strokeWidth={1.25} />
        <h3>No aparece ninguna obra</h3>
        <p>Prueba con otra palabra o retira alguno de los filtros.</p>
        <button type="button" onclick={resetFilters}>Ver toda la colección</button>
      </div>
    {/if}

    <div class="load-sentinel" bind:this={sentinel}>
      {#if visibleWorks.length < filteredWorks.length}
        <span>Preparando más obras…</span>
      {/if}
    </div>
  </section>
</main>

<footer class="site-footer">
  <a class="brand brand--footer" href="./"><span class="brand__mark">A</span><span class="brand__name">ARTETECA</span></a>
  <p>Una colección abierta, construida obra a obra.</p>
  <span>{catalog?.total ?? '—'} obras catalogadas</span>
</footer>

{#if activeArtwork}
  <ArtworkModal
    obra={activeArtwork}
    immersive={artworkImmersive}
    anterior={filteredWorks.length > 1 ? () => moveArtwork(-1) : undefined}
    siguiente={filteredWorks.length > 1 ? () => moveArtwork(1) : undefined}
    cambiarVisor={changeArtworkViewer}
    cerrar={closeArtwork}
  />
{/if}

{#if aboutOpen}
  <AboutModal cerrar={() => (aboutOpen = false)} />
{/if}

{#if inventoryOpen && catalog}
  <InventoryModal {catalog} cerrar={() => (inventoryOpen = false)} />
{/if}
