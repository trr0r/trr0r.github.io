#!/usr/bin/env python3

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import random
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

    match = re.match(
        r"^---\s*\n(.*?)\n---\s*\n",
        text,
        re.DOTALL,
    )

    if not match:
        raise ValueError(
            f"{path.name}: front matter inválido. "
            "Debe comenzar y terminar exactamente con ---"
        )

    front_matter = match.group(1)

    title_match = re.search(
        r'^title:\s*["\']?(.*?)["\']?\s*$',
        front_matter,
        re.MULTILINE,
    )

    if not title_match:
        raise ValueError(
            f"{path.name}: no contiene 'title:' en el front matter"
        )

    title = title_match.group(1).strip().strip('"').strip("'")

    if not title:
        raise ValueError(
            f"{path.name}: el título está vacío"
        )

    return text, title


def update_front_matter(text: str, new_date: str) -> str:
    updated = re.sub(
        r"^date:\s*.*$",
        f"date: {new_date}",
        text,
        count=1,
        flags=re.MULTILINE,
    )

    if updated == text:
        raise ValueError(
            "El artículo no contiene un campo 'date:' válido"
        )

    return updated


def update_image_paths(text: str, new_image_dir: str) -> str:
    pattern = (
        r"(\.\./assets/images/posts/)"
        r"(\d{4}-\d{2}-\d{2}-[^/\s)>\"]+)"
        r"(/)"
    )

    return re.sub(
        pattern,
        rf"\g<1>{new_image_dir}\3",
        text,
    )


def main():
    if not PENDING_DIR.exists():
        print("No existe _pending/. No hay nada que publicar.")
        return 0

    # Ordenamos únicamente para que el conjunto de candidatos
    # sea determinista antes de aplicar la selección aleatoria.
    pending_posts = sorted(
        PENDING_DIR.glob("*.md"),
        key=lambda path: path.name.lower(),
    )

    if not pending_posts:
        print("No hay artículos pendientes de publicación.")
        print("No se realizará ninguna modificación.")
        return 0

    # Publicar exactamente un artículo aleatorio por ejecución.
    source = random.choice(pending_posts)

    print("========================================")
    print("PUBLICACIÓN DIARIA")
    print("========================================")
    print(
        f"Artículo seleccionado aleatoriamente: {source.name}"
    )

    original_text, title = read_front_matter(source)

    now = datetime.now(TIMEZONE)

    date_string = now.strftime("%Y-%m-%d")
    datetime_string = now.strftime("%Y-%m-%d %H:%M:%S %z")

    slug = slugify(title)

    if not slug:
        raise ValueError(
            f"No se puede generar un slug válido para '{title}'"
        )

    destination_post = POSTS_DIR / f"{date_string}-{slug}.md"
    destination_images = IMAGES_DIR / f"{date_string}-{slug}"

    print(f"Título: {title}")
    print(f"Slug: {slug}")
    print(f"Fecha de publicación: {datetime_string}")
    print(f"Post destino: {destination_post}")
    print(f"Imágenes destino: {destination_images}")

    # ----------------------------------------
    # PROTECCIÓN CONTRA DUPLICADOS
    # ----------------------------------------

    existing_posts = list(
        POSTS_DIR.glob(f"*-{slug}.md")
    )

    if existing_posts:
        print()
        print("ERROR: El artículo ya parece estar publicado.")
        print("Posts encontrados:")

        for post in existing_posts:
            print(f"  - {post}")

        print()
        print("No se realizará ninguna modificación.")
        return 1

    if destination_post.exists():
        raise FileExistsError(
            f"El destino ya existe: {destination_post}"
        )

    if destination_images.exists():
        raise FileExistsError(
            f"La carpeta de imágenes ya existe: {destination_images}"
        )

    # ----------------------------------------
    # COMPROBAR IMÁGENES
    # ----------------------------------------

    image_source = PENDING_DIR / f"images_{source.stem}"

    if not image_source.exists():
        raise FileNotFoundError(
            f"No existe la carpeta de imágenes esperada: "
            f"{image_source}"
        )

    if not image_source.is_dir():
        raise ValueError(
            f"La ruta de imágenes no es una carpeta: "
            f"{image_source}"
        )

    # ----------------------------------------
    # PREPARAR POST
    # ----------------------------------------

    new_text = update_front_matter(
        original_text,
        datetime_string,
    )

    new_text = update_image_paths(
        new_text,
        f"{date_string}-{slug}",
    )

    POSTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    IMAGES_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Copiamos primero las imágenes.
    shutil.copytree(
        image_source,
        destination_images,
    )

    try:
        destination_post.write_text(
            new_text,
            encoding="utf-8",
        )

        # Solo eliminamos _pending después de crear
        # correctamente post + imágenes.
        source.unlink()
        shutil.rmtree(image_source)

    except Exception:
        # Si algo falla, eliminamos los destinos creados
        # para no dejar una publicación incompleta.
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
    print("El artículo ha sido eliminado de _pending/.")
    print("El workflow hará commit y push.")
    print("========================================")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print()
        print(f"ERROR: {exc}")
        sys.exit(1)
