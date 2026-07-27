# Arteteca

[![Construir y publicar Arteteca](https://github.com/AlejandroPico/Arteteca/actions/workflows/deploy-pages.yml/badge.svg)](https://github.com/AlejandroPico/Arteteca/actions/workflows/deploy-pages.yml)

**Arteteca** es una exposición digital abierta a cualquier forma de arte: pintura, escultura, relieve, grabado, fotografía, manuscrito, textil, cerámica, instalación o arte rupestre. La portada no impone una ruta de museo; presenta un mosaico distinto en cada visita y conserva las proporciones de las obras.

La aplicación está publicada mediante GitHub Pages y construida con Svelte 5, TypeScript, SCSS, Python y SQLite.

## Qué ofrece esta versión

- Mosaico irregular y denso con tarjetas panorámicas, cuadradas y verticales.
- Entrada editorial breve que se desvanece para mostrar el mosaico sin exigir desplazamiento.
- Orden aleatorio nuevo en cada carga y botón **Redescubrir**.
- Carga progresiva al hacer *scroll*.
- Barra superior fija con búsqueda desplegable, filtros, orden y acceso a **Acerca de**.
- Búsqueda por título, autor, fecha, técnica, tipo, periodo y etiquetas.
- Filtros por tipo y periodo; orden aleatorio, cronológico o alfabético.
- Modos claro, oscuro y automático.
- Ficha ampliada, navegación entre obras y visor inmersivo con rueda, pellizco, zoom y arrastre.
- Ventana editorial sobre el proyecto con enlaces al porfolio del autor y al repositorio público.
- Pestañas creadas automáticamente a partir de los archivos Markdown de cada obra.
- Índice JSON muy pequeño para la primera carga y fichas completas bajo demanda.
- Base de datos SQLite reconstruida en cada compilación.
- Diez obras iniciales de épocas, soportes y culturas diferentes.

## Arquitectura de carga

La carpeta [`obras/`](./obras) es la **fuente de verdad**. No se consulta toda esa carpeta desde el navegador, porque GitHub Pages no puede enumerar directorios y hacerlo sería lento.

Durante la compilación, [`scripts/build_catalog.py`](./scripts/build_catalog.py):

1. recorre las subcarpetas de `obras/`;
2. valida cada `obra.json`;
3. convierte cada `NN-nombre.md` en una pestaña;
4. genera `public/data/catalogo.json`, que solo contiene lo necesario para el mosaico;
5. genera una ficha independiente en `public/data/obras/<id>.json`;
6. genera `public/data/arteteca.sqlite` con obras, secciones, etiquetas e índice FTS5 cuando está disponible.

Así, la portada realiza una sola petición compacta. El contenido extenso de una obra se descarga únicamente cuando alguien abre su ficha. SQLite queda como índice portable, fuente para auditoría y base de futuras aplicaciones o API; el JSON resumido es deliberadamente la vía más rápida para el navegador.

## Estructura del proyecto

```text
Arteteca/
├── obras/                         # Fuente editorial: una carpeta por obra
│   └── las-meninas-velazquez/
│       ├── obra.json              # Metadatos, portada, filtros y licencia
│       ├── 10-mirada.md           # Primera pestaña
│       ├── 20-historia.md         # Segunda pestaña
│       ├── 30-autor.md            # Solo si la información existe
│       └── 40-composicion.md
├── plantillas/obra/               # Plantilla copiable para nuevas obras
├── public/data/                   # Índices generados; no editar a mano
├── schemas/obra.schema.json       # Contrato formal de obra.json
├── scripts/build_catalog.py       # Compilador y generador de SQLite
├── src/                           # Interfaz Svelte/TypeScript/SCSS
└── .github/workflows/             # Validación y publicación en Pages
```

## Cómo añadir una obra

La guía completa está en [`obras/README.md`](./obras/README.md). El procedimiento mínimo es:

1. copiar `plantillas/obra/` dentro de `obras/`;
2. renombrar la carpeta con un identificador único en minúsculas, sin espacios ni tildes;
3. completar `obra.json`;
4. añadir los archivos Markdown que realmente tengan contenido;
5. ejecutar `npm run check`;
6. ejecutar `npm run dev` para revisar la ficha.

No hay una lista fija de pestañas. Si una pieza prehistórica no tiene autor conocido, **no se crea un archivo de autor** y la interfaz no muestra esa pestaña. Si una obra necesita secciones singulares —por ejemplo, `50-restauraciones.md`, `60-inscripciones.md` o `70-teorias.md`—, basta con añadirlas.

## Desarrollo local

Requisitos:

- Node.js 24
- Python 3.12 o posterior
- npm 11 o posterior

```bash
npm install
npm run dev
```

Comandos disponibles:

```bash
npm run catalogo  # reconstruye JSON y SQLite
npm run check     # valida catálogo, TypeScript y Svelte
npm run build     # genera dist/ para producción
npm run preview   # sirve localmente la compilación
```

## GitHub Pages

El flujo `Construir y publicar Arteteca` se ejecuta con cada cambio en `main`. Usa las versiones actuales de las acciones oficiales y Node.js 24. En **Settings → Pages**, la fuente debe estar configurada como **GitHub Actions**.

La URL prevista es:

<https://alejandropico.github.io/Arteteca/>

## Imágenes, fuentes y licencias

Cada `obra.json` declara la URL de procedencia, el crédito y la licencia de su reproducción. La colección inicial usa archivos de Wikimedia Commons en dominio público o con licencias abiertas. La interfaz enlaza siempre a la ficha de origen.

Para una colección duradera se recomienda descargar una reproducción permitida, optimizarla como WebP o AVIF y guardarla dentro de la carpeta de la obra. El compilador admite tanto `imagen.archivo` como `imagen.url`.

- Código: [licencia MIT](./LICENSE).
- Textos editoriales propios: CC BY-SA 4.0.
- Reproducciones: la licencia indicada en cada `obra.json`; no quedan relicenciadas por el proyecto.

## Principio editorial

Arteteca separa hechos, interpretaciones y tradiciones populares. Antes de incorporar una obra deben comprobarse autoría, datación, técnica, localización y derechos de imagen en fuentes museísticas o académicas. Las teorías discutidas se pueden documentar, pero deben presentarse como tales y no como hechos.
