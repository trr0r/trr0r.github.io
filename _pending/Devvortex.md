---
title: "Devvortex"
date: 2025-05-29 16:41:29 +0200
categories: writeups HackTheBox
tags: joomla cve rce dbenum infoleak máquina apport linux sudoers
description: Writeup de la máquina Devvortex de Hackthebox.
image: ../assets/images/posts/logos/hackthebox.png
---
## Reconocimiento

En primer lugar, debemos desplegar la máquina para poder obtener la **Dirección IP** todo ello desde la web de **HackTheBox** y luego desde la **terminal** debemos conectarnos a la VPN usando el fichero correspondiente de la siguiente forma:

```bash
openvpn lab_trr0r.opvn
```

Después le lanzaremos un **ping** para ver si se encuentra activa dicha máquina, además de ver si acepta la traza **ICM**. Comprobamos que efectivamente nos devuelve el paquete que le enviamos por lo que acepta la traza **ICMP**, gracias al **ttl** podremos saber si se trata de una máquina **Linux (TTL 64 )** y **Windows (TTL 128)**, y vemos que se trata de una máquina **Linux** pues cuenta con **TTL** próximo a 64 (**63**), además gracias al script ****whichSystem.py**** podremos conocer dicha información.

![](<../assets/images/posts/2025-05-29-devvortex/Pasted image 20241227200803.png>)

> El motivo por el cual el **TTL** es de **63** es porque el paquete pasa por unos intermediarios (routers) antes de llegar a su destino (máquina atacante). Esto podemos comprobarlo con el comando `ping -c 1 -R 10.10.11.242`.
### Nmap

En segundo lugar, realizaremos un escaneo usando **Nmap** para ver que puertos de la máquina víctima se encuentra abiertos.

```bash
nmap -p- --open --min-rate 5000 -sS -v -Pn -n 10.10.11.242 -oG allPorts
```

Observamos como nos reporta que se encuentran abiertos los puertos **22 y 80**.

![](<../assets/images/posts/2025-05-29-devvortex/Pasted image 20241227200945.png>)

Ahora, gracias a la utilidad **getPorts** definida en nuestra **.zshrc** podremos copiarnos cómodamente todos los puerto abiertos de la máquina víctima a nuestra **clipboard**.

A continuación, volveremos a realizar un escaneo con **Nmap**, pero esta vez se trata de un escaneo más exhaustivo pues lanzaremos unos script básicos de reconocimiento, además de que nos intente reportar la versión y servicio que corre para cada puerto.

```bash
nmap -p22,80 -sCV 10.10.11.242 -oN targeted
```

Observamos que en la captura de **Nmap** no encontramos ninguna información relevante.

![](<../assets/images/posts/2025-05-29-devvortex/Pasted image 20241227201030.png>)
___
## Explotación

Al tener tan pocas opciones sabremos que la intrusión a la máquina irá a través de la página web alojada en puerto **80**. Al realizar un `whatweb` sobre la página web veremos que nos da un error el cual nos está indicando que es incapaz de redireccionar a la página `devvortex.htb`.

```bash
whatweb http://10.10.11.242
```

![](<../assets/images/posts/2025-05-29-devvortex/Pasted image 20241229131215.png>)

Para solucionar este problema tenemos que aplicar **Virtual Hosting** para ello abrimos el `/etc/hosts` y añadimos la siguiente línea: `10.10.11.242  devvortex.htb`.

Ahora veremos que al correr de nuevo el comando de `whatweb` sobre la página web no nos dará ningún error, al igual que si accedemos a través del navegador no tendremos ningún problema.

![](<../assets/images/posts/2025-05-29-devvortex/Pasted image 20241227205955.png>)

El aspecto de la página web es el siguiente, en primer lugar navegaremos por la página y como no vemos nada interesante realizaremos fuzzing de directorios con **Gobuster** o cualquier otra herramienta, aunque finalmente no encontraremos nada en la página web.

![](<../assets/images/posts/2025-05-29-devvortex/Pasted image 20241227205918.png>)

Como haciendo fuzzing de directorios no encontramos nada pasaremos a realizar fuzzing de subdominios usando **Wfuzz** de la siguiente forma:

```bash
wfuzz -c -u http://devvortex.htb -H 'Host: FUZZ.devvortex.htb' -w /usr/share/wordlists/SecLists/Discovery/DNS/subdomains-top1million-110000.txt -t 100 --hh 154
```

Observamos un subdominio 

![](<../assets/images/posts/2025-05-29-devvortex/Pasted image 20241227210313.png>)

Una vez hemos encontrado el subdominio volveremos a aplicar **Virtual Hosting** para ello abrimos el `/etc/hosts` y lo actualizamos a: `10.10.11.242  devvortex.htb dev.devvortex.htb`.

La página web alojada en el subdominio es simular a la del dominio principal.

![](<../assets/images/posts/2025-05-29-devvortex/Pasted image 20241227214442.png>)

Realizaremos fuzzing de directorios usando **Gobuster** gracias al siguiente comando:

```bash
gobuster dir -u http://dev.devvortex.htb/ -w /usr/share/wordlists/SecLists/Discovery/Web-Content/directory-list-2.3-medium.txt -x php,html,js,txt -t 100
```

Observamos que nos reporta un montón directorios:

![](<../assets/images/posts/2025-05-29-devvortex/Pasted image 20241227214634.png>)

Tras estar un rato navegando por ello nos damos cuenta que el fichero **README.txt** nos está indicando que estamos ante un **Joomla**.

![](<../assets/images/posts/2025-05-29-devvortex/Pasted image 20241227214653.png>)

Además si accedemos a la ruta **/administrator** veremos que efectivamente estamos ante un **Joomla**.

![](<../assets/images/posts/2025-05-29-devvortex/Pasted image 20241227214900.png>)

En primer lugar lo que debemos de hacer cuando estamos ante un **CMS** es conocer la versión de dicho **Gestor de Contenido**, en este caso para **Joomla** contamos con la herramienta **JoomlaScan** la cual nos reporta la versión y muchas cosas más.

> Para utilizar dicha herramienta nos clonaremos el siguiente repositorio: [joomscan](https://github.com/OWASP/joomscan).

Para ejecutar el script usaremos **perl** de la siguiente forma:

```bash
perl joomscan.pl -u http://dev.devvortex.htb
```

Observamos que nos detecta que el **Joomla** se encuentra en la versión **4.2.6**.

![](<../assets/images/posts/2025-05-29-devvortex/Pasted image 20241227215044.png>)

> Además en la ruta **/administrator/manifests/files/joomla.xml** también es posible ver la versión de **Joomla** tal y como se aprecia en la captura.
> 
> ![](<../assets/images/posts/2025-05-29-devvortex/Pasted image 20241227215910.png>)

Si buscamos por exploits en **searchsploit** veremos que no nos reporta ninguno por lo que pasaremos a buscar en internet.

![](<../assets/images/posts/2025-05-29-devvortex/Pasted image 20241227220138.png>)

Buscando en Google encontraremos muchos resultados relacionados con el **CVE-2023-23752** por lo que entraremos al segundo repositorio.

![](<../assets/images/posts/2025-05-29-devvortex/Pasted image 20241227220150.png>)

Una vez en el repositorio nos descargaremos el exploit de python con **wget** de la siguiente forma:

```bash
wget https://raw.githubusercontent.com/0xNahim/CVE-2023-23752/refs/heads/main/exploit.py
```

Ejecutaremos dicho exploit pasando la URL donde está alojado el **Joomla** tal y como se muestra a continuación:

```bash
python3 exploit.py -u http://dev.devvortex.htb
``` 

Observamos que nos reporta un nombre de **usuario** y una **contraseña** pertenecientes a una base de datos.

![](<../assets/images/posts/2025-05-29-devvortex/Pasted image 20241227220337.png>)

Si nos fijamos en el script lo único que se encarga de hacer es mirar la **Information Leakage** que se produce en estas dos rutas:

```bash
curl -s -X GET "http://dev.devvortex.htb/api/index.php/v1/users?public=true"
curl -s -X GET "http://dev.devvortex.htb/api/index.php/v1/config/application?public=true"
```

![](<../assets/images/posts/2025-05-29-devvortex/Pasted image 20241227222017.png>)

![](<../assets/images/posts/2025-05-29-devvortex/Pasted image 20241227221948.png>)

Probaremos a autenticarnos con las credenciales encontradas (**lewis:P4ntherg0t1n5r3c0n##**) en el panel de administrador de **Joomla** previamente encontrado.

![](<../assets/images/posts/2025-05-29-devvortex/Pasted image 20241227222126.png>)

Observamos que hemos podido logearnos correctamente por lo que ya estamos dentro del panel del administrador desde el cual debemos de ganar acceso a la máquina (debemos de usar una**webshell** lo más seguro). Para proceder con la **webshell** debemos dirigirnos a **System**.

![](<../assets/images/posts/2025-05-29-devvortex/Pasted image 20241227222243.png>)

Posteriormente le daremos a **Site Templates** y en la siguiente página le daremos clic sobre el único template que tenemos (**cassiopeia**).

![](<../assets/images/posts/2025-05-29-devvortex/Pasted image 20241227222503.png>)

Finalmente, debemos de crear una **webshell** para ello tenemos dos opciones:
 - Crear un **cmd.php** ya que al subir un **cmd.php** nos dará error.
 - Modificar un archivo sobre el cual tengamos permisos (**error.php**).

![](<../assets/images/posts/2025-05-29-devvortex/Pasted image 20241227222756.png>)

Creamos un archivo de nombre **cmd** y con la extensión **.php** el cual nos va a permitir tener una **webshell**.

![](<../assets/images/posts/2025-05-29-devvortex/Pasted image 20241227223238.png>)

Pasaremos a editar el archivo **cmd.php** añadiéndole el siguiente contenido y le daremos a **Save & Close**.

![](<../assets/images/posts/2025-05-29-devvortex/Pasted image 20241227223316.png>)

Accedemos a la ruta donde se ha creado el archivo (**/templates/cassiopeia/cmd.php**) y observamos que tenemos una **webshell** por lo que ahora lo que tenemos que hacer es enviarnos una **Reverse Shell**.

![](<../assets/images/posts/2025-05-29-devvortex/Pasted image 20241227223351.png>)

Poniéndonos en escucha con **NetCat** (`nc -nvlp 443`) observamos que recibimos correctamente la **Reverse Shell**.

![](<../assets/images/posts/2025-05-29-devvortex/Pasted image 20241227223949.png>)
___
## Escalada de privilegios

Una vez realizado el **Tratamiento de la TTY** podemos proceder con la escalada de privilegios, como en todas las máquina buscaremos los principales vectores para elevar nuestros privilegios como lo son **Sudoers** o **SUID** pero en está máquina la escalada no va por ahí. 

Como tenemos credenciales correspondientes a una base de datos (**lewis:P4ntherg0t1n5r3c0n##**) probaremos a autenticarnos de la siguiente forma:

```bash
mysql -ulewis -p
```

Observamos que hemos podido conectarnos correctamente.

![](<../assets/images/posts/2025-05-29-devvortex/Pasted image 20241227224821.png>)

Vemos que existe una base de datos llamada **joomla** y dentro de ella nos llama la atención la tabla **sd4fg_users**.

![](<../assets/images/posts/2025-05-29-devvortex/Pasted image 20241227225044.png>)

Nos quedaremos con el hash correspondiente al usuario **logan** e intentaremos romperlo.

![](<../assets/images/posts/2025-05-29-devvortex/Pasted image 20241227225325.png>)

> Nos quedaremos con el hash del usuario **logan** ya que dicho usuario existe en el sistema y la contraseña del usuario **lewis** ya la tenemos del **Information Leakage** anteriormente explotado.
> 
> ![](<../assets/images/posts/2025-05-29-devvortex/Pasted image 20241227225450.png>)

Existen varias formas de crackear el hash, vía terminal con **johntheripper** / **hashcat** o las alternativas en la web como [Crackstation](https://crackstation.net/) o [Hashes](https://hashes.com/en/decrypt/hash) 

En este caso nosotros usaremos la manera manual, identificando en primer lugar el tipo de hash y luego buscando en **hashcat --example-hashes** o en [Hashcat - example-hashes](https://hashcat.net/wiki/doku.php?id=example_hashes) el **modo** de hash asociado de dicho hash.

![](<../assets/images/posts/2025-05-29-devvortex/Pasted image 20241227225818.png>)

Una vez conocemos el modo (**3200**) ejecutaremos **hashcat** de la siguiente forma:

```bash
hashcat -m 3200 -a 0 -o cracked.txt hash /usr/share/wordlists/rockyou.txt
```

Al cabo de poco tiempo observamos como nos reporta que la contraseña crackeada es: **tequieromucho**:

![](<../assets/images/posts/2025-05-29-devvortex/Pasted image 20241227230149.png>)

Nos convertiremos en el usuario **logan**  satisfactoriamente con la contraseña crackeada: **tequieromucho**.

![](<../assets/images/posts/2025-05-29-devvortex/Pasted image 20241227230612.png>)

Mirando los permisos de **Sudoers** nos daremos cuenta que podemos ejecutar el binario **/usr/bin/apport-cli** como cualquier usuario por lo que la escalada final irá por aquí.

![](<../assets/images/posts/2025-05-29-devvortex/Pasted image 20241227230651.png>)

Tras investigar por internet nos daremos cuenta que dicha herramienta cuenta con una vulnerabilidad la cual nos permite colar comandos de igual forma que comando el **less** gracias al signo de **exclamación** (**!**).

![](<../assets/images/posts/2025-05-29-devvortex/Pasted image 20241227231201.png>)

Existen **3** principales formas de invocarnos una **/bin/bash** y convertirnos en **root** gracias al permiso de **Sudoers** en **apport-cli**.
### Crash Sleep

La primera de las formas consiste en crear un archivo **crash** intencionadamente para ello debemos de ejecutar un `sleep` en segundo plano: `sleep 20 &` y posteriormente matar dicho proceso con `-ABRT` o `-6` y así generar un core dump es decir un **.crash** tal y como vemos en la captura.

![](<../assets/images/posts/2025-05-29-devvortex/Pasted image 20241227232322.png>)

Posteriormente ejecutaremos la herramienta **apport-cli** como el usuario administrador pasándole el Path donde se encuentra el **crash** con la opción `-c`, en definitiva debemos de ejecutar el siguiente comando y nos saltará el **menú interactivo** para elegir la opción de **visualizar** el reporte (**V: View Report**) y así colar un comando:

```bash
sudo -u root /usr/bin/apport-cli -c /var/crash/_usr_bin_sleep.1000.crash 
```
### Con apport-cli

Con la segunda forma no necesitaremos generar ningún tipo de **crash** será todo con la herramienta **apport-cli**, en primer lugar lanzaremos la herramienta con el parámetro `-f`, es decir tal y como se observa a continuación:

```bash
sudo -u root apport-cli -f
```

Una vez ejecutado el anterior comando nos saltará el siguiente menú interactivo donde tendremos que escoger la primer opción, es decir escribir un **1**.

![](<../assets/images/posts/2025-05-29-devvortex/Pasted image 20241227233623.png>)

Tras el anterior menú interactivo nos volverá a saltar otro parecido pero en cambio en este tendremos que seleccionar la segunda opción (escribir un **2**), posteriormente debemos de pulsar cualquier letra, finalmente nos saltará el **menú interactivo** para elegir la opción de **visualizar** el reporte (**V: View Report**) y así colar un comando:

![](<../assets/images/posts/2025-05-29-devvortex/Pasted image 20241227233716.png>)

### Fake Data

Como última opción podemos crear un falso archivo **crash** ya que observamos que al pasarle un archivo que no es un **crash** nos dice que falta el campo **ProblemType**.

![](<../assets/images/posts/2025-05-29-devvortex/Pasted image 20241227234130.png>)

Nos crearemos un archivo **.crash** con dicho campo tal y como se aprecia en la captura de pantalla:

![](<../assets/images/posts/2025-05-29-devvortex/Pasted image 20241227234324.png>)

Finalmente, ejecutaremos el binario **/usr/bin/apport-cli** con el parámetro `-c` al igual que en el primer caso (**Crash Sleep**), en resumen lanzaremos la siguiente instrucción y ya entraremos en el **menú interactivo** donde podemos seleccionar la opción **V: View report**.

```bash
sudo -u root /usr/bin/apport-cli -c /tmp/test.crash 
```
### V: View report

Cuando consigamos que nos aparezca la opción **V: View report** debemos de seleccionarla pulsado la tecla <kbd>V</kbd>:

![](<../assets/images/posts/2025-05-29-devvortex/Pasted image 20241227233132.png>)

Posteriormente cuando la herramienta deje de sacar output por la pantalla escaparemos del visualizador del reporte gracias a la exclamación (**!**), es decir nos lanzaremos una **bash** con `!/bin/bash`.

![](<../assets/images/posts/2025-05-29-devvortex/Pasted image 20241227232853.png>)

Observamos que hemos conseguido convertirnos en el usuario **root** por lo que ya habríamos **pwneado** la máquina.

![](<../assets/images/posts/2025-05-29-devvortex/Pasted image 20241227233354.png>)