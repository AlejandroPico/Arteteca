<script lang="ts">
  import { ArrowUpRight, GitFork, X } from '@lucide/svelte';
  import { onMount } from 'svelte';

  export let cerrar: () => void;

  function keydown(event: KeyboardEvent) {
    if (event.key === 'Escape') cerrar();
  }

  onMount(() => {
    const previous = document.body.style.overflow;
    document.body.style.overflow = 'hidden';

    return () => {
      document.body.style.overflow = previous;
    };
  });
</script>

<svelte:window onkeydown={keydown} />

<div class="about-modal" role="dialog" aria-modal="true" aria-labelledby="about-title">
  <button class="about-modal__scrim" type="button" aria-label="Cerrar acerca de Arteteca" onclick={cerrar}></button>

  <section class="about-modal__panel">
    <button class="about-modal__close" type="button" aria-label="Cerrar" title="Cerrar" onclick={cerrar}>
      <X size={21} />
    </button>

    <div class="about-modal__index" aria-hidden="true">A—01</div>

    <div class="about-modal__intro">
      <header class="about-modal__heading">
        <span class="eyebrow">Sobre Arteteca</span>
        <h2 id="about-title">Una colección sin una única definición de arte.</h2>
      </header>

      <nav class="about-modal__links" aria-label="Enlaces del proyecto">
        <a href="https://alejandropico.github.io/Portfolio/" target="_blank" rel="noreferrer">
          <span>
            <small>Conocer al autor</small>
            Porfolio de Alejandro Pico
          </span>
          <ArrowUpRight size={19} />
        </a>
        <a href="https://github.com/AlejandroPico/Arteteca" target="_blank" rel="noreferrer">
          <span>
            <small>Proyecto abierto</small>
            Código y catálogo en GitHub
          </span>
          <GitFork size={20} />
        </a>
      </nav>
    </div>

    <div class="about-modal__copy">
      <p class="about-modal__lead">
        Arteteca es una exposición digital abierta: un lugar en el que una pintura célebre,
        una talla anónima, una fotografía documental, un manuscrito o una huella trazada
        sobre roca pueden compartir espacio sin someterse a un único recorrido.
      </p>
      <p>
        El proyecto ha sido creado por <strong>Alejandro Pico Perez</strong> como una exploración
        personal, técnica y editorial. Busca acercar obras muy distintas, disfrutar de ellas
        y, al mismo tiempo, demostrar cómo el desarrollo web puede construir nuevas maneras
        de descubrir, ordenar y narrar el patrimonio artístico.
      </p>
      <p>
        Cada ficha crece a partir de archivos independientes. La información se adapta a la
        pieza: si no se conoce su autoría, esa sección no se inventa; si una obra exige hablar
        de restauraciones, materiales, contexto o interpretaciones, dispone de su propio lugar.
      </p>
      <p>
        Arteteca se desarrolla públicamente en GitHub y está pensada para ampliarse obra a obra.
        Su estructura, su código y sus instrucciones de catalogación permanecen abiertos para
        que otras personas —y otras inteligencias artificiales— puedan estudiarla, mejorarla
        y contribuir a la colección con rigor.
      </p>
    </div>

  </section>
</div>
