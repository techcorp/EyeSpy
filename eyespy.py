#!/usr/bin/env python3
# EyeSpy - Network Camera Auditor
# Author: Muhammad Anas (IT & Cybersecurity)
# Description: Local network camera scanner + ONVIF info + HTML report

import os, sys, ipaddress, time, threading, queue, socket, json, argparse
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from rich.progress import Progress
from rich.panel import Panel
from rich import box

# Optional libraries
try:
    from wsdiscovery import WSDiscovery
    WS_DISCOVERY_AVAILABLE = True
except Exception:
    WS_DISCOVERY_AVAILABLE = False

try:
   # import miniupnpc
    MINIUPNPC_AVAILABLE = True
except Exception:
    MINIUPNPC_AVAILABLE = False


try:
    from onvif import ONVIFCamera
    ONVIF_AVAILABLE = True
except Exception:
    ONVIF_AVAILABLE = False

from jinja2 import Template

console = Console()

COMMON_PORTS = [80, 554, 8000, 8080, 8554, 5000]
CAM_KEYWORDS = ['camera', 'onvif', 'dvr', 'nvr', 'hikvision', 'dahua', 'axis', 'video', 'surveillance', 'ipcam']

BANNER = """[bold cyan]
 /$$$$$$$$                      /$$$$$$                     
| $$_____/                     /$$__  $$                    
| $$       /$$   /$$  /$$$$$$ | $$  \__/  /$$$$$$  /$$   /$$
| $$$$$   | $$  | $$ /$$__  $$|  $$$$$$  /$$__  $$| $$  | $$
| $$__/   | $$  | $$| $$$$$$$$ \____  $$| $$  \ $$| $$  | $$
| $$      | $$  | $$| $$_____/ /$$  \ $$| $$  | $$| $$  | $$
| $$$$$$$$|  $$$$$$$|  $$$$$$$|  $$$$$$/| $$$$$$$/|  $$$$$$$
|________/ \____  $$ \_______/ \______/ | $$____/  \____  $$
           /$$  | $$                    | $$       /$$  | $$
          |  $$$$$$/                    | $$      |  $$$$$$/
           \______/                     |__/       \______/ 
[/bold cyan]
[bright_yellow]EyeSpy Network Auditor v1.0 | By Technical Corp[/bright_yellow]
"""

def banner():
    os.system('clear' if os.name == 'posix' else 'cls')
    console.print(Panel.fit(BANNER, style="cyan", box=box.DOUBLE))

# -------------------------------------------------------------
# Network Scan Core
# -------------------------------------------------------------

def tcp_connect(ip, port, timeout=2):
    try:
        s = socket.socket()
        s.settimeout(timeout)
        s.connect((ip, port))
        return s
    except Exception:
        return None

def http_probe(ip, port=80):
    s = tcp_connect(ip, port)
    if not s:
        return None
    try:
        req = f"GET / HTTP/1.1\r\nHost: {ip}\r\nConnection: close\r\n\r\n"
        s.send(req.encode())
        resp = s.recv(1024).decode(errors='ignore')
        s.close()
        return resp
    except Exception:
        return None

def rtsp_probe(ip, port=554):
    s = tcp_connect(ip, port)
    if not s:
        return None
    try:
        req = f"OPTIONS rtsp://{ip}/ RTSP/1.0\r\nCSeq: 1\r\n\r\n"
        s.send(req.encode())
        resp = s.recv(1024).decode(errors='ignore')
        s.close()
        return resp
    except Exception:
        return None

def onvif_info(ip):
    if not ONVIF_AVAILABLE:
        return None
    try:
        cam = ONVIFCamera(ip, 80, '', '', '/usr/local/lib/python3.8/site-packages/wsdl/')
        info = cam.devicemgmt.GetDeviceInformation()
        return {
            'manufacturer': info.Manufacturer,
            'model': info.Model,
            'firmware': info.FirmwareVersion,
            'serial': info.SerialNumber
        }
    except Exception:
        return None

def scan_host(ip):
    data = {'ip': ip, 'http': False, 'rtsp': False, 'onvif': None}
    for p in [80, 8000, 8080]:
        r = http_probe(ip, p)
        if r and any(k in r.lower() for k in CAM_KEYWORDS):
            data['http'] = True
            break
    rt = rtsp_probe(ip)
    if rt and "rtsp" in rt.lower():
        data['rtsp'] = True
    if ONVIF_AVAILABLE:
        info = onvif_info(ip)
        if info:
            data['onvif'] = info
    return data

def run_scan(subnet):
    net = ipaddress.ip_network(subnet, strict=False)
    hosts = list(net.hosts())
    results = []
    q = queue.Queue()
    for ip in hosts:
        q.put(str(ip))
    total = len(hosts)
    with Progress() as progress:
        task = progress.add_task("[cyan]Scanning network...", total=total)
        def worker():
            while not q.empty():
                ip = q.get()
                result = scan_host(ip)
                if result['http'] or result['rtsp'] or result['onvif']:
                    results.append(result)
                progress.update(task, advance=1)
                q.task_done()
        threads = []
        for _ in range(50):
            t = threading.Thread(target=worker, daemon=True)
            t.start()
            threads.append(t)
        q.join()
    return results

# -------------------------------------------------------------
# HTML Report Generator
# -------------------------------------------------------------

HTML_TEMPLATE = """
<html>
<head>
<title>EyeSpy Report</title>
<style>
body { font-family: Arial, sans-serif; background: #121212; color: #e0e0e0; }
table { border-collapse: collapse; width: 100%; margin-top: 20px; }
th, td { border: 1px solid #444; padding: 8px; }
th { background: #00acc1; color: white; }
tr:nth-child(even) { background: #1e1e1e; }
a { color: #00bcd4; text-decoration: none; }
a:hover { text-decoration: underline; }
</style>
</head>
<body>
<h2>EyeSpy Network Camera Report</h2>
<p>Scan Time: {{ timestamp }}</p>
<table>
<tr><th>IP Address</th><th>Manufacturer</th><th>Model</th><th>Firmware</th><th>HTTP</th><th>RTSP</th></tr>
{% for cam in results %}
<tr>
<td><a href="http://{{ cam.ip }}" target="_blank">{{ cam.ip }}</a></td>
<td>{{ cam.onvif.manufacturer if cam.onvif else '-' }}</td>
<td>{{ cam.onvif.model if cam.onvif else '-' }}</td>
<td>{{ cam.onvif.firmware if cam.onvif else '-' }}</td>
<td>{{ '✅' if cam.http else '❌' }}</td>
<td>{{ '✅' if cam.rtsp else '❌' }}</td>
</tr>
{% endfor %}
</table>
</body>
</html>
"""

def generate_html_report(results):
    tmpl = Template(HTML_TEMPLATE)
    html = tmpl.render(results=results, timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    with open("eyespy_report.html", "w") as f:
        f.write(html)
    console.print("[green]✅ HTML report saved as eyespy_report.html[/green]")

# -------------------------------------------------------------
# Menu Interface
# -------------------------------------------------------------

def menu():
    banner()
    while True:
        console.print("\n[bright_yellow]Main Menu:[/bright_yellow]")
        console.print(" [cyan]1[/cyan]. Scan network for cameras")
        console.print(" [cyan]2[/cyan]. Generate HTML report")
        console.print(" [cyan]3[/cyan]. Exit")
        choice = Prompt.ask("\nSelect an option", choices=["1", "2", "3"])
        if choice == "1":
            subnet = Prompt.ask("[green]Enter subnet (e.g., 192.168.1.0/24)[/green]", default="192.168.1.0/24")
            results = run_scan(subnet)
            console.print(Panel(f"Scan Complete! Found {len(results)} possible cameras.", style="green"))
            with open("eyespy_results.json", "w") as f:
                json.dump(results, f, indent=2)
        elif choice == "2":
            if not os.path.exists("eyespy_results.json"):
                console.print("[red]No results found. Please scan first.[/red]")
            else:
                with open("eyespy_results.json") as f:
                    data = json.load(f)
                generate_html_report(data)
        elif choice == "3":
            console.print("[cyan]Goodbye! Stay secure.[/cyan]")
            break

# -------------------------------------------------------------
# CLI Entrypoint
# -------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # CLI mode
        parser = argparse.ArgumentParser(description="EyeSpy Network Auditor CLI")
        sub = parser.add_subparsers(dest="command")

        scan_cmd = sub.add_parser("scan", help="Scan network for cameras")
        scan_cmd.add_argument("--subnet", required=True, help="CIDR subnet e.g. 192.168.1.0/24")

        export_cmd = sub.add_parser("export", help="Generate HTML report from existing results")

        args = parser.parse_args()
        if args.command == "scan":
            results = run_scan(args.subnet)
            with open("eyespy_results.json", "w") as f:
                json.dump(results, f, indent=2)
            console.print(f"[green]Scan completed. {len(results)} cameras found.[/green]")
        elif args.command == "export":
            if os.path.exists("eyespy_results.json"):
                with open("eyespy_results.json") as f:
                    data = json.load(f)
                generate_html_report(data)
            else:
                console.print("[red]No results found. Run a scan first.[/red]")
    else:
        menu()
