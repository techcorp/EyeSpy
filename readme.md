# EyeSpy — Network Camera Auditor

![EyeSpy Banner](40444c49-e875-4db5-b342-3357ebab98b3.png)

**EyeSpy** is a lightweight, interactive network camera discovery and auditing tool built for IT and security teams. It combines multiple discovery techniques (SSDP/UPnP, ONVIF/WS-Discovery, HTTP/RTSP probing) and produces JSON/CSV and a clean HTML report with clickable links. The tool is designed for authorized, non-destructive discovery and inventory of IP cameras on local networks.

---

## Quick banner

```
EyeSpy Network Auditor v1.0
By Muhammad Anas
```

---

## Key features

- Multimethod discovery: SSDP/UPnP, ONVIF (WS-Discovery), RTSP and HTTP probes.
- ONVIF details extraction: manufacturer, model, firmware version, serial (when device supports ONVIF).
- NAT/UPnP mapping enumeration (optional) to infer public exposure of devices.
- Interactive, menu-driven terminal UI with a colorful banner (uses `rich`).
- CLI subcommands for automation: `scan`, `export` (HTML), and `check-public` (optional).
- Exports: `eyespy_results.json` and `eyespy_report.html` (clickable links to camera web UI and RTSP URIs).
- Non-destructive: no brute force or exploit attempts — only fingerprinting and metadata collection.

---

## Requirements

- Python 3.8+
- Recommended packages (install via pip):

```bash
pip install rich tqdm requests onvif_zeep wsdiscovery jinja2
```

- Optional packages:

  - `miniupnpc` — for UPnP/NAT mapping checks (may require C build tools on Windows)
  - `wsdiscovery` — for ONVIF/WS-Discovery support (recommended)
  - `onvif_zeep` or `onvif` — to retrieve ONVIF device information (manufacturer/model/firmware)

> **Windows note:** Installing `miniupnpc` on Windows may fail if Visual C++ Build Tools are not installed. See Troubleshooting below for workarounds.

---

## Installation

1. Create a virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate     # Windows
```

2. Install core dependencies:

```bash
pip install --upgrade pip
pip install rich tqdm requests onvif_zeep wsdiscovery jinja2
```

3. (Optional) Install `miniupnpc` for NAT/UPnP checks:

```bash
pip install miniupnpc
```

If the above fails on Windows with a wheel/build error, either install Visual C++ Build Tools (Desktop C++ workload) or install the prebuilt package `miniupnpc-bin`:

```bash
pip install miniupnpc-bin
```

---

## Files produced

- `eyespy_results.json` — raw scan results (JSON)
- `eyespy_report.html` — human-friendly HTML report with clickable links
- `cameras.csv` — (optional) CSV export of found cameras

---

## Usage

### Interactive mode

Run the tool without arguments to use the interactive menu:

```bash
python eyespy.py
```

Follow the prompts to:
- Scan a subnet (e.g. `192.168.1.0/24`)
- Generate HTML report from last results
- Run other utilities

### CLI mode (non-interactive)

Use subcommands for automation and integration.

**Scan a subnet and save results**

```bash
python eyespy.py scan --subnet 192.168.1.0/24
```

This saves `eyespy_results.json` to the current folder.

**Generate HTML report from previous results**

```bash
python eyespy.py export
```

**(Optional) Check public exposure (UPnP/NAT)**

```bash
python eyespy.py check-public
```

> Note: `check-public` requires `miniupnpc` and that your router responds to UPnP. On locked-down enterprise networks this may not work.

---

## How discovery works (high level)

1. **SSDP/UPnP**: sends M-SEARCH multicast and collects responses. Useful for devices advertising services.
2. **ONVIF (WS-Discovery)**: attempts WS-Discovery to find ONVIF-compliant devices (if library available).
3. **RTSP probe**: sends `OPTIONS` to port 554 and looks for RTSP responses.
4. **HTTP probe**: performs lightweight GET requests to common ports and looks for camera-related signatures in headers/body.
5. **Heuristics**: the tool uses a scoring approach combining ONVIF presence, RTSP response, and keyword matches to mark a device as `likely_camera`.

This preserves safety — no default-cred checks, no configuration changes, and no exploitation.

---

## HTML report

The generated `eyespy_report.html` contains a table of discovered devices with these columns:
- IP Address (clickable HTTP link)
- Manufacturer
- Model
- Firmware
- HTTP present (yes/no)
- RTSP present (yes/no)

Open the file in your browser for a quick audit report ready for inclusion in documentation.

---

## Troubleshooting & Common Errors

### `Failed building wheel for miniupnpc` on Windows
**Cause:** Missing Visual C++ Build Tools.
**Fixes:**
- Install Visual C++ Build Tools from Microsoft (Desktop development with C++ workload), then `pip install miniupnpc`.
- Or install the prebuilt package: `pip install miniupnpc-bin`.
- Or skip the NAT check — the tool will run without `miniupnpc`.

### ONVIF errors or no ONVIF results
- Ensure cameras support ONVIF and that ONVIF is enabled on the device.
- ONVIF requests may require reaching specific ports (often 80/8080/8899/554) — ensure network routing/firewall allows it.

### SSDP/Multicast blocked
- Some networks block multicast/SSDP. If SSDP returns few or no results, rely on port-based scanning and ONVIF discovery.

---

## Security, ethics, and scope

**Important:** Only run EyeSpy where you have explicit authorization. Scanning networks or devices without permission may be illegal and unethical. This tool intentionally avoids intrusive actions (no credential brute force, no configuration changes, no firmware operations).

When using the tool for formal testing, keep a written authorization and a scope-of-work defining allowed activities.

---

## Extending the tool

Suggestions for future features you can add or request:
- ONVIF device detail enrichment (pull device service URLs, profiles, stream URIs).
- Live TUI dashboard (real-time discovery & status).
- Flask web UI for central reporting and historical tracking.
- Integration with SIEM or asset database.

If you want any of these, I can help implement them.

---

## License & Attribution

Use freely within your organization. Attribution appreciated: "EyeSpy — Network Camera Auditor by Muhammad Anas".

---

## Contact / Support

If you run into issues, share the following when reporting:
- OS and Python version
- Exact `pip install` error output (if any)
- The subnet scanned and sample `eyespy_results.json` (if available)

I'll help debug further.

---

*End of README*

