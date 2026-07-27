<script lang="ts">
  import { ImageOff, MoveUpRight } from '@lucide/svelte';
  import type { ObraResumen } from '../lib/types';
  import { masonryItem } from '../lib/masonry';

  export let obra: ObraResumen;
  export let abrir: (obra: ObraResumen) => void;

  let imageFailed = false;
  $: ratio = obra.proporcion[0] / obra.proporcion[1];
  $: wide = ratio >= 1.55;
</script>

<article
  class:obra-grid-item--wide={wide}
  class="obra-grid-item"
  use:masonryItem
  style={`--obra-color: ${obra.color}`}
>
  <button class="obra-card" type="button" onclick={() => abrir(obra)} aria-label={`Abrir ${obra.titulo}`}>
    <span class="obra-card__visual" style={`aspect-ratio: ${obra.proporcion[0]} / ${obra.proporcion[1]}`}>
      {#if imageFailed}
        <span class="obra-card__fallback">
          <ImageOff size={28} strokeWidth={1.5} />
          <small>Imagen no disponible</small>
        </span>
      {:else}
        <img
          src={obra.imagen.src}
          alt={obra.imagen.alt}
          loading="lazy"
          decoding="async"
          style={`object-position: ${obra.imagen.foco ?? 'center'}`}
          onerror={() => (imageFailed = true)}
        />
      {/if}
      <span class="obra-card__shade"></span>
      <span class="obra-card__type">{obra.tipo}</span>
      <span class="obra-card__arrow"><MoveUpRight size={18} /></span>
    </span>
    <span class="obra-card__caption">
      <span>
        <strong>{obra.titulo}</strong>
        <em>{obra.autor}</em>
      </span>
      <span class="obra-card__date">{obra.fecha}</span>
    </span>
  </button>
</article>
