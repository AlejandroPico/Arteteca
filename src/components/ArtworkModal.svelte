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

  marked.setOptions({ gfm: true, breaks: false });

  $: sections = detail?.secciones ?? [];
  $: activeSection = sections.find((section) => section.id === activeTab) ?? sections[0];
  $: html = activeSection
    ? DOMPurify.sanitize(marked.parse(activeSection.contenido) as string, {
        ADD_ATTR: ['target', 'rel'],
      })
    : '';

  async function fetchDetail() {
    loading = true;
    error = '';
    detail = null;
    imageFailed = false;
    try {
      detail = await loadArtwork(obra.id);
      activeTab = detail.secciones[0]?.id ?? '';
    } catch (reason) {
      error = reason instanceof Error ? reason.message : 'No se pudo abrir la obra.';
    } finally {
      loading = false;
    }
  }

  function close() {
    cerrar();
  }

  function keydown(event: KeyboardEvent) {
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
      <button type="button" onclick={() => (immersive = !immersive)} title={immersive ? 'Volver a la ficha' : 'Ver obra a pantalla completa'}>
        {#if immersive}<Minimize2 size={19} />{:else}<Maximize2 size={19} />{/if}
      </button>
      <button type="button" onclick={close} title="Cerrar"><X size={21} /></button>
    </div>

    <figure class="obra-modal__image" style={`--obra-color: ${obra.color}`}>
      {#if imageFailed}
        <span class="obra-modal__image-fallback">
          <ImageOff size={42} strokeWidth={1.25} />
          La reproducción no ha podido cargarse.
        </span>
      {:else}
        <img
          src={detail?.imagen.src ?? obra.imagen.src}
          alt={obra.imagen.alt}
          style={`object-position: ${obra.imagen.foco ?? 'center'}`}
          onerror={() => (imageFailed = true)}
        />
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
          {#if obra.localizacion}<span><MapPin size={15} /> {obra.localizacion}</span>{/if}
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
