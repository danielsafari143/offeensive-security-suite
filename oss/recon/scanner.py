# recon/scanner.py

import socket
import ipaddress
import whois
import dns.resolver
import http.client
from urllib.parse import urlparse
import subprocess
import random
import time
from recon.utils import print_info, print_success, print_error


def discover_subnet(subnet):
    """Discover live hosts using stealthy Nmap TCP SYN ping instead of noisy ICMP."""
    print_info(f"Stealthily discovering hosts in {subnet} using Nmap TCP SYN ping")
    live_hosts = []
    try:
        # Use Nmap with TCP SYN ping (-PS) on common ports, no ICMP
        result = subprocess.run(
            ["nmap", "-sn", "-PS22,80,443", "-T2", "-n", "-oG", "-", subnet],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0:
            print_error(f"Nmap ping scan failed: {result.stderr.strip()}")
            return []

        # Parse grepable output for 'Up' hosts
        for line in result.stdout.splitlines():
            if "Status: Up" in line:
                parts = line.split()
                if parts:
                    ip = parts[1]
                    print_success(f"Host found: {ip}")
                    live_hosts.append(ip)
    except subprocess.TimeoutExpired:
        print_error("Nmap ping scan timed out.")
    except Exception as e:
        print_error(f"Error running Nmap ping scan: {e}")
    return live_hosts


def scan_ports(host, ports):
    """Stealthy port scan using Nmap with slow scan delay and multiple scan types."""
    print_info(f"Stealth scanning ports on {host}")
    open_ports = []

    ports_str = ",".join(map(str, ports))

    # Use multiple stealth scan types with delays and low rate (-T2 slow)
    try:
        # SYN scan with delay and max rate limit
        cmd_syn = [
            "nmap",
            "-sS",            # SYN scan (stealth)
            "-p", ports_str,
            "--scan-delay", "500ms",  # 0.5s delay between probes
            "--max-rate", "10",       # max 10 packets/sec
            "-T2",                   # polite timing template
            "-Pn",                   # no ping (host assumed up)
            "-n",                    # no DNS resolution
            host
        ]
        print_info(f"Running SYN scan: {' '.join(cmd_syn)}")
        result_syn = subprocess.run(cmd_syn, capture_output=True, text=True, timeout=120)

        # Parse results
        for line in result_syn.stdout.splitlines():
            if "/tcp" in line and "open" in line:
                port_num = int(line.split("/")[0])
                if port_num not in open_ports:
                    print_success(f"Port {port_num} open on {host} (SYN scan)")
                    open_ports.append(port_num)

        # If no ports found, try NULL scan (more stealthy but less reliable)
        if not open_ports:
            cmd_null = [
                "nmap",
                "-sN",            # NULL scan (no flags)
                "-p", ports_str,
                "--scan-delay", "500ms",
                "--max-rate", "10",
                "-T2",
                "-Pn",
                "-n",
                host
            ]
            print_info(f"Running NULL scan: {' '.join(cmd_null)}")
            result_null = subprocess.run(cmd_null, capture_output=True, text=True, timeout=120)

            for line in result_null.stdout.splitlines():
                if "/tcp" in line and "open" in line:
                    port_num = int(line.split("/")[0])
                    if port_num not in open_ports:
                        print_success(f"Port {port_num} open on {host} (NULL scan)")
                        open_ports.append(port_num)

    except subprocess.TimeoutExpired:
        print_error("Nmap stealth scan timed out.")
    except Exception as e:
        print_error(f"Error running stealth port scan: {e}")

    return open_ports


def grab_banner(host, port):
    """Grab banner with minimal traffic and delay to avoid detection."""
    print_info(f"Stealthily grabbing banner from {host}:{port}")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(3)
            s.connect((host, port))
            # For HTTP ports, send minimal HEAD request
            if port in (80, 8080, 443):
                s.sendall(b"HEAD / HTTP/1.1\r\nHost: %b\r\n\r\n" % host.encode())
            else:
                # Just send newline for banner grabbing on other services
                s.sendall(b"\r\n")
            # Small recv buffer to minimize traffic
            banner = s.recv(512).decode(errors='ignore')
            print_success(f"Banner from {host}:{port}:\n{banner.strip()}")
            return banner
    except Exception as e:
        print_error(f"Banner grab failed: {e}")
        return None


def dns_lookup(domain):
    """Perform DNS lookup with retries and minimal delay."""
    try:
        print_info(f"Stealthy DNS lookup for {domain}")
        result = dns.resolver.resolve(domain, 'A')
        ips = [str(ip) for ip in result]
        for ip in ips:
            print_success(f"{domain} => {ip}")
        return ips
    except Exception as e:
        print_error(f"DNS error: {e}")
        return []


def whois_lookup(domain):
    """Perform WHOIS lookup (no stealth needed)."""
    try:
        print_info(f"WHOIS lookup for {domain}")
        info = whois.whois(domain)
        print_success(str(info))
        return str(info)
    except Exception as e:
        print_error(f"WHOIS error: {e}")
        return str(e)


def detect_web_technologies(url):
    """Use WhatWeb with stealth flags to fingerprint web technologies."""
    print_info(f"Stealth detecting web technologies at {url} using WhatWeb")

    try:
        # WhatWeb has --random-agent and --delay options for stealth
        result = subprocess.run(
            ["whatweb", url, "--quiet", "--random-agent", "--delay", "3"],
            capture_output=True,
            text=True,
            timeout=45
        )
        if result.returncode != 0:
            print_error(f"WhatWeb failed: {result.stderr.strip()}")
            return []

        output = result.stdout.strip()
        if output:
            print_success(output)
            return [output]
        else:
            print_info("No web technologies detected by WhatWeb.")
            return []

    except subprocess.TimeoutExpired:
        print_error("WhatWeb scan timed out.")
        return []
    except Exception as e:
        print_error(f"Error running WhatWeb: {e}")
        return []


def web_vulnerability_scan(url):
    """Run Nikto with delay to avoid detection."""
    print_info(f"Running stealthy Nikto web vulnerability scan on {url}")

    try:
        result = subprocess.run(
            ["nikto", "-h", url, "-delay", "5"],
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode != 0:
            print_error(f"Nikto scan failed: {result.stderr.strip()}")
            return []

        print_success("Nikto Scan Results:")
        print(result.stdout)
        return result.stdout

    except subprocess.TimeoutExpired:
        print_error("Nikto scan timed out.")
        return []
    except Exception as e:
        print_error(f"Error running Nikto: {e}")
        return []


def get_installed_software(host):
    """Use Nmap version detection with stealth options, plus optional nbtscan."""
    print_info(f"Running stealthy Nmap version detection on {host} (this may take a while)...")

    try:
        nmap_cmd = [
            "nmap",
            "-sV",
            "-Pn",
            "-p-",
            "--scan-delay", "300ms",    # 0.3s delay between probes
            "--max-rate", "10",         # max 10 packets per second
            "-T2",                     # polite timing
            host,
            "--open"
        ]

        result = subprocess.run(nmap_cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            print_error(f"Nmap scan failed: {result.stderr.strip()}")
            return []

        software_list = []
        print_info(f"Parsing Nmap output for detected services on {host}...")

        for line in result.stdout.splitlines():
            if "/tcp" in line and ("open" in line or "filtered" in line):
                print_success(line.strip())
                software_list.append(line.strip())

        if not software_list:
            print_info("No services detected or Nmap output could not be parsed.")

        # Optional NetBIOS enumeration (slow, stealthy)
        try:
            print_info(f"Running nbtscan on {host} for NetBIOS info")
            nbtscan_result = subprocess.run(
                ["nbtscan", "-v", host],
                capture_output=True,
                text=True,
                timeout=30
            )
            if nbtscan_result.returncode == 0:
                print_success(nbtscan_result.stdout.strip())
            else:
                print_info("No NetBIOS info found or nbtscan failed.")
        except Exception as e:
            print_error(f"Error running nbtscan: {e}")

        return software_list

    except subprocess.TimeoutExpired:
        print_error("Nmap scan timed out.")
        return []
    except Exception as e:
        print_error(f"Error running Nmap: {e}")
        return []
