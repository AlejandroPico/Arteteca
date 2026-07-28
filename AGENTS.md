# Instrucciones para asistentes que amplíen Arteteca

Lee primero `ARTETECA_AI_CONTEXT.md`: es el manual canónico y exhaustivo de continuidad para cualquier asistente de IA. Después consulta `README.md`, `obras/README.md`, el esquema y el código cuando necesites comprobar detalles de la versión actual. La carpeta `obras/` es la fuente de verdad.

Al añadir una obra:

1. investiga en fuentes museísticas, patrimoniales o académicas;
2. comprueba expresamente los derechos de la reproducción;
3. crea una carpeta única cuyo nombre coincida con `obra.json.id`;
4. añade únicamente las secciones Markdown para las que exista información;
5. no edites `public/data/` a mano;
6. ejecuta `npm run check` y `npm run build`;
7. revisa visualmente portada, proporción, título, autor, móvil y ficha;
8. conserva la interfaz y el contrato existentes salvo que se haya pedido cambiarlos.

No inventes un autor, una fecha exacta, dimensiones, materiales o teorías. Usa «Autoría desconocida», rangos o `c.` cuando corresponda. Separa los hechos documentados de atribuciones, leyendas e interpretaciones.

Las imágenes locales deben ser WebP o AVIF optimizadas cuando la fuente permita redistribución. Cada imagen necesita `alt`, `fuente`, `licencia` y, si procede, `credito`.
