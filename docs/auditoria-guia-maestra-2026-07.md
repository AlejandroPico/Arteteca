# Auditoría de la Guía Maestra de artistas y obras

Fecha de revisión: **28 de julio de 2026**

> Esta es la primera fotografía de la incorporación. La continuación, incluida
> la descomposición de tres series de Goya y la recepción de la Parte II, se
> documenta en [`auditoria-guias-maestras-2026-08.md`](./auditoria-guias-maestras-2026-08.md).

## Resultado

La guía aportada contiene **894 entradas** distribuidas entre 75 artistas,
talleres o tradiciones. Se comparó con el catálogo de 200 obras que tenía
Arteteca antes de esta ampliación.

El resultado de esta primera incorporación rigurosa es:

| Estado | Entradas |
|---|---:|
| Ya presentes y verificadas en Arteteca | 77 |
| Nuevas fichas incorporadas | 280 |
| Pendientes de resolución individual | 537 |
| Catálogo final tras la tanda | 480 |

Las 280 incorporaciones aportan cinco pestañas documentales cada una, por lo que
el catálogo pasa de 990 a **2.390 pestañas**.

## Qué significa «pendiente»

Una entrada pendiente no está rechazada. Significa que no superó todavía todas
las comprobaciones necesarias para publicarse como ficha fiable. Las causas
principales son:

- la guía trata como obras independientes escenas que pertenecen a un único
  mural, friso, manuscrito, cueva, ciclo o conjunto;
- el nombre usado es demasiado genérico o mezcla dos obras distintas;
- la obra original está perdida y la imagen encontrada es una copia o
  reconstrucción sin identificar;
- la atribución propuesta por la guía no coincide con el catálogo de la obra;
- no apareció una reproducción inequívoca con licencia reutilizable;
- se trata de una obra moderna o contemporánea cuyos derechos siguen vigentes;
- faltan identificadores o fuentes institucionales suficientes para evitar una
  coincidencia falsa.

No se han creado tarjetas con imágenes inventadas, fotografías de otra obra ni
licencias supuestas para alcanzar artificialmente el total de 894.

## Correcciones aplicadas durante la comparación

La guía es útil como mapa inicial, pero contiene errores y simplificaciones. Se
han aplicado, entre otras, estas correcciones:

- **Maestro del Mosaico de Alejandro:** no se atribuyeron al mismo maestro otras
  piezas pompeyanas y romanas sin relación demostrada.
- **Shankei / bronces de Benín:** no se aceptó la unión de un escultor japonés
  con la tradición colectiva de las placas de Benín.
- **Fidias:** Zeus de Olimpia y Atenea Promacos se incorporaron expresamente como
  reconstrucciones documentales; Atenea Lemnia se presenta mediante las copias
  conservadas.
- **Leonardo:** no se incorporó *La batalla de Anghiari* como si el mural original
  sobreviviera.
- **Tiziano:** se rechazó una coincidencia que confundía el retrato individual de
  Paulo III con el retrato del papa acompañado por sus sobrinos.
- **Caravaggio:** se evitó duplicar *Judit decapitando a Holofernes* con una
  versión discutida de Toulouse.
- **Hiroshige:** no se hizo pasar la serie completa del Tōkaidō por la estampa
  concreta de Kambara.
- **Cézanne:** se separaron autorretratos y naturalezas muertas que la búsqueda
  aproximada había confundido.
- **Mondrian:** no se equipararon composiciones distintas por compartir número,
  colores o una estructura de título similar.

## Cobertura incorporada

Se añadieron obras de 46 autorías verificadas. Los grupos con mayor crecimiento
fueron:

| Autoría | Nuevas obras |
|---|---:|
| Vincent van Gogh | 13 |
| Auguste Rodin | 13 |
| Gian Lorenzo Bernini | 12 |
| Alberto Durero | 11 |
| Pieter Brueghel el Viejo | 11 |
| Caravaggio | 10 |
| Jan van Eyck | 9 |
| Jacques-Louis David | 9 |
| El Greco | 9 |
| Édouard Manet | 9 |
| Rafael | 8 |
| Rubens, Vermeer, Goya, Delacroix, El Bosco, Velázquez, Monet y Gauguin | 8 cada uno |

También se ampliaron Grecia clásica y helenística, China, Protorrenacimiento,
Gótico sienés, Renacimiento italiano y nórdico, Barroco, Rococó, Ukiyo-e,
Neoclasicismo, Romanticismo, Realismo, Impresionismo, Postimpresionismo,
Neoimpresionismo, Fauvismo, abstracción, Neoplasticismo y Suprematismo.

## Trazabilidad de cada ficha

Cada obra incorporada conserva en `obra.json`:

```json
{
  "referencia": {
    "wikidata": "https://www.wikidata.org/wiki/Q…",
    "qid": "Q…",
    "guia": "Título tal como apareció en la guía",
    "coincidencia": 1,
    "importada": "2026-07-28"
  }
}
```

Además:

- `90-fuentes.md` enlaza Wikidata, Wikimedia Commons y la institución cuando
  está disponible;
- `imagen.url` usa una derivada apta para el mosaico;
- `imagen.urlAltaResolucion` conserva el archivo original de Commons;
- `imagen.fuente`, `imagen.licencia` e `imagen.credito` documentan la
  reproducción;
- la proporción se obtiene de las dimensiones reales del archivo;
- la guía queda citada como origen de la selección, no como única fuente
  académica.

## Próxima pasada recomendada

Las 537 entradas pendientes deben resolverse por bloques pequeños. El orden más
útil sería:

1. conjuntos antiguos y medievales de autoría colectiva;
2. obras seguras de artistas en dominio público que no tenían identificador o
   imagen estructurada;
3. series y ciclos que necesitan decidir si se catalogan como conjunto o como
   escenas individuales;
4. arte moderno y contemporáneo, solo después de resolver derechos de imagen
   obra por obra.

Este documento debe actualizarse si una pasada posterior transforma entradas
pendientes en nuevas fichas.
