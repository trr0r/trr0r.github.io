#!/usr/bin/env python3

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import re
import shutil
import sys


ROOT = Path(__file__).resolve().parent.parent

PENDING_DIR = ROOT / "_pending"
POSTS_DIR = ROOT / "_posts"
IMAGES_DIR = ROOT / "assets" / "images" / "posts"

TIMEZONE = ZoneInfo("Europe/Madrid")


def slugify(value: str) -> str:
    value = value.strip().lower()

    replacements = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ü": "u",
        "ñ": "n",
    }

    for old, new in replacements.items():
        value = value.replace(old, new)

    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def read_front_matter(path: Path):
    text = path.read_text(encoding="utf-8")

    match = re.match(r"^---\s*\n(.*?)\n---\s*", text, re.DOTALL)

    if not match:
        raise ValueError(f"{path} no contiene un front matter válido")

    front_matter = match.group(1)
    body_start = match.end()

    title_match = re.search(
        r'^title:\s*["\']?(.*?)["\']?\s*$',
        front_matter,
        re.MULTILINE,
    )

    if not title_match:
        raise ValueError(f"{path} no contiene 'title:' en el front matter")

    title = title_match.group(1).strip().strip('"').strip("'")

    return text, front_matter, body_start, title


def update_front_matter(text: str, new_date: str) -> str:
    return re.sub(
        r"^date:\s*.*$",
        f"date: {new_date}",
        text,
        count=1,
        flags=re.MULTILINE,
    )


def update_image_paths(text: str, new_image_dir: str) -> str:
    """
    Cambia referencias del tipo:

    ../assets/images/posts/2025-05-29-lame/imagen.png

    a:

    ../assets/images/posts/2026-09-14-lame/imagen.png

    sin modificar otras rutas como:
    
    ../assets/images/posts/logos/hackthebox.png
    """

    pattern = r"(\.\./assets/images/posts/)(\d{4}-\d{2}-\d{2}-[^/\s)>\"]+)(/)"

    return re.sub(
        pattern,
        rf"\g<1>{new_image_dir}\3",
        text,
    )


def main():
    if not PENDING_DIR.exists():
        print("No existe _pending/. No hay nada que publicar.")
        return 0

    pending_posts = sorted(PENDING_DIR.glob("*.md"))

    if not pending_posts:
        print("No quedan artículos pendientes de publicación.")
        return 0

    # Para la prueba de concepto debe existir solamente Lame.md.
    if len(pending_posts) > 1:
        print("ERROR: Hay más de un artículo pendiente.")
        print("Artículos encontrados:")

        for post in pending_posts:
            print(f"  - {post.name}")

        print()
        print("Durante la prueba de concepto debe existir solamente un .md en _pending/.")
        return 1

    source = pending_posts[0]

    original_text, _, _, title = read_front_matter(source)

    now = datetime.now(TIMEZONE)

    date_string = now.strftime("%Y-%m-%d")
    datetime_string = now.strftime("%Y-%m-%d %H:%M:%S %z")

    slug = slugify(title)

    destination_post = POSTS_DIR / f"{date_string}-{slug}.md"
    destination_images = IMAGES_DIR / f"{date_string}-{slug}"

    print(f"Artículo seleccionado: {source.name}")
    print(f"Título: {title}")
    print(f"Slug: {slug}")
    print(f"Fecha de publicación: {datetime_string}")
    print(f"Post destino: {destination_post}")
    print(f"Imágenes destino: {destination_images}")

    # Seguridad: no publicar nunca encima de un post existente.
    existing_posts = list(POSTS_DIR.glob(f"*-{slug}.md"))

    if existing_posts:
        print()
        print("ERROR: El artículo parece estar ya publicado.")
        print("Posts encontrados:")

        for post in existing_posts:
            print(f"  - {post}")

        print()
        print("No se realizará ninguna modificación.")
        return 1

    image_source_name = f"images_{source.stem}"
    image_source = PENDING_DIR / image_source_name

    if not image_source.exists():
        raise FileNotFoundError(
            f"No existe la carpeta de imágenes esperada: {image_source}"
        )

    if destination_post.exists():
        raise FileExistsError(
            f"El destino ya existe: {destination_post}"
        )

    if destination_images.exists():
        raise FileExistsError(
            f"La carpeta de imágenes destino ya existe: {destination_images}"
        )

    # Crear directorios destino.
    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    # Actualizar fecha.
    new_text = update_front_matter(
        original_text,
        datetime_string,
    )

    # Actualizar únicamente las rutas que apuntan a la carpeta de imágenes
    # del propio artículo.
    new_text = update_image_paths(
        new_text,
        f"{date_string}-{slug}",
    )

    # Copiar primero las imágenes.
    shutil.copytree(
        image_source,
        destination_images,
    )

    try:
        # Escribir el nuevo post.
        destination_post.write_text(
            new_text,
            encoding="utf-8",
        )

        # Solo después de haber creado correctamente los destinos,
        # eliminamos el contenido pendiente.
        source.unlink()
        shutil.rmtree(image_source)

    except Exception:
        # Intentar limpiar si algo falla durante la operación.
        if destination_post.exists():
            destination_post.unlink()

        if destination_images.exists():
            shutil.rmtree(destination_images)

        raise

    print()
    print("========================================")
    print("PUBLICACIÓN PREPARADA CORRECTAMENTE")
    print("========================================")
    print(f"Post: {destination_post}")
    print(f"Imágenes: {destination_images}")
    print()
    print("El artículo ya no está en _pending/.")
    print("El siguiente paso será comprobar el build y GitHub Pages.")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print()
        print(f"ERROR: {exc}")
        sys.exit(1)
