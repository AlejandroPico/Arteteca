<script lang="ts">
  import { onMount } from 'svelte';
  import {
    ArrowUpRight,
    CalendarDays,
    ChevronLeft,
    ChevronRight,
    ImageOff,
    MapPin,
    Maximize2,
    Minimize2,
    X,
  } from '@lucide/svelte';
  import DOMPurify from 'dompurify';
  import { marked } from 'marked';
  import { loadArtwork } from '../lib/catalog';
  import type { ObraDetalle, ObraResumen, SeccionObra } from '../lib/types';

  export let obra: ObraResumen;
  export let anterior: (() => void) | undefined = undefined;
  export let siguiente: (() => void) | undefined = undefined;
  export let cerrar: () => void;

  let detail: ObraDetalle | null = null;
  let loading = true;
  let error = '';
  let activeTab = '';
  let immersive = false;
  let imageFailed = false;
  let displayedImage = obra.imagen.src;
  let highResolutionLoading = false;
  let highResolutionRequest = 0;
  let zoom = 1;
  let panX = 0;
  let panY = 0;
  let dragging = false;
  let viewer: HTMLButtonElement;
  const pointers = new Map<number, { x: number; y: number }>();
  let dragOrigin = { x: 0, y: 0, panX: 0, panY: 0 };
  let pinchOrigin = { distance: 0, zoom: 1, x: 0, y: 0, panX: 0, panY: 0 };

  marked.setOptions({ gfm: true, breaks: false });

  $: sections = detail?.secciones ?? [];
  $: activeSection = sections.find((section) => section.id === activeTab) ?? sections[0];
  $: html = activeSection
    ? DOMPurify.sanitize(marked.parse(activeSection.contenido) as string, {
        ADD_ATTR: ['target', 'rel'],
      })
    : '';

  async function fetchDetail() {
    const requestId = ++highResolutionRequest;
    loading = true;
    error = '';
    detail = null;
    imageFailed = false;
    displayedImage = obra.imagen.src;
    highResolutionLoading = false;
    try {
      const loadedDetail = await loadArtwork(obra.id);
      if (requestId !== highResolutionRequest) return;
      detail = loadedDetail;
      activeTab = detail.secciones[0]?.id ?? '';
      if (immersive) void loadHighResolution();
    } catch (reason) {
      error = reason instanceof Error ? reason.message : 'No se pudo abrir la obra.';
    } finally {
      loading = false;
    }
  }

  function close() {
    cerrar();
  }

  function resetViewer() {
    zoom = 1;
    panX = 0;
    panY = 0;
    pointers.clear();
    dragging = false;
  }

  function loadHighResolution() {
    const source = detail?.imagen.srcAltaResolucion;
    if (!immersive || !source || source === displayedImage) return;

    const requestId = ++highResolutionRequest;
    highResolutionLoading = true;
    const preloader = new Image();
    preloader.onload = () => {
      if (requestId !== highResolutionRequest || !immersive) return;
      displayedImage = source;
      highResolutionLoading = false;
    };
    preloader.onerror = () => {
      if (requestId === highResolutionRequest) highResolutionLoading = false;
    };
    preloader.src = source;
  }

  function setImmersive(next: boolean) {
    immersive = next;
    resetViewer();
    if (next) {
      void loadHighResolution();
    } else {
      highResolutionRequest += 1;
      highResolutionLoading = false;
      displayedImage = detail?.imagen.src ?? obra.imagen.src;
    }
  }

  function zoomAt(nextZoom: number, clientX: number, clientY: number) {
    if (!viewer) return;
    const rect = viewer.getBoundingClientRect();
    const pointX = clientX - (rect.left + rect.width / 2);
    const pointY = clientY - (rect.top + rect.height / 2);
    const clamped = Math.min(8, Math.max(1, nextZoom));
    const ratio = clamped / zoom;

    panX = pointX - (pointX - panX) * ratio;
    panY = pointY - (pointY - panY) * ratio;
    zoom = clamped;

    if (zoom === 1) {
      panX = 0;
      panY = 0;
    }
  }

  function wheel(event: WheelEvent) {
    if (!immersive) return;
    event.preventDefault();
    zoomAt(zoom * Math.exp(-event.deltaY * 0.0015), event.clientX, event.clientY);
  }

  function doubleClick(event: MouseEvent) {
    if (!immersive) {
      setImmersive(true);
      return;
    }
    zoomAt(zoom > 1.05 ? 1 : 2.5, event.clientX, event.clientY);
  }

  function pointerDown(event: PointerEvent) {
    if (!immersive) return;
    viewer.setPointerCapture(event.pointerId);
    pointers.set(event.pointerId, { x: event.clientX, y: event.clientY });
    dragging = true;

    if (pointers.size === 1) {
      dragOrigin = { x: event.clientX, y: event.clientY, panX, panY };
    } else if (pointers.size === 2) {
      const [first, second] = [...pointers.values()];
      pinchOrigin = {
        distance: Math.hypot(second.x - first.x, second.y - first.y),
        zoom,
        x: (first.x + second.x) / 2,
        y: (first.y + second.y) / 2,
        panX,
        panY,
      };
    }
  }

  function pointerMove(event: PointerEvent) {
    if (!immersive || !pointers.has(event.pointerId)) return;
    pointers.set(event.pointerId, { x: event.clientX, y: event.clientY });

    if (pointers.size === 1) {
      panX = dragOrigin.panX + event.clientX - dragOrigin.x;
      panY = dragOrigin.panY + event.clientY - dragOrigin.y;
      return;
    }

    const [first, second] = [...pointers.values()];
    const distance = Math.hypot(second.x - first.x, second.y - first.y);
    const midpointX = (first.x + second.x) / 2;
    const midpointY = (first.y + second.y) / 2;
    const nextZoom = Math.min(8, Math.max(1, pinchOrigin.zoom * (distance / pinchOrigin.distance)));
    const ratio = nextZoom / pinchOrigin.zoom;

    panX = pinchOrigin.panX * ratio + midpointX - pinchOrigin.x;
    panY = pinchOrigin.panY * ratio + midpointY - pinchOrigin.y;
    zoom = nextZoom;
  }

  function pointerUp(event: PointerEvent) {
    pointers.delete(event.pointerId);
    if (viewer?.hasPointerCapture(event.pointerId)) viewer.releasePointerCapture(event.pointerId);

    if (pointers.size === 1) {
      const remaining = [...pointers.values()][0];
      dragOrigin = { x: remaining.x, y: remaining.y, panX, panY };
    } else if (pointers.size === 0) {
      dragging = false;
    }
  }

  function keydown(event: KeyboardEvent) {
    if (event.key === 'Escape' && immersive) {
      setImmersive(false);
      return;
    }
    if (event.key === 'Escape') close();
    if (event.key === 'ArrowLeft' && !immersive) anterior?.();
    if (event.key === 'ArrowRight' && !immersive) siguiente?.();
  }

  onMount(() => {
    const previous = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = previous;
    };
  });

  $: if (obra.id) fetchDetail();
</script>

<svelte:window onkeydown={keydown} />

<div class:obra-modal--immersive={immersive} class="obra-modal" role="dialog" aria-modal="true" aria-label={obra.titulo}>
  <button class="obra-modal__scrim" type="button" aria-label="Cerrar ficha" onclick={close}></button>
  <section class="obra-modal__panel">
    <div class="obra-modal__top-actions">
      <button type="button" onclick={() => setImmersive(!immersive)} title={immersive ? 'Volver a la ficha' : 'Ver obra a pantalla completa'}>
        {#if immersive}<Minimize2 size={19} />{:else}<Maximize2 size={19} />{/if}
      </button>
      <button type="button" onclick={close} title="Cerrar"><X size={21} /></button>
    </div>

    <figure class:dragging class="obra-modal__image" style={`--obra-color: ${obra.color}`}>
      {#if imageFailed}
        <span class="obra-modal__image-fallback">
          <ImageOff size={42} strokeWidth={1.25} />
          La reproducción no ha podido cargarse.
        </span>
      {:else}
        <button
          bind:this={viewer}
          class="obra-modal__image-button"
          type="button"
          aria-label={immersive ? 'Visor ampliable de la obra' : 'Ver obra a pantalla completa'}
          onclick={() => {
            if (!immersive) setImmersive(true);
          }}
          ondblclick={doubleClick}
          onwheel={wheel}
          onpointerdown={pointerDown}
          onpointermove={pointerMove}
          onpointerup={pointerUp}
          onpointercancel={pointerUp}
        >
          <img
            src={displayedImage}
            alt={obra.imagen.alt}
            draggable="false"
            style={`object-position: ${obra.imagen.foco ?? 'center'}; transform: translate3d(${panX}px, ${panY}px, 0) scale(${zoom})`}
            onerror={() => (imageFailed = true)}
          />
        </button>
      {/if}
      {#if immersive}
        {#if highResolutionLoading}
          <p class="obra-modal__resolution-state" aria-live="polite">Cargando reproducción de máxima resolución…</p>
        {/if}
        <p class="obra-modal__viewer-hint">Rueda o pellizca para ampliar · arrastra para recorrer · doble clic para restablecer</p>
      {/if}
      <figcaption>
        <span>{obra.imagen.credito ?? obra.autor}</span>
        <a href={obra.imagen.fuente} target="_blank" rel="noreferrer">
          Fuente y licencia <ArrowUpRight size={13} />
        </a>
      </figcaption>
    </figure>

    <div class="obra-modal__content">
      <header class="obra-modal__heading">
        <span class="eyebrow">{obra.tipo} · {obra.periodo}</span>
        <h2>{obra.titulo}</h2>
        {#if obra.tituloOriginal}<p class="obra-modal__original">{obra.tituloOriginal}</p>{/if}
        <p class="obra-modal__author">{obra.autor}</p>
        <div class="obra-modal__facts">
          <span><CalendarDays size={15} /> {obra.fecha}</span>
          {#if obra.localizacion}
            <span class="obra-modal__location">
              <MapPin size={15} />
              {#if obra.urlLocalizacion}
                <a href={obra.urlLocalizacion} target="_blank" rel="noreferrer">{obra.localizacion}</a>
              {:else}
                {obra.localizacion}
              {/if}
              {#if obra.ciudad}
                <i aria-hidden="true">·</i>
                {#if obra.urlMapa}
                  <a href={obra.urlMapa} target="_blank" rel="noreferrer">{obra.ciudad}</a>
                {:else}
                  {obra.ciudad}
                {/if}
              {/if}
            </span>
          {/if}
        </div>
        <p class="obra-modal__summary">{obra.descripcion}</p>
      </header>

      {#if loading}
        <div class="detail-loading" aria-live="polite">
          <span></span><span></span><span></span>
          <p>Abriendo los archivos de la obra…</p>
        </div>
      {:else if error}
        <p class="detail-error">{error}</p>
      {:else if sections.length}
        <div class="obra-tabs" role="tablist" aria-label="Secciones de la obra">
          {#each sections as section (section.id)}
            <button
              type="button"
              role="tab"
              class:active={section.id === activeSection?.id}
              aria-selected={section.id === activeSection?.id}
              onclick={() => (activeTab = section.id)}
            >
              {section.titulo}
            </button>
          {/each}
        </div>
        <article class="obra-prose" aria-live="polite">
          {@html html}
        </article>
      {:else}
        <p class="detail-empty">Esta obra todavía no tiene secciones documentales.</p>
      {/if}
    </div>

    {#if anterior}
      <button class="obra-modal__nav obra-modal__nav--prev" type="button" onclick={anterior} title="Obra anterior">
        <ChevronLeft size={23} />
      </button>
    {/if}
    {#if siguiente}
      <button class="obra-modal__nav obra-modal__nav--next" type="button" onclick={siguiente} title="Obra siguiente">
        <ChevronRight size={23} />
      </button>
    {/if}
  </section>
</div>
