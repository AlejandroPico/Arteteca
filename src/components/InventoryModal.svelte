<script lang="ts">
  import { onMount } from 'svelte';
  import {
    AlertTriangle,
    BookOpenText,
    CheckCircle2,
    Download,
    FileSpreadsheet,
    FileText,
    Search,
    ShieldCheck,
    X,
  } from '@lucide/svelte';
  import ARTETECA_AI_CONTEXT from '../../ARTETECA_AI_CONTEXT.md?raw';
  import { normalizeForSearch } from '../lib/catalog';
  import type { Catalogo, ObraResumen } from '../lib/types';

  export let catalog: Catalogo;
  export let cerrar: () => void;

  type Vista = 'inventario' | 'cobertura' | 'validacion' | 'superprompt';
  let vista: Vista = 'inventario';
  let query = '';
  let coverageBlocks: Array<{ title: string; entries: Array<[string, number]> }> = [];
  const superpromptWords = ARTETECA_AI_CONTEXT.trim().split(/\s+/).length;
  const superpromptLines = ARTETECA_AI_CONTEXT.split('\n').length;

  const exportColumns: Array<[keyof ReturnType<typeof rowFrom>, string]> = [
    ['id', 'ID'],
    ['titulo', 'Título'],
    ['autor', 'Autoría'],
    ['fecha', 'Fecha'],
    ['tipo', 'Tipo'],
    ['periodo', 'Periodo'],
    ['coleccion', 'Colección editorial'],
    ['pais', 'País o cultura'],
    ['localizacion', 'Institución o lugar'],
    ['ciudad', 'Ciudad'],
    ['tecnicas', 'Técnicas'],
    ['pestanas', 'Pestañas'],
    ['altaResolucion', 'Alta resolución'],
    ['licencia', 'Licencia'],
    ['reconocimiento', 'Premio o reconocimiento'],
    ['estado', 'Estado'],
  ];

  function rowFrom(work: ObraResumen) {
    const issues: string[] = [];
    if (!work.imagen?.fuente) issues.push('sin fuente de imagen');
    if (!work.imagen?.licencia) issues.push('sin licencia');
    if (!work.pestanas?.length) issues.push('sin pestañas');
    if (!work.localizacion) issues.push('sin localización');
    if (!work.tieneAltaResolucion) issues.push('sin variante de alta resolución');
    return {
      id: work.id,
      titulo: work.titulo,
      autor: work.autor,
      fecha: work.fecha,
      tipo: work.tipo,
      periodo: work.periodo,
      coleccion: work.coleccion ?? '',
      pais: work.pais ?? '',
      localizacion: work.localizacion ?? '',
      ciudad: work.ciudad ?? '',
      tecnicas: (work.tecnicas ?? []).join(', '),
      pestanas: work.pestanas.map((tab) => tab.titulo).join(', '),
      numeroPestanas: work.pestanas.length,
      altaResolucion: work.tieneAltaResolucion ? 'Sí' : 'No',
      licencia: work.imagen.licencia,
      reconocimiento: work.reconocimiento ?? '',
      issues,
      estado: issues.length ? `${issues.length} aviso${issues.length === 1 ? '' : 's'}` : 'Completa',
    };
  }

  const rows = catalog.obras.map(rowFrom).sort((a, b) => a.titulo.localeCompare(b.titulo, 'es'));
  $: normalizedQuery = normalizeForSearch(query);
  $: filteredRows = normalizedQuery
    ? rows.filter((row) =>
        normalizeForSearch(
          Object.values(row)
            .map((value) => (Array.isArray(value) ? value.join(' ') : String(value)))
            .join(' '),
        ).includes(normalizedQuery),
      )
    : rows;
  $: warningRows = rows.filter((row) => row.issues.length);
  $: completeRows = rows.length - warningRows.length;
  $: coverageBlocks = [
    { title: 'Colecciones editoriales', entries: countBy('coleccion') },
    { title: 'Tipos de obra', entries: countBy('tipo') },
    { title: 'Periodos', entries: countBy('periodo') },
    { title: 'Países y culturas', entries: countBy('pais') },
  ];

  function countBy(field: 'coleccion' | 'tipo' | 'periodo' | 'pais') {
    const counts = new Map<string, number>();
    rows.forEach((row) => {
      const label = row[field] || 'Sin clasificar';
      counts.set(label, (counts.get(label) ?? 0) + 1);
    });
    return [...counts.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0], 'es'));
  }

  function csvCell(value: unknown) {
    return `"${String(value ?? '').replace(/"/g, '""')}"`;
  }

  function download(content: string, filename: string, type: string) {
    const url = URL.createObjectURL(new Blob([content], { type }));
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
  }

  function downloadCsv() {
    const csv = [
      exportColumns.map(([, label]) => csvCell(label)).join(';'),
      ...rows.map((row) => exportColumns.map(([field]) => csvCell(row[field])).join(';')),
    ].join('\n');
    download(`\ufeff${csv}`, 'inventario-arteteca.csv', 'text/csv;charset=utf-8');
  }

  function downloadText() {
    const lines = [
      `ARTETECA — INVENTARIO DE ${rows.length} OBRAS`,
      `Generado: ${new Date().toLocaleString('es-ES')}`,
      '',
    ];
    rows.forEach((row, index) => {
      lines.push(
        `${index + 1}. ${row.titulo} — ${row.autor}`,
        `   ${row.fecha} · ${row.tipo} · ${row.periodo}${row.coleccion ? ` · ${row.coleccion}` : ''}`,
        `   ${[row.localizacion, row.ciudad, row.pais].filter(Boolean).join(' · ') || 'Sin localización'}`,
        `   Pestañas: ${row.pestanas || 'ninguna'} · Estado: ${row.estado}`,
        row.reconocimiento ? `   Reconocimiento: ${row.reconocimiento}` : '',
        '',
      );
    });
    const text = lines.join('\n');
    download(text, 'inventario-arteteca.txt', 'text/plain;charset=utf-8');
  }

  function downloadExcel() {
    const header = exportColumns.map(([, label]) => `<th>${label}</th>`).join('');
    const body = rows
      .map((row) => `<tr>${exportColumns.map(([field]) => `<td>${String(row[field] ?? '')}</td>`).join('')}</tr>`)
      .join('');
    const workbook = `<!doctype html><html><head><meta charset="utf-8"><style>table{border-collapse:collapse;font-family:Arial,sans-serif}th,td{border:1px solid #aaa;padding:6px 9px;text-align:left}th{background:#ede8de}</style></head><body><table><thead><tr>${header}</tr></thead><tbody>${body}</tbody></table></body></html>`;
    download(`\ufeff${workbook}`, 'inventario-arteteca.xls', 'application/vnd.ms-excel;charset=utf-8');
  }

  function downloadSuperprompt() {
    download(ARTETECA_AI_CONTEXT, 'ARTETECA_AI_CONTEXT.txt', 'text/plain;charset=utf-8');
  }

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

<div class="inventory-modal" role="dialog" aria-modal="true" aria-labelledby="inventory-title">
  <button class="inventory-modal__scrim" type="button" aria-label="Cerrar inventario" onclick={cerrar}></button>
  <section class:inventory-modal__panel--superprompt={vista === 'superprompt'} class="inventory-modal__panel">
    <header class="inventory-modal__header">
      <div>
        <span class="eyebrow">Herramienta interna · Alt + clic</span>
        <h2 id="inventory-title">Inventario de Arteteca</h2>
      </div>
      <button class="inventory-modal__close" type="button" aria-label="Cerrar" onclick={cerrar}><X size={21} /></button>
    </header>

    <nav class="inventory-tabs" aria-label="Vistas del inventario">
      <button class:active={vista === 'inventario'} type="button" onclick={() => (vista = 'inventario')}>Inventario</button>
      <button class:active={vista === 'cobertura'} type="button" onclick={() => (vista = 'cobertura')}>Cobertura</button>
      <button class:active={vista === 'validacion'} type="button" onclick={() => (vista = 'validacion')}>Validación</button>
      <button class:active={vista === 'superprompt'} type="button" onclick={() => (vista = 'superprompt')}>Superprompt</button>
    </nav>

    {#if vista === 'superprompt'}
      <div class="inventory-toolbar inventory-toolbar--superprompt">
        <div class="inventory-toolbar__prompt">
          <BookOpenText size={19} />
          <span>
            <strong>Contexto maestro para continuar Arteteca con cualquier IA</strong>
            <small>{superpromptWords.toLocaleString('es-ES')} palabras · {superpromptLines.toLocaleString('es-ES')} líneas · fuente canónica: ARTETECA_AI_CONTEXT.md</small>
          </span>
        </div>
        <div>
          <button type="button" onclick={downloadSuperprompt}><FileText size={16} /> Descargar TXT</button>
        </div>
      </div>
    {:else}
      <div class="inventory-toolbar">
        <label>
          <Search size={16} />
          <input type="search" placeholder="Obra, autor, periodo, cultura, técnica…" bind:value={query} />
        </label>
        <div>
          <button type="button" onclick={downloadText}><FileText size={16} /> TXT</button>
          <button type="button" onclick={downloadCsv}><Download size={16} /> CSV</button>
          <button type="button" onclick={downloadExcel}><FileSpreadsheet size={16} /> Excel</button>
        </div>
      </div>

      <section class="inventory-summary" aria-label="Resumen del catálogo">
        <article><strong>{rows.length}</strong><span>obras</span></article>
        <article><strong>{catalog.colecciones?.length ?? 0}</strong><span>colecciones</span></article>
        <article><strong>{catalog.tipos.length}</strong><span>tipos</span></article>
        <article><strong>{catalog.periodos.length}</strong><span>periodos</span></article>
        <article><strong>{completeRows}</strong><span>completas</span></article>
        <article class:warn={warningRows.length > 0}><strong>{warningRows.length}</strong><span>con avisos</span></article>
      </section>
    {/if}

    <div class="inventory-content">
      {#if vista === 'inventario'}
        <div class="inventory-table-wrap">
          <table>
            <thead><tr><th>Obra</th><th>Colección</th><th>Tipo</th><th>Fecha</th><th>Lugar</th><th>Pestañas</th><th>Estado</th></tr></thead>
            <tbody>
              {#each filteredRows as row (row.id)}
                <tr>
                  <td><strong>{row.titulo}</strong><small>{row.autor}</small></td>
                  <td>{row.coleccion || row.periodo}</td>
                  <td>{row.tipo}</td>
                  <td>{row.fecha}</td>
                  <td>{[row.localizacion, row.ciudad].filter(Boolean).join(' · ') || '—'}</td>
                  <td>{row.numeroPestanas}</td>
                  <td class:inventory-ok={!row.issues.length} class:inventory-warn={row.issues.length > 0}>
                    {#if row.issues.length}<AlertTriangle size={14} />{:else}<CheckCircle2 size={14} />{/if}
                    {row.estado}
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      {:else if vista === 'cobertura'}
        <div class="inventory-coverage">
          {#each coverageBlocks as block}
            <section>
              <h3>{block.title}</h3>
              <div class="coverage-list">
                {#each block.entries as entry}
                  <div>
                    <span>{entry[0]}</span><strong>{entry[1]}</strong>
                    <i style={`--coverage: ${(entry[1] / rows.length) * 100}%`}></i>
                  </div>
                {/each}
              </div>
            </section>
          {/each}
        </div>
      {:else if vista === 'validacion'}
        <div class="inventory-validation">
          <header><ShieldCheck size={24} /><div><h3>Control editorial automático</h3><p>Comprueba metadatos esenciales, pestañas, procedencia, licencia y reproducción ampliable.</p></div></header>
          {#if warningRows.length}
            {#each warningRows as row (row.id)}
              <article><AlertTriangle size={17} /><strong>{row.titulo}</strong><span>{row.issues.join(' · ')}</span></article>
            {/each}
          {:else}
            <div class="inventory-validation__empty"><CheckCircle2 size={30} /><p>Las {rows.length} obras superan todas las comprobaciones.</p></div>
          {/if}
        </div>
      {:else}
        <article class="inventory-superprompt">
          <header>
            <span class="eyebrow">Archivo de contexto · Markdown en texto plano</span>
            <h3>ARTETECA_AI_CONTEXT</h3>
            <p>Entrega el archivo completo a otra inteligencia artificial como contexto inicial. El TXT descargado conserva títulos, listas, ejemplos, código y esquema SQL.</p>
          </header>
          <pre>{ARTETECA_AI_CONTEXT}</pre>
        </article>
      {/if}
    </div>
  </section>
</div>
