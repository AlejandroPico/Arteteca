# Contrato de la carpeta `obras/`

Esta carpeta es el archivo editorial de Arteteca. **Cada subcarpeta representa exactamente una obra** y puede contener tantos documentos como la pieza necesite.

## 1. Nombre de la carpeta

Usa un identificador único:

```text
titulo-breve-autor-o-lugar
```

Reglas:

- minúsculas;
- palabras separadas por guiones;
- sin espacios, tildes ni signos;
- debe evitar colisiones entre obras con el mismo título;
- debe coincidir exactamente con el campo `id` de `obra.json`.

Ejemplos:

```text
la-ultima-cena-leonardo
la-ultima-cena-tintoretto
bisontes-altamira
david-miguel-angel
```

## 2. Archivo obligatorio `obra.json`

Es el resumen rápido para el mosaico, la búsqueda y los filtros.

Campos obligatorios:

| Campo | Uso |
|---|---|
| `id` | Identificador único; igual al nombre de la carpeta |
| `titulo` | Título mostrado |
| `autor` | Nombre o fórmula rigurosa: «Autoría desconocida», «Taller de…» |
| `fecha` | Texto visible: `1656`, `c. 800`, `1501–1504` |
| `tipo` | Pintura, Escultura, Fotografía, Arte rupestre… |
| `periodo` | Barroco, Helenismo, Arte insular… |
| `descripcion` | Resumen breve de dos o tres frases |
| `imagen` | Reproducción, texto alternativo, fuente y licencia |

Campos muy recomendados:

- `tituloOriginal`
- `fechaOrden` como entero; los años a. C. son negativos
- `coleccion`: ruta editorial amplia utilizada por el inventario interno
- `reconocimiento`: premio, declaración patrimonial o reconocimiento relevante, si existe
- `localizacion`: institución o lugar, sin repetir la ciudad
- `ciudad`
- `urlLocalizacion`: ficha oficial de la obra o web oficial de la institución
- `urlMapa`: ubicación de la institución o lugar
- `pais`
- `dimensiones`
- `tecnicas`
- `etiquetas`
- `proporcion`: `[ancho, alto]`
- `color`: color ambiental hexadecimal de la tarjeta

La imagen admite dos modalidades:

```json
{
  "imagen": {
    "archivo": "portada.webp",
    "alt": "Descripción visual precisa",
    "fuente": "https://museo.example/obra",
    "licencia": "Dominio público",
    "credito": "Museo o fotógrafo",
    "foco": "center 35%"
  }
}
```

o una URL remota:

```json
{
  "imagen": {
    "url": "https://servidor.example/imagen.jpg",
    "alt": "Descripción visual precisa",
    "fuente": "https://servidor.example/ficha",
    "licencia": "CC BY-SA 4.0"
  }
}
```

La opción local es preferible si la licencia permite redistribuir la reproducción. Nunca se debe copiar una imagen sin verificar sus derechos.

Para el visor ampliable se puede añadir una segunda reproducción:

```json
{
  "imagen": {
    "url": "https://servidor.example/imagen-1600.jpg",
    "urlAltaResolucion": "https://servidor.example/imagen-original.jpg",
    "alt": "Descripción visual precisa",
    "fuente": "https://servidor.example/ficha",
    "licencia": "Dominio público"
  }
}
```

La variante de alta resolución queda fuera del catálogo ligero y se precarga únicamente cuando se abre la obra a pantalla completa. Debe escogerse el original cuando su peso sea razonable; para originales extraordinariamente grandes, usa la mayor derivada que el navegador pueda manejar con seguridad. La modalidad local equivalente es `archivoAltaResolucion`.

## 3. Pestañas detectadas por archivos

Todo archivo con el patrón siguiente se convierte en una pestaña:

```text
NN-nombre-de-pestana.md
```

- `NN` controla el orden.
- El nombre tras el número genera el identificador interno.
- El encabezado opcional cambia el título visible:

```md
---
titulo: Técnica y conservación
icono: tecnica
---

## Primer apartado

Contenido en Markdown…
```

No existe ninguna pestaña obligatoria. Ejemplos posibles:

```text
10-mirada.md
20-historia.md
30-autor.md
40-tecnica.md
50-contexto.md
60-restauraciones.md
70-simbolos.md
80-teorias.md
90-bibliografia.md
```

Si no se conoce la autoría, **no se crea `30-autor.md`**. No deben añadirse pestañas vacías ni inventar información para mantener una estructura uniforme.

## 4. Imágenes secundarias

Se pueden guardar dentro de la misma carpeta. En Markdown se referencian de forma relativa pensando en una futura ampliación del compilador. En la versión actual, la portada local sí se copia automáticamente; las imágenes incrustadas en secciones deben usar una URL pública y licenciada.

## 5. Comprobaciones antes de entregar

1. El título y la autoría son correctos.
2. Las fechas distinguen entre certeza y aproximación.
3. La localización es actual y sus enlaces oficial y cartográfico apuntan al lugar correcto.
4. La técnica y dimensiones proceden de una fuente fiable.
5. La imagen —incluida su variante de alta resolución— tiene licencia compatible, crédito, fuente y texto alternativo.
6. Las interpretaciones controvertidas están identificadas como hipótesis.
7. Los archivos tienen órdenes únicos.
8. `npm run check` termina sin errores.

## 6. Qué genera el compilador

No edites manualmente `public/data/`. `python3 scripts/build_catalog.py` genera:

- un índice compacto para abrir el mosaico;
- una ficha JSON completa por obra;
- una base SQLite con obras, pestañas y etiquetas;
- un índice de texto completo FTS5 cuando la instalación de SQLite lo admite.

Al subir cambios a `main`, GitHub Actions repite la validación y publica el resultado.
