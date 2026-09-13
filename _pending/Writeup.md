---
title: "Writeup"
date: 2025-05-29 16:41:52 +0200
categories: writeups HackTheBox
tags: joomla cve rce dbenum infoleak máquina pathhijacking linux
description: Writeup de la máquina Writeup de Hackthebox.
image: ../assets/images/posts/logos/hackthebox.png
---
## Reconocimiento

En primer lugar, debemos desplegar la máquina para poder obtener la **Dirección IP** todo ello desde la web de **HackTheBox** y luego desde la **terminal** debemos conectarnos a la VPN usando el fichero correspondiente de la siguiente forma:

```bash
openvpn lab_trr0r.opvn
```

Después le lanzaremos un **ping** para ver si se encuentra activa dicha máquina, además de ver si acepta la traza **ICM**. Comprobamos que efectivamente nos devuelve el paquete que le enviamos por lo que acepta la traza **ICMP**, gracias al **ttl** podremos saber si se trata de una máquina **Linux (TTL 64 )** y **Windows (TTL 128)**, y vemos que se trata de una máquina **Linux** pues cuenta con **TTL** próximo a 64 (**63**), además gracias al script ****whichSystem.py**** podremos conocer dicha información.

![](<../assets/images/posts/2025-05-29-writeup/Pasted image 20241229223946.png>)

> El motivo por el cual el **TTL** es de **63** es porque el paquete pasa por unos intermediarios (routers) antes de llegar a su destino (máquina atacante). Esto podemos comprobarlo con el comando `ping -c 1 -R 10.10.10.138`.
### Nmap

En segundo lugar, realizaremos un escaneo usando **Nmap** para ver que puertos de la máquina víctima se encuentra abiertos.

```bash
nmap -p- --open --min-rate 5000 -sS -v -Pn -n 10.10.10.138 -oG allPorts
```

Observamos como nos reporta que se encuentran abiertos los puertos **22 y 80**.

![](<../assets/images/posts/2025-05-29-writeup/Pasted image 20241229224320.png>)

Ahora, gracias a la utilidad **getPorts** definida en nuestra **.zshrc** podremos copiarnos cómodamente todos los puerto abiertos de la máquina víctima a nuestra **clipboard**.

A continuación, volveremos a realizar un escaneo con **Nmap**, pero esta vez se trata de un escaneo más exhaustivo pues lanzaremos unos script básicos de reconocimiento, además de que nos intente reportar la versión y servicio que corre para cada puerto.

```bash
nmap -p22,80 -sCV 10.10.10.138 -oN targeted
```

Observamos que en la captura de **Nmap** lo único que realmente parece interesante es que el página web esta accesible el **robots.txt**

![](<../assets/images/posts/2025-05-29-writeup/Pasted image 20241229224412.png>)
___
## Explotación

Al meternos a la página web veremos como nos está advirtiendo de que se está baneando a los hosts que hagan muchas peticiones para evitar un ataque DoS por lo que podremos realizar fuzzing con **Gobuster** o cualquier otra herramienta.

![](<../assets/images/posts/2025-05-29-writeup/Pasted image 20241229224853.png>)

Nos dirigiremos al **robots.txt** que habíamos descubierto en el escaneo realizado con **Nmap** y veremos como se está filtrando una ruta (**/writeup**).

![](<../assets/images/posts/2025-05-29-writeup/Pasted image 20241229225055.png>)

Al acceder a dicha ruta no veremos nada interesante:

![](<../assets/images/posts/2025-05-29-writeup/Pasted image 20241229225206.png>)

En cambio si miramos el código fuente descubriremos que estamos ante un gestor de contenido conocido como **CMS Made Simple**:

![](<../assets/images/posts/2025-05-29-writeup/Pasted image 20241229225729.png>)

Usaremos **searchsploit** vía web para buscar por exploits que afecten a dicho gestor de contenido y además, debemos de buscar por alguna versión que haya salido en **2019**, hemos llegado a esta conclusión gracias a la fecha que aparece en la firma del Copyright.

Veremos que existe un exploit relacionado con una **SQL Injection** basada en tiempo (**Inyección SQL basada en tiempo**) que salió en **2019**.

![](<../assets/images/posts/2025-05-29-writeup/Pasted image 20241229230535.png>)

Gracias a **searchsploit** nos descargaremos dicho exploit (`searhsploit -m php/webapps/46635.py`), lo ejecutaremos con **python2** y nos daremos cuenta de los parámetros que hemos de pasarle:

![](<../assets/images/posts/2025-05-29-writeup/Pasted image 20241229231339.png>)

Seguidamente ejecutaremos el exploit de la siguiente forma:

```bash
python2 cms_sqlinjection.py -u http://10.10.10.138/writeup/
```

A partir del exploit conseguiremos obtener información valiosa así como un nombre de usuario y una contraseña cifrada en **MD5**, y además contamos con el **Salt** para dicha contraseña.

![](<../assets/images/posts/2025-05-29-writeup/Pasted image 20241229232729.png>)

En este punto lo que debemos de hacer es descifrar dicha contraseña para ello en primer lugar debemos de identificar el tipo de hash y estaremos ante estos dos (**Hash mode \#10** y **Hash mode \#20**):

> Destacar es posible crackear la contraseña desde el propio script pero el ordenador se peta bastante en el proceso de descifrar. También podíamos haber usado **johntheripper** pero en este caso no nos funcionará como hemos de esperar.

![](<../assets/images/posts/2025-05-29-writeup/Pasted image 20241229233707.png>)

Como no podemos saber con que tipo de hash quedarnos probaremos con las dos posibilidades y nos quedaremos con el que mejor resultados nos dé. 

En primer lugar, comenzaremos el **hash mode \#10** para ello debemos de ejecutar la siguiente instrución:

```bash
hashcat -m 10 -a 0 hash /usr/share/wordlists/rockyou.txt -o cracked.txt
```

Observamos que con el primer tipo de **hash** no tendremos buenos resultados ya que no ha encontrado ninguna contraseña válida, tal y como podemos ver la captura de pantalla:

![](<../assets/images/posts/2025-05-29-writeup/Pasted image 20241229234443.png>)

Por lo que ahora pasaremos a probar con el segundo tipo de hash (**20**), para ello lo único que tenemos que cambiar respecto al comando anterior es el número del parámetro `-m` el cual hace referencia el hash mode, en definitiva ejecutaremos el siguiente comando:

```bash
hashcat -m 20 -a 0 hash /usr/share/wordlists/rockyou.txt
```

Observamos que con este tipo de hash si que nos encuentra una contraseña (**raykayjay9**):

![](<../assets/images/posts/2025-05-29-writeup/Pasted image 20241229234653.png>)

Una vez que tenemos la contraseña crackeada (**raykayjay9**) pasaremos a autenticarnos por **ssh** con el nombre de usuario (**jkr**) encontrado gracias a la **SQL Injection**, para ello ejecutaremos el siguiente comando:

```bash
ssh jkr@10.10.10.138
```

Observamos que conseguimos conectarnos como el usuario **jkr** satisfactoriamente tal y como vemos a continuación:

![](<../assets/images/posts/2025-05-29-writeup/Pasted image 20241229235122.png>)
___
## Escalada de privilegios 

Como nos hemos conectado por **ssh** no hace falta hacer un **Tratamiento de la TTY**, lo único que debemos de hacer es un `export TERM=xterm` para que nos funcione el <kbd>CTRL</kbd>+<kbd>L</kbd>.

Como en todas las buscaremos alguna forma de elevar nuestros privilegios de la misma forma (**Sudoers**, **SUID**) pero no tendremos éxito. 

Al mirar en los grupos que estamos (`id`) nos daremos cuenta que hay algo poco habital, y es la presencia en el grupo **staff**. En este punto lo que haremos será buscar por ficheros y directorios que como grupo propietario figure **staff** para ello ejecutaremos el siguiente comando:

```bash
find / -group staff 2>/dev/null
```

Tal y como vemos a continuación nos daremos cuenta que el grupo **staff** es grupo propietario de **/usr/local**:

![](<../assets/images/posts/2025-05-29-writeup/Pasted image 20241229235627.png>)

Lo que más nos llama la atención de la anterior captura es que tenemos capacidad de escritura en dichos directorios, tal y como vemos a continuación:

![](<../assets/images/posts/2025-05-29-writeup/Pasted image 20241230000433.png>)

En este punto lo que haremos será **transferirnos** **pspy** a la máquina víctima para buscar algún binario que se esté ejecutando y así poder abusar de nuestros privilegios sobre el directorio **/user/local/\**** .

Observaremos que no se está ejecutando ningún binario en segundo plano del cual podamos abusar:

![](<../assets/images/posts/2025-05-29-writeup/Pasted image 20241230000831.png>)

Desde otra terminal nos conectaremos por **ssh** y veremos un proceso en segundo plano un tanto inusual gracias a la herramienta **pspy**. 

En definitiva, lo que estamos viendo en la captura es que cuando nos conectamos a través **ssh** la variable de entorno **PATH** se redefine y como primeras rutas del se encuentran los **directorios** sobre los que nosotros casualmente tenemos capacidad de **escritura**, además vemos que se está ejecutando un script llamado **run-parts** y todo esto está siendo ejecutado por el **root** (**0**).

![](<../assets/images/posts/2025-05-29-writeup/Pasted image 20241230001041.png>)

Una vez tenemos claro lo que está pasando por detrás cuando nos conectamos a través de **ssh**, debemos de crearnos un script con el nombre **run-parts** el cual asigne permiso **SUID** a la bash, en definitiva lo que debemos de hacer es lo siguiente:

![](<../assets/images/posts/2025-05-29-writeup/Pasted image 20241230001748.png>)

Desde otra terminal nos conectarnos por **ssh** y veremos como la bash tiene permiso **SUID** por lo que nos lanzaremos una **bash** privilegiada (`bash -p`) y nuestro **efective user id** será **root**.

![](<../assets/images/posts/2025-05-29-writeup/Pasted image 20241230002544.png>)