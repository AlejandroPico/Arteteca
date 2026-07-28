#!/usr/bin/env python3
"""Compila la carpeta ``obras`` en índices rápidos para la web de Arteteca.

La carpeta sigue siendo la fuente de verdad. Este script crea:

* ``public/data/catalogo.json``: resumen ligero para el mosaico inicial.
* ``public/data/obras/<id>.json``: ficha completa, cargada solo al abrirla.
* ``public/data/arteteca.sqlite``: índice portable para búsquedas, auditoría y
  futuras aplicaciones de escritorio o API.

No necesita paquetes externos: usa únicamente la biblioteca estándar de Python.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sqlite3
import sys
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OBRAS_DIR = ROOT / "obras"
DATA_DIR = ROOT / "public" / "data"
DETAIL_DIR = DATA_DIR / "obras"
MEDIA_DIR = DATA_DIR / "media"
SECTION_PATTERN = re.compile(r"^(?P<order>\d{2,3})-(?P<slug>[a-z0-9-]+)\.md$")
ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
REQUIRED_FIELDS = {
    "id",
    "titulo",
    "autor",
    "fecha",
    "tipo",
    "periodo",
    "descripcion",
    "imagen",
}


@dataclass
class BuildError:
    path: Path
    message: str

    def __str__(self) -> str:
        return f"{self.path.relative_to(ROOT)}: {self.message}"


def compact_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def pretty_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def normalise_text(value: str) -> str:
    return " ".join(value.split())


def parse_frontmatter(raw: str) -> tuple[dict[str, str], str]:
    if not raw.startswith("---\n"):
        return {}, raw.strip()

    closing = raw.find("\n---\n", 4)
    if closing == -1:
        return {}, raw.strip()

    metadata: dict[str, str] = {}
    for line in raw[4:closing].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip("\"'")
    return metadata, raw[closing + 5 :].strip()


def title_from_slug(slug: str) -> str:
    words = slug.replace("-", " ").split()
    return " ".join(word.capitalize() for word in words)


def image_url(work_dir: Path, work_id: str, image: dict[str, Any], errors: list[BuildError]) -> str:
    local_file = image.get("archivo")
    remote_url = image.get("url")

    if local_file:
        source = work_dir / str(local_file)
        if not source.is_file():
            errors.append(BuildError(source, "la imagen local indicada no existe"))
            return ""
        destination = MEDIA_DIR / work_id / source.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        return f"data/media/{work_id}/{source.name}"

    if isinstance(remote_url, str) and remote_url.startswith(("https://", "http://")):
        return remote_url

    errors.append(
        BuildError(
            work_dir / "obra.json",
            "imagen debe incluir `archivo` (local) o `url` (remota)",
        )
    )
    return ""


def high_resolution_image_url(
    work_dir: Path,
    work_id: str,
    image: dict[str, Any],
    errors: list[BuildError],
    *,
    write_media: bool,
) -> str | None:
    local_file = image.get("archivoAltaResolucion")
    remote_url = image.get("urlAltaResolucion")

    if local_file:
        source = work_dir / str(local_file)
        if not source.is_file():
            errors.append(BuildError(source, "la imagen de alta resolución indicada no existe"))
            return None
        if not write_media:
            return str(local_file)
        destination = MEDIA_DIR / work_id / source.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        return f"data/media/{work_id}/{source.name}"

    if remote_url is None:
        return None
    if isinstance(remote_url, str) and remote_url.startswith(("https://", "http://")):
        return remote_url

    errors.append(
        BuildError(
            work_dir / "obra.json",
            "`imagen.urlAltaResolucion` debe ser una URL http(s)",
        )
    )
    return None


def load_work(work_dir: Path, errors: list[BuildError], *, write_media: bool) -> dict[str, Any] | None:
    metadata_path = work_dir / "obra.json"
    if not metadata_path.is_file():
        errors.append(BuildError(work_dir, "falta el archivo obligatorio obra.json"))
        return None

    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(BuildError(metadata_path, f"JSON no válido: {exc}"))
        return None

    missing = sorted(REQUIRED_FIELDS - metadata.keys())
    if missing:
        errors.append(BuildError(metadata_path, f"faltan campos: {', '.join(missing)}"))
        return None

    work_id = metadata.get("id")
    if not isinstance(work_id, str) or not ID_PATTERN.fullmatch(work_id):
        errors.append(BuildError(metadata_path, "`id` debe ser un slug en minúsculas"))
        return None
    if work_id != work_dir.name:
        errors.append(BuildError(metadata_path, "`id` debe coincidir con el nombre de la carpeta"))

    image = metadata.get("imagen")
    if not isinstance(image, dict):
        errors.append(BuildError(metadata_path, "`imagen` debe ser un objeto"))
        return None

    if write_media:
        resolved_image = image_url(work_dir, work_id, image, errors)
    else:
        resolved_image = str(image.get("url") or image.get("archivo") or "")
    resolved_high_resolution = high_resolution_image_url(
        work_dir,
        work_id,
        image,
        errors,
        write_media=write_media,
    )

    sections: list[dict[str, Any]] = []
    seen_orders: set[int] = set()
    for section_path in sorted(work_dir.glob("*.md")):
        match = SECTION_PATTERN.match(section_path.name)
        if not match:
            errors.append(
                BuildError(
                    section_path,
                    "las secciones deben llamarse `NN-nombre.md` (por ejemplo, 10-historia.md)",
                )
            )
            continue
        order = int(match.group("order"))
        if order in seen_orders:
            errors.append(BuildError(section_path, f"orden de pestaña duplicado: {order}"))
            continue
        seen_orders.add(order)
        frontmatter, content = parse_frontmatter(section_path.read_text(encoding="utf-8"))
        if not content:
            errors.append(BuildError(section_path, "la sección está vacía"))
            continue
        slug = match.group("slug")
        sections.append(
            {
                "id": slug,
                "titulo": frontmatter.get("titulo", title_from_slug(slug)),
                "icono": frontmatter.get("icono", "archivo"),
                "orden": order,
                "contenido": content,
                "archivo": section_path.name,
            }
        )

    sections.sort(key=lambda item: item["orden"])
    tags = sorted(
        {
            normalise_text(str(value))
            for value in (
                metadata.get("etiquetas", [])
                + metadata.get("tecnicas", [])
                + [metadata.get("tipo", ""), metadata.get("periodo", "")]
            )
            if str(value).strip()
        },
        key=str.casefold,
    )

    ratio = metadata.get("proporcion", [4, 3])
    if (
        not isinstance(ratio, list)
        or len(ratio) != 2
        or not all(isinstance(value, (int, float)) and value > 0 for value in ratio)
    ):
        errors.append(BuildError(metadata_path, "`proporcion` debe ser [ancho, alto] con números positivos"))
        ratio = [4, 3]

    compiled_image = {**image, "src": resolved_image}
    if resolved_high_resolution:
        compiled_image["srcAltaResolucion"] = resolved_high_resolution

    return {
        **metadata,
        "imagen": compiled_image,
        "proporcion": ratio,
        "etiquetas": tags,
        "secciones": sections,
    }


def summary_from(work: dict[str, Any]) -> dict[str, Any]:
    lightweight_image = {
        key: value
        for key, value in work["imagen"].items()
        if key not in {"archivoAltaResolucion", "urlAltaResolucion", "srcAltaResolucion"}
    }
    return {
        "id": work["id"],
        "titulo": work["titulo"],
        "tituloOriginal": work.get("tituloOriginal"),
        "autor": work["autor"],
        "fecha": work["fecha"],
        "fechaOrden": work.get("fechaOrden"),
        "tipo": work["tipo"],
        "periodo": work["periodo"],
        "coleccion": work.get("coleccion"),
        "reconocimiento": work.get("reconocimiento"),
        "descripcion": work["descripcion"],
        "localizacion": work.get("localizacion"),
        "ciudad": work.get("ciudad"),
        "urlLocalizacion": work.get("urlLocalizacion"),
        "urlMapa": work.get("urlMapa"),
        "pais": work.get("pais"),
        "tecnicas": work.get("tecnicas", []),
        "tieneAltaResolucion": bool(work["imagen"].get("srcAltaResolucion")),
        "proporcion": work["proporcion"],
        "color": work.get("color", "#8f543d"),
        "etiquetas": work["etiquetas"],
        "imagen": lightweight_image,
        "pestanas": [
            {"id": section["id"], "titulo": section["titulo"], "icono": section["icono"]}
            for section in work["secciones"]
        ],
    }


def create_database(path: Path, works: list[dict[str, Any]], build_id: str) -> None:
    if path.exists():
        path.unlink()
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        PRAGMA journal_mode = DELETE;
        PRAGMA foreign_keys = ON;
        CREATE TABLE metadatos (
            clave TEXT PRIMARY KEY,
            valor TEXT NOT NULL
        );
        CREATE TABLE obras (
            id TEXT PRIMARY KEY,
            titulo TEXT NOT NULL,
            titulo_original TEXT,
            autor TEXT NOT NULL,
            fecha TEXT NOT NULL,
            fecha_orden INTEGER,
            tipo TEXT NOT NULL,
            periodo TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            localizacion TEXT,
            pais TEXT,
            imagen TEXT NOT NULL,
            proporcion_ancho REAL NOT NULL,
            proporcion_alto REAL NOT NULL,
            datos_json TEXT NOT NULL
        );
        CREATE TABLE secciones (
            obra_id TEXT NOT NULL REFERENCES obras(id) ON DELETE CASCADE,
            id TEXT NOT NULL,
            titulo TEXT NOT NULL,
            icono TEXT NOT NULL,
            orden INTEGER NOT NULL,
            contenido_markdown TEXT NOT NULL,
            archivo TEXT NOT NULL,
            PRIMARY KEY (obra_id, id)
        );
        CREATE TABLE etiquetas (
            obra_id TEXT NOT NULL REFERENCES obras(id) ON DELETE CASCADE,
            etiqueta TEXT NOT NULL,
            PRIMARY KEY (obra_id, etiqueta)
        );
        CREATE INDEX idx_obras_tipo ON obras(tipo);
        CREATE INDEX idx_obras_periodo ON obras(periodo);
        CREATE INDEX idx_obras_fecha ON obras(fecha_orden);
        CREATE INDEX idx_etiquetas_etiqueta ON etiquetas(etiqueta);
        """
    )
    connection.executemany(
        "INSERT INTO metadatos(clave, valor) VALUES (?, ?)",
        [
            ("schema_version", "1"),
            ("build_id", build_id),
            ("generado_utc", datetime.now(UTC).isoformat()),
            ("total_obras", str(len(works))),
        ],
    )

    for work in works:
        width, height = work["proporcion"]
        connection.execute(
            """
            INSERT INTO obras VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                work["id"],
                work["titulo"],
                work.get("tituloOriginal"),
                work["autor"],
                work["fecha"],
                work.get("fechaOrden"),
                work["tipo"],
                work["periodo"],
                work["descripcion"],
                work.get("localizacion"),
                work.get("pais"),
                work["imagen"]["src"],
                width,
                height,
                compact_json({key: value for key, value in work.items() if key != "secciones"}),
            ),
        )
        connection.executemany(
            "INSERT INTO secciones VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    work["id"],
                    section["id"],
                    section["titulo"],
                    section["icono"],
                    section["orden"],
                    section["contenido"],
                    section["archivo"],
                )
                for section in work["secciones"]
            ],
        )
        connection.executemany(
            "INSERT INTO etiquetas VALUES (?, ?)",
            [(work["id"], tag) for tag in work["etiquetas"]],
        )

    try:
        connection.executescript(
            """
            CREATE VIRTUAL TABLE busqueda USING fts5(
                obra_id UNINDEXED,
                titulo,
                autor,
                texto,
                tokenize = 'unicode61 remove_diacritics 2'
            );
            """
        )
        for work in works:
            full_text = "\n".join(section["contenido"] for section in work["secciones"])
            connection.execute(
                "INSERT INTO busqueda VALUES (?, ?, ?, ?)",
                (work["id"], work["titulo"], work["autor"], full_text),
            )
    except sqlite3.OperationalError:
        # Algunas compilaciones mínimas de SQLite no incluyen FTS5. El catálogo
        # continúa siendo plenamente funcional sin este índice opcional.
        pass

    connection.commit()
    connection.execute("VACUUM")
    connection.close()


def compile_catalog(*, check_only: bool) -> int:
    errors: list[BuildError] = []
    if not OBRAS_DIR.is_dir():
        print("No existe la carpeta `obras`.", file=sys.stderr)
        return 1

    work_dirs = sorted(path for path in OBRAS_DIR.iterdir() if path.is_dir() and not path.name.startswith("."))
    if not work_dirs:
        print("La carpeta `obras` no contiene ninguna obra.", file=sys.stderr)
        return 1

    if not check_only:
        DETAIL_DIR.mkdir(parents=True, exist_ok=True)
        if MEDIA_DIR.exists():
            shutil.rmtree(MEDIA_DIR)

    works = [
        work
        for directory in work_dirs
        if (work := load_work(directory, errors, write_media=not check_only)) is not None
    ]

    ids = [work["id"] for work in works]
    for duplicate in sorted({work_id for work_id in ids if ids.count(work_id) > 1}):
        errors.append(BuildError(OBRAS_DIR, f"id de obra duplicado: {duplicate}"))

    if errors:
        print(f"Se encontraron {len(errors)} error(es):", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    if check_only:
        print(f"Catálogo válido: {len(works)} obras y {sum(len(w['secciones']) for w in works)} secciones.")
        return 0

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for old_detail in DETAIL_DIR.glob("*.json"):
        old_detail.unlink()

    summaries = [summary_from(work) for work in works]
    digest = hashlib.sha256(compact_json(summaries).encode("utf-8")).hexdigest()[:16]
    catalog = {
        "version": 1,
        "buildId": digest,
        "total": len(summaries),
        "tipos": sorted({work["tipo"] for work in works}, key=str.casefold),
        "periodos": sorted({work["periodo"] for work in works}, key=str.casefold),
        "colecciones": sorted(
            {work["coleccion"] for work in works if work.get("coleccion")},
            key=str.casefold,
        ),
        "obras": summaries,
    }

    (DATA_DIR / "catalogo.json").write_text(pretty_json(catalog), encoding="utf-8")
    for work in works:
        (DETAIL_DIR / f"{work['id']}.json").write_text(pretty_json(work), encoding="utf-8")

    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False, dir=DATA_DIR) as temp:
        temp_path = Path(temp.name)
    create_database(temp_path, works, digest)
    temp_path.replace(DATA_DIR / "arteteca.sqlite")

    print(
        f"Catálogo {digest}: {len(works)} obras, "
        f"{sum(len(work['secciones']) for work in works)} pestañas."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Compila el catálogo de Arteteca")
    parser.add_argument(
        "--check",
        action="store_true",
        help="solo valida la estructura; no genera archivos",
    )
    args = parser.parse_args()
    return compile_catalog(check_only=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
