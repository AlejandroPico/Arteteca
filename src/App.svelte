<script lang="ts">
  import { onMount } from 'svelte';
  import {
    ArrowDown,
    Check,
    ChevronDown,
    Dices,
    Filter,
    Menu,
    Moon,
    Search,
    SlidersHorizontal,
    Sparkles,
    Sun,
    X,
  } from '@lucide/svelte';
  import ArtworkCard from './components/ArtworkCard.svelte';
  import ArtworkModal from './components/ArtworkModal.svelte';
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
  let order: OrdenCatalogo = 'azar';
  let limit = BATCH_SIZE;
  let activeArtwork: ObraResumen | null = null;
  let filtersOpen = false;
  let mobileMenuOpen = false;
  let theme: Tema = 'auto';
  let sentinel: HTMLElement;

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
    limit = BATCH_SIZE;
    if (next === 'azar') reshuffle();
  }

  function resetFilters() {
    query = '';
    selectedType = 'Todos';
    selectedPeriod = 'Todos';
    limit = BATCH_SIZE;
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

  $: normalizedQuery = normalizeForSearch(query);
  $: filteredWorks = orderedWorks
    .filter((work) => {
      if (selectedType !== 'Todos' && work.tipo !== selectedType) return false;
      if (selectedPeriod !== 'Todos' && work.periodo !== selectedPeriod) return false;
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
  $: activeFilters = Number(selectedType !== 'Todos') + Number(selectedPeriod !== 'Todos');

  onMount(() => {
    applyTheme((localStorage.getItem('arteteca-tema') as Tema | null) ?? 'auto');
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

  <nav class:open={mobileMenuOpen} class="site-nav" aria-label="Navegación principal">
    <a href="#coleccion" onclick={() => (mobileMenuOpen = false)}>Colección</a>
    <a href="#acerca" onclick={() => (mobileMenuOpen = false)}>Acerca de</a>
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

<main>
  <section class="hero" aria-labelledby="hero-title">
    <div class="hero__kicker"><span></span> Colección abierta de arte universal</div>
    <h1 id="hero-title">
      El arte,<br />
      <em>sin pasillos.</em>
    </h1>
    <p>
      Una exposición viva donde conviven lienzos, piedra, papel, muros y miradas.
      Entra por cualquier obra; no existe un recorrido obligatorio.
    </p>
    <a class="hero__down" href="#coleccion">
      Explorar la colección <ArrowDown size={17} />
    </a>
    <div class="hero__ornament" aria-hidden="true">
      <span></span><span></span><span></span>
    </div>
  </section>

  <section class="collection" id="coleccion" aria-labelledby="collection-title">
    <div class="collection__heading">
      <div>
        <span class="eyebrow">La colección</span>
        <h2 id="collection-title">Un mosaico que nunca se repite</h2>
      </div>
      <button class="shuffle-button" type="button" onclick={reshuffle}>
        <Dices size={18} /> Redescubrir
      </button>
    </div>

    <div class="toolbar">
      <label class="search-box">
        <Search size={19} />
        <input
          type="search"
          placeholder="Busca una obra, autor, técnica o época…"
          bind:value={query}
          oninput={() => (limit = BATCH_SIZE)}
        />
        {#if query}
          <button type="button" aria-label="Borrar búsqueda" onclick={() => (query = '')}><X size={16} /></button>
        {/if}
      </label>

      <button
        class:active={activeFilters > 0}
        class="filter-button"
        type="button"
        onclick={() => (filtersOpen = !filtersOpen)}
        aria-expanded={filtersOpen}
      >
        <SlidersHorizontal size={18} />
        Filtros
        {#if activeFilters}<span>{activeFilters}</span>{/if}
        <ChevronDown class={filtersOpen ? 'rotated' : ''} size={15} />
      </button>

      <label class="order-select">
        <span>Orden</span>
        <select value={order} onchange={(event) => setOrder(event.currentTarget.value as OrdenCatalogo)}>
          <option value="azar">Al azar</option>
          <option value="antiguas">Más antiguas</option>
          <option value="recientes">Más recientes</option>
          <option value="titulo">Título A–Z</option>
        </select>
        <ChevronDown size={14} />
      </label>
    </div>

    {#if filtersOpen}
      <div class="filter-panel">
        <fieldset>
          <legend>Tipo de obra</legend>
          <div class="filter-options">
            {#each ['Todos', ...(catalog?.tipos ?? [])] as type}
              <button
                class:active={selectedType === type}
                type="button"
                onclick={() => {
                  selectedType = type;
                  limit = BATCH_SIZE;
                }}
              >
                {#if selectedType === type}<Check size={14} />{/if}{type}
              </button>
            {/each}
          </div>
        </fieldset>
        <fieldset>
          <legend>Periodo</legend>
          <div class="filter-options">
            {#each ['Todos', ...(catalog?.periodos ?? [])] as period}
              <button
                class:active={selectedPeriod === period}
                type="button"
                onclick={() => {
                  selectedPeriod = period;
                  limit = BATCH_SIZE;
                }}
              >
                {#if selectedPeriod === period}<Check size={14} />{/if}{period}
              </button>
            {/each}
          </div>
        </fieldset>
        {#if activeFilters}
          <button class="clear-filters" type="button" onclick={resetFilters}>Limpiar filtros</button>
        {/if}
      </div>
    {/if}

    <div class="result-line" aria-live="polite">
      {#if !loading && catalog}
        <span><strong>{filteredWorks.length}</strong> {filteredWorks.length === 1 ? 'obra' : 'obras'}</span>
        <span class="result-line__rule"></span>
        <span>La disposición cambia en cada visita</span>
      {/if}
    </div>

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
        <span><Sparkles size={15} /> Preparando más obras…</span>
      {:else if filteredWorks.length}
        <span>Has recorrido las {filteredWorks.length} obras disponibles.</span>
      {/if}
    </div>
  </section>

  <section class="manifesto" id="acerca">
    <div class="manifesto__number">A—01</div>
    <div>
      <span class="eyebrow">Sobre Arteteca</span>
      <h2>Una colección sin una única definición de arte.</h2>
    </div>
    <div class="manifesto__copy">
      <p>
        Arteteca nace para reunir objetos capaces de contar algo: una pintura célebre,
        una talla anónima, una imagen documental o una huella trazada sobre roca.
      </p>
      <p>
        Cada ficha crece por archivos independientes. Si una obra no tiene autor conocido,
        esa pestaña sencillamente no existe. La forma de la información se adapta a la obra,
        igual que este mosaico se adapta a sus proporciones.
      </p>
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
