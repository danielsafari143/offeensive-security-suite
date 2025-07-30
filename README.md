# Python Offensive Security Suite

## Overview

This project is an **Educational Offensive Security Suite** designed to provide a hands-on learning experience with various cybersecurity and penetration testing techniques. It offers a modular set of tools and functionalities commonly used in reconnaissance, exploitation, and reverse shell scenarios, with the aim of helping students, security enthusiasts, and professionals understand how offensive security tools work under the hood.

---

## Features and Functionalities

### 1. Reconnaissance Module
- **Subnet Discovery:** Identify live hosts within a specified IP subnet using stealthy ICMP ping scans.
- **Port Scanning:** Conduct TCP connect scans with fallback to stealthy Nmap SYN scans to identify open and filtered ports.
- **Banner Grabbing:** Retrieve service banners from target hosts for footprinting.
- **DNS Lookup:** Perform DNS A record resolution for domain names.
- **WHOIS Lookup:** Query domain registration and ownership information.
- **Web Technology Fingerprinting:** Detect web server technologies and frameworks using `WhatWeb`.
- **Vulnerability Scanning:** Perform stealthy web vulnerability assessments using `Nikto`.
- **Installed Software Detection:** Use Nmap service/version detection and additional Kali Linux tools (like `nbtscan`) to gather software info.

### 2. Exploit Module
- Framework to develop and manage various exploit payloads targeting discovered vulnerabilities.
- **Note:** The full exploit code is **not included** in this repository to avoid misuse and potential harm. Users must develop and customize exploits responsibly in controlled environments.

### 3. Payload Module
- Payload creation and management for delivering malicious code such as reverse shells.
- **Note:** This module is **not provided** here to prevent misuse and possible illegal activities.

### 4. Reverse Shell Module
- Implements a TCP-based reverse shell server to interact with compromised clients.
- Supports commands such as file upload/download, taking screenshots and snapshots, and live video streaming.
- Provides a fully interactive shell interface.
- This module contains **complete functionality**, but **should be further modified** and tailored for real-world attacks.
- The author **assumes full responsibility for excluding parts of the code** related to payload and exploit creation to prevent misuse.

---

## Command-Line Interface (CLI) Commands

### Recon Shell Commands

| Command                 | Description                                                     | Example                            |
|-------------------------|-----------------------------------------------------------------|----------------------------------|
| `discover <subnet>`     | Discover live hosts in a subnet (ICMP ping scan)                | `discover 192.168.1.0/24`        |
| `scan <host> ports=...` | Scan specified TCP ports on a host                              | `scan 192.168.1.10 ports=22,80`  |
| `banner <host> <port>`  | Grab service banner from a host and port                        | `banner 192.168.1.10 80`          |
| `dns <domain>`          | Perform DNS A record lookup                                     | `dns example.com`                 |
| `whois <domain>`        | Perform WHOIS lookup                                           | `whois example.com`               |
| `detect <url>`          | Fingerprint web technologies using WhatWeb                    | `detect example.com`              |
| `vuln <url>`            | Run stealthy web vulnerability scan using Nikto               | `vuln example.com`                |
| `soft <host>`           | Detect installed software/services with Nmap & Kali tools      | `soft 192.168.1.10`               |
| `history`               | Show command history                                           | `history`                        |
| `help`                  | Show help message                                             | `help`                          |
| `exit`                  | Exit the recon shell                                          | `exit`                          |

### Reverse Shell Module Commands (Inside Interactive Shell)

| Command           | Description                                      |
|-------------------|------------------------------------------------|
| `upload <file>`   | Upload a local file to the remote client         |
| `download <file>` | Download a file from the remote client            |
| `snapshot`       | Receive a snapshot image from the client          |
| `screenshot`     | Receive a screenshot image from the client        |
| `stream`         | Start live video streaming from the client        |
| `exit`           | Terminate the reverse shell session                |
| *Any shell command* | Executes on the remote machine                     |

---

## Important Disclaimer

**This project is strictly for educational and research purposes only.**

- Some components intentionally contain **misconfigurations** and **security weaknesses** to serve as practical learning exercises.
- The author **explicitly disclaims any responsibility** for misuse of this software.
- **Do NOT use this software against any network, system, or target without explicit legal authorization.**
- Modifying or deploying this code against unauthorized targets is illegal and unethical.
- Users assume full responsibility for their actions.

---

## Getting Started

1. Clone the repository.
2. Install dependencies from `requirements.txt` (recommended in a virtual environment).
3. **It is strongly recommended to run this suite on Kali Linux or similar penetration testing Linux distributions** where all dependencies and tools (like Nmap, Nikto, WhatWeb) are readily available.
4. Use the provided CLI tools and modules to practice offensive security techniques in a controlled and authorized environment.
5. Refer to the included documentation and comments for guidance.

---

## Contribution & Support

Contributions and suggestions are welcome, but please ensure all usage aligns with legal and ethical standards.

---

## Contact

For questions or educational collaboration, please reach out responsibly.

---

*Stay ethical. Stay safe.*
