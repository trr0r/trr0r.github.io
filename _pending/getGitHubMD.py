#!/usr/bin/env python3

# Author: Álvaro Bernal (aka. trr0r)

import sys,re,os,shutil, pytz
from colorama import init
from termcolor import colored
from datetime import datetime
from fuzzywuzzy import fuzz

# Variables globales
# Especificamos la carpeta donde están las imágenes
image_folder = "C://Users//Alvaro//OneDrive2//Docus//hack4u//Obisidian-Hack//images"
# Especificamos la categorías que tendrá nuestro fichero markdown, normalmente será writeups + <nombre-máquina>
cathegories = "writeups "
# Especifiamos el encoding para evitar problemas a lo hora de leer el fichero MD
encoding = "utf-8"

# Change this if your timezone is different
time_zone = pytz.timezone("Europe/Madrid")

# Activamos los colores para la terminal de Windows (cmd)
init()

# Obtenemos el nombre del fichero markdown, es decir el argumento
def get_argument():
    if (len(sys.argv) != 3):
        print(colored(f"\n[+] Uso:", 'blue'))
        print(colored(f"\n\tpython3 getImagesMD.py \"C://users//desktop//prueba.md\" thehackerslabs\n", 'blue'))
        sys.exit(1)
    else:
        return sys.argv[1], sys.argv[2]

# Comprobamos si el fichero markdown, es un fichero markdown
def is_md_file(md_file):

    if (os.name == "nt"):
        regex = r'[\w\s]+.md$'
    else:
        regex = r'[\w\s]+.md$'

    result = re.search(regex, md_file)

    if not result:
        print(colored("\n[!] No es un archivo de Markdown.\n", 'red'))
        sys.exit(1)

# Comprobaremos si el fichero markdown existe
def check_file_exists(md_file):

    if not os.path.isfile(md_file):
        print(colored("\n[!] El archivo no existe.\n", 'red'))
        sys.exit(1)

# Comprobamos si el directorio que conteniene todas las imágenes existe
def check_directory_exists(image_folder):

    if image_folder == "":
        print(colored("\n[!] Debes de establecer la ruta donde están las imágenes\n",'red'))
        sys.exit(1)

    if not os.path.isdir(image_folder):
        print(colored("\n[!] La carpeta de imágenes no existe.\n", 'red'))
        sys.exit(1)

# Obtenemos las imagenes que hay en el archivo markdown
def get_images_url(md_file):

    regex = r"/(Pasted image \d{14}\.(?:jpg|png|jpeg))"

    with open(md_file, "r", encoding=encoding) as f:
        content_md = f.read()

    images = re.findall(regex, content_md)

    if not images:
        print(colored("\n[!] Este archivo no contiene imágenes.\n", 'red'))
        sys.exit(1)

    return images

# Creamos una carpeta que contendrá las imágenes
def create_folder_new_images(md_file):
    mdFileName = re.findall(r'([\w\s]+)(?:.md)$', md_file)[0]

    newFolder = f"images_{mdFileName}"
    newFolder = newFolder.replace(" ", "")

    if os.path.exists(newFolder):
        shutil.rmtree(newFolder)

    os.makedirs(newFolder)
    return newFolder

# Obtenemos las imagenes y las copiamos en una carpeta
def get_and_copy_images(images, pathImages, md_file):

    folder = create_folder_new_images(md_file)

    imagesFolder = os.listdir(pathImages)

    images = [f"{pathImages}/{image}" for image in imagesFolder if image in images]

    [shutil.copy(image, folder) for image in images]

    print(colored(f"\n[+] Imágenes copiadas correctamente en {folder}\n",'green'))

# Sustituimos los links por su nombre en negrita
def sub_md_links(md_file):

    regex = r"\[(.*?)\]\(<(?!.*images).*?>\)"

    with open(md_file, "r", encoding=encoding) as f:
        content_md = f.read()

    md_links = re.findall(regex, content_md)

    content_md = re.sub(regex, r"**\1**", content_md)

    with open(md_file, "w", encoding=encoding) as f:
        f.write(content_md)

# Eliminamos la negrita de los headers (encabezados)
def remove_strong_headers(md_file):

    regex = r"(^#+\s.*?)\*\*(.*?)\*\*(.*$)"  # Captura el texto antes, dentro y después de **

    with open(md_file, "r", encoding=encoding) as f:
        content_md = f.read()

    content_md = re.sub(regex, r"\1\2\3", content_md, flags=re.MULTILINE)

    with open(md_file, "w", encoding=encoding) as f:
        f.write(content_md)

# Obtenemos el nombre de la máquina
def get_file_name(md_file):
    return re.sub(r"^(.*).md$", r"\1",md_file)

# Añadimos las propiedades del fichero (fecha, nombre, tags, categorías, image)
def add_properties(md_file, platform_input):
    global cathegories

    platform, logo_path = get_logo_path(platform_input)

    tags = get_tags(md_file)

    if logo_path == "" and platform == "":
        print(colored(f"\n[!] La plataforma {platform_input} no está contemplada\n",'red'))
        sys.exit(1)

    date = datetime.now(time_zone).strftime("%Y-%m-%d %H:%M:%S %z") # Obtenemos el formato de fecha correcto
    name = get_file_name(md_file)
    cathegories += platform # Establecemos las categorías correspondientes
    platform = platform.lower() # Convertimos el nombre de la plataforma a minúscula

    properties = f"""---
title: "{name}"
date: {date}
categories: {cathegories}
tags: {tags}
description: Writeup de la máquina {name} de {platform.capitalize()}.
image: {logo_path}
---"""

    sub_tags(md_file, properties)

    print(colored("[+] Formato Markdown para GitHub Pages generado correctamente\n",'green'))
    print(colored(properties + "\n", 'blue'))

# Obtenemos la ruta donde está almacenado el logo
def get_logo_path(platform):
    # Añadir aquí más plataformas si es necesario
    platforms = {
        "BugBountyLabs" : "../assets/images/posts/logos/bugbountylabs.jpeg", 
        "TheHackersLabs": "../assets/images/posts/logos/thehackerlabs.png", 
        "VulnHub": "../assets/images/posts/logos/vulnhub.jpg",
        "DockerLabs" : "../assets/images/posts/logos/dockerlabs.png", 
        "HackTheBox": "../assets/images/posts/logos/hackthebox.png"}

    for platform_correct, path in platforms.items():
        if platform_correct == platform:
            return platform_correct, path

    return "", ""

# Obtenemos los tags presente en el fichero markdown
def get_tags(md_file):

    with open(md_file, "r", encoding=encoding) as f:
        content_md = f.read()

    match = re.search(r"- Tags: (.*)", content_md)

    if match:
        tags = re.findall(r"#(\w+)", match.group(1))
        tags = " ".join(tag for tag in tags)
        return tags
    return []

# Eliminamos el encabezado "- Tags:" original
def sub_tags(md_file, properties):

    with open(md_file, "r", encoding=encoding) as f:
        content_md = f.read()

    content_md = re.sub(r"___\s- Tags: .*?\s___", properties, content_md)

    with open(md_file, "w", encoding=encoding) as f:
        f.write(content_md)

# Sustituimos el link de las imágenes por su ruta correcta
def sub_images_links(md_file):

    regex = r"<.*\/(Pasted image \d{14}\.(?:jpg|png|jpeg))>"

    with open(md_file, "r", encoding=encoding) as f:
        content_md = f.read()

    date = datetime.now().strftime('%Y-%m-%d')
    name = get_file_name(md_file)
    new_image_path = f"<../assets/images/posts/{date}-{name.lower()}/"

    content_md = re.sub(regex, new_image_path + r"\1>", content_md)

    with open(md_file, "w", encoding=encoding) as f:
        f.write(content_md)

if __name__ == '__main__':
    md_file, platform = get_argument() # Obtenemos los argumetnos
    is_md_file(md_file) # Comprobamos si es un archivo de markdown

    check_file_exists(md_file) # Comprobamos si el fichero markdown existe
    check_directory_exists(image_folder) # Comprobamos si el directorio de las imágenes existe

    images = get_images_url(md_file) # Obtenemos los nombres de las imagenes del fichero markdown
    get_and_copy_images(images, image_folder, md_file) # Copiamos las imágenes del fichero markdown en una nueva carpeta

    sub_md_links(md_file) # Sustituimos los enlaces a archivos externos por únicamente el nombre del archivo
    sub_images_links(md_file) # Actualizamos la ruta de las imágenes
    remove_strong_headers(md_file) # Quitamos la negrita los encabezados (#, ##, ...)

    add_properties(md_file, platform) # Añadimos las propiedades (nombre, tags, cathegories, image_path, description)
