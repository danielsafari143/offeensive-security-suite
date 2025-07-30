import sys
from recon import scanner

HISTORY = []

def print_banner():
    print("\033[96m" + r"""
    ██████╗ ███████╗ ██████╗ ██████╗  ██████╗ ███╗   ██╗
    ██╔══██╗██╔════╝██╔════╝ ██╔══██╗██╔═══██╗████╗  ██║
    ██████╔╝█████╗  ██║  ███╗██████╔╝██║   ██║██╔██╗ ██║
    ██╔═══╝ ██╔══╝  ██║   ██║██╔═══╝ ██║   ██║██║╚██╗██║
    ██║     ███████╗╚██████╔╝██║     ╚██████╔╝██║ ╚████║
    ╚═╝     ╚══════╝ ╚═════╝ ╚═╝      ╚═════╝ ╚═╝  ╚═══╝
    Recon Shell - Offensive Recon Toolkit (Educational Use Only)
    \033[0m""")

def print_help():
    print("""
Commands:
  discover <subnet>                - Discover live hosts in a subnet (e.g., discover 192.168.1.0/24)
  scan <host> ports=22,80         - Scan specific ports on a host (e.g., scan 192.168.1.1 ports=22,80)
  banner <host> <port>            - Grab banner from a service (e.g., banner 192.168.1.1 80)
  dns <domain>                    - Perform DNS A record lookup (e.g., dns example.com)
  whois <domain>                  - Perform WHOIS lookup (e.g., whois example.com)
  detect <url>                    - Fingerprint web technologies on the given URL (e.g., detect example.com)
  vuln <url>                      - Run stealthy web vulnerability scan using Nikto (e.g., vuln example.com)
  soft <host>                     - Detect installed software on host using Nmap (e.g., soft 192.168.1.1)
  history                         - Show command history
  help                            - Show this help message
  exit                            - Exit the shell
""")

def main():
    print_banner()
    print_help()

    while True:
        try:
            cmd = input("recon> ").strip()
            if not cmd:
                continue

            HISTORY.append(cmd)

            if cmd.startswith("discover "):
                _, subnet = cmd.split(maxsplit=1)
                scanner.discover_subnet(subnet)

            elif cmd.startswith("scan "):
                parts = cmd.split()
                if len(parts) < 3:
                    print("[-] Usage: scan <host> ports=22,80")
                    continue
                host = parts[1]
                ports = []
                for part in parts[2:]:
                    if part.startswith("ports="):
                        ports = list(map(int, part.split("=")[1].split(",")))
                if ports:
                    scanner.scan_ports(host, ports)
                else:
                    print("[-] Usage: scan <host> ports=22,80")

            elif cmd.startswith("banner "):
                parts = cmd.split()
                if len(parts) == 3:
                    host = parts[1]
                    try:
                        port = int(parts[2])
                    except ValueError:
                        print("[-] Port must be a number.")
                        continue
                    scanner.grab_banner(host, port)
                else:
                    print("[-] Usage: banner <host> <port>")

            elif cmd.startswith("dns "):
                _, domain = cmd.split(maxsplit=1)
                scanner.dns_lookup(domain)

            elif cmd.startswith("whois "):
                _, domain = cmd.split(maxsplit=1)
                scanner.whois_lookup(domain)

            elif cmd.startswith("detect "):
                _, url = cmd.split(maxsplit=1)
                scanner.detect_web_technologies(url)

            elif cmd.startswith("vuln "):
                _, url = cmd.split(maxsplit=1)
                scanner.web_vulnerability_scan(url)

            elif cmd.startswith("soft "):
                _, host = cmd.split(maxsplit=1)
                scanner.get_installed_software(host)

            elif cmd == "history":
                print("Command History:")
                for i, h in enumerate(HISTORY, 1):
                    print(f"{i}. {h}")

            elif cmd == "help":
                print_help()

            elif cmd == "exit":
                print("[+] Exiting.")
                break

            else:
                print("[-] Unknown command.")
                print_help()

        except KeyboardInterrupt:
            print("\n[!] Interrupted.")
            break
        except Exception as e:
            print(f"[!] Error: {e}")

if __name__ == "__main__":
    main()
