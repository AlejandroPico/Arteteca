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
  import type { Catalogo, ObraResumen, OrdenCatalogo, Tema } from './lib/types';

  const BATCH_SIZE = 18;
  let catalog: Catalogo | null = null;
  let orderedWorks: ObraResumen[] = [];
  let loading = true;
  let error = '';
  let query = '';
  let selectedType = 'Todos';
  let selectedPeriod = 'Todos';
  let selectedArtist = 'Todos';
  let order: OrdenCatalogo = 'azar';
  let limit = BATCH_SIZE;
  let activeArtwork: ObraResumen | null = null;
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
  let sentinel: HTMLElement;
  let introVisible = true;
  let introLeaving = false;

  function applyTheme(next: Tema) {
    theme = next;
    localStorage.setItem('arteteca-tema', next);
    document.documentElement.dataset.theme = next;
  }

  function cycleTheme() {
    const themes: Tema[] = ['auto', 'claro', 'oscuro'];
    applyTheme(themes[(themes.indexOf(theme) + 1) % themes.length]);
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
    selectedType = 'Todos';
    selectedPeriod = 'Todos';
    selectedArtist = 'Todos';
    filterQuery = '';
    limit = BATCH_SIZE;
  }

  function selectFilter(value: string) {
    if (filterFacet === 'tipo') {
      selectedType = value;
    } else if (filterFacet === 'periodo') {
      selectedPeriod = value;
    } else {
      selectedArtist = value;
    }
    limit = BATCH_SIZE;
  }

  function filterOptionCount(facet: FilterFacet, value: string) {
    return (catalog?.obras ?? []).filter((work) => {
      if (facet === 'tipo' && selectedPeriod !== 'Todos' && work.periodo !== selectedPeriod) return false;
      if (facet === 'tipo' && selectedArtist !== 'Todos' && work.autor !== selectedArtist) return false;
      if (facet === 'periodo' && selectedType !== 'Todos' && work.tipo !== selectedType) return false;
      if (facet === 'periodo' && selectedArtist !== 'Todos' && work.autor !== selectedArtist) return false;
      if (facet === 'artista' && selectedType !== 'Todos' && work.tipo !== selectedType) return false;
      if (facet === 'artista' && selectedPeriod !== 'Todos' && work.periodo !== selectedPeriod) return false;
      if (value === 'Todos') return true;
      if (facet === 'tipo') return work.tipo === value;
      if (facet === 'periodo') return work.periodo === value;
      return work.autor === value;
    }).length;
  }

  function openArtwork(work: ObraResumen) {
    activeArtwork = work;
    history.replaceState(null, '', `${location.pathname}${location.search}#obra=${work.id}`);
  }

  function closeArtwork() {
    activeArtwork = null;
    history.replaceState(null, '', `${location.pathname}${location.search}`);
  }

  function moveArtwork(direction: -1 | 1) {
    if (!activeArtwork || filteredWorks.length < 2) return;
    const current = filteredWorks.findIndex((work) => work.id === activeArtwork?.id);
    const next = (current + direction + filteredWorks.length) % filteredWorks.length;
    openArtwork(filteredWorks[next]);
  }

  function updateHashArtwork() {
    const id = new URLSearchParams(location.hash.replace(/^#/, '')).get('obra');
    activeArtwork = id ? catalog?.obras.find((work) => work.id === id) ?? null : null;
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
      if (selectedType !== 'Todos' && work.tipo !== selectedType) return false;
      if (selectedPeriod !== 'Todos' && work.periodo !== selectedPeriod) return false;
      if (selectedArtist !== 'Todos' && work.autor !== selectedArtist) return false;
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
  $: activeFilters =
    Number(selectedType !== 'Todos') +
    Number(selectedPeriod !== 'Todos') +
    Number(selectedArtist !== 'Todos');
  $: normalizedFilterQuery = normalizeForSearch(filterQuery);
  $: currentFilterOptions =
    (filterFacet === 'tipo' ? catalog?.tipos : filterFacet === 'periodo' ? catalog?.periodos : catalog?.artistas) ?? [];
  $: visibleFilterOptions = currentFilterOptions.filter((option) =>
    normalizedFilterQuery ? normalizeForSearch(option).includes(normalizedFilterQuery) : true,
  );
  $: selectedFilterValue =
    filterFacet === 'tipo' ? selectedType : filterFacet === 'periodo' ? selectedPeriod : selectedArtist;
  $: filterFacetLabel = filterFacet === 'tipo' ? 'tipo de obra' : filterFacet === 'periodo' ? 'periodo' : 'artista';
  $: filterFacetPlural = filterFacet === 'tipo' ? 'tipos' : filterFacet === 'periodo' ? 'periodos' : 'artistas';

  onMount(() => {
    applyTheme((localStorage.getItem('arteteca-tema') as Tema | null) ?? 'auto');
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
    window.addEventListener('hashchange', updateHashArtwork);

    void (async () => {
      try {
        catalog = await loadCatalog();
        orderedWorks = shuffle(catalog.obras);
        updateHashArtwork();
      } catch (reason) {
        error = reason instanceof Error ? reason.message : 'No se pudo cargar Arteteca.';
      } finally {
        loading = false;
      }
    })();

    return () => {
      window.clearTimeout(introLeaveTimer);
      window.clearTimeout(introRemoveTimer);
      observer.disconnect();
      window.removeEventListener('hashchange', updateHashArtwork);
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

  <nav class:open={mobileMenuOpen} class="site-nav" aria-label="Herramientas de la colección">
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
              {#if selectedType !== 'Todos'}<i>{selectedType}</i>{/if}
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
              {#if selectedPeriod !== 'Todos'}<i>{selectedPeriod}</i>{/if}
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
              {#if selectedArtist !== 'Todos'}<i>{selectedArtist}</i>{/if}
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

          <div class="filter-browser__list" role="listbox" aria-label={`Filtro por ${filterFacetLabel}`}>
            {#if !normalizedFilterQuery}
              <button
                class:active={selectedFilterValue === 'Todos'}
                type="button"
                role="option"
                aria-selected={selectedFilterValue === 'Todos'}
                onclick={() => selectFilter('Todos')}
              >
                <span>{selectedFilterValue === 'Todos' ? 'Toda la colección' : `Todos los ${filterFacetPlural}`}</span>
                <strong>{filterOptionCount(filterFacet, 'Todos')}</strong>
                {#if selectedFilterValue === 'Todos'}<Check size={15} />{/if}
              </button>
            {/if}

            {#each visibleFilterOptions as option}
              <button
                class:active={selectedFilterValue === option}
                type="button"
                role="option"
                aria-selected={selectedFilterValue === option}
                onclick={() => selectFilter(option)}
              >
                <span>{option}</span>
                <strong>{filterOptionCount(filterFacet, option)}</strong>
                {#if selectedFilterValue === option}<Check size={15} />{/if}
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

    <button class="theme-switch" type="button" onclick={cycleTheme} aria-label={`Tema: ${theme}`} title={`Tema: ${theme}`}>
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
    anterior={filteredWorks.length > 1 ? () => moveArtwork(-1) : undefined}
    siguiente={filteredWorks.length > 1 ? () => moveArtwork(1) : undefined}
    cerrar={closeArtwork}
  />
{/if}

{#if aboutOpen}
  <AboutModal cerrar={() => (aboutOpen = false)} />
{/if}

{#if inventoryOpen && catalog}
  <InventoryModal {catalog} cerrar={() => (inventoryOpen = false)} />
{/if}
