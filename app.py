from flask import Flask, request
import subprocess
import json
import shutil
import socket
import ipaddress
import html
import os
from urllib.parse import urlparse

app = Flask(__name__)

HTML = """<!DOCTYPE html>
<html>
<head>
  <title>Website Scanner</title>
  <style>
    body {{
      font-family: Arial, sans-serif;
      max-width: 750px;
      margin: 60px auto;
      padding: 0 20px;
      background: #f7f7f7;
    }}
    .card {{
      background: white;
      padding: 30px;
      border-radius: 12px;
      box-shadow: 0 4px 15px rgba(0,0,0,0.08);
    }}
    h1 {{
      margin-top: 0;
    }}
    input {{
      width: 100%;
      padding: 12px;
      margin-bottom: 15px;
      box-sizing: border-box;
      font-size: 16px;
      border: 1px solid #ccc;
      border-radius: 6px;
    }}
    button {{
      padding: 10px 25px;
      font-size: 16px;
      cursor: pointer;
      border: none;
      border-radius: 6px;
      background: #111;
      color: white;
    }}
    pre {{
      background: #111;
      color: #00ff66;
      padding: 15px;
      border-radius: 8px;
      white-space: pre-wrap;
      word-wrap: break-word;
      font-size: 0.9em;
      margin-top: 25px;
    }}
    small {{
      color: #777;
      display: block;
      margin-top: 10px;
    }}
  </style>
</head>
<body>
  <div class="card">
    <h1>Website Scanner</h1>
    <form method="post" action="/scan">
      <input name="target" placeholder="https://example.com" required>
      <button type="submit">Scan</button>
    </form>
    <small>Only scan websites you own or have permission to test.</small>
    <small>This app is deployed using GitHub and Render. Powered by Nuclei.</small>
    {result}
  </div>
</body>
</html>"""

# Severities to run by default. Keep this conservative for a public-facing,
# unauthenticated form — "critical/high" only avoids turning this into a
# heavyweight all-templates scan against arbitrary third-party hosts.
DEFAULT_SEVERITIES = "info,low,medium,high,critical"
NUCLEI_TIMEOUT_SECONDS = 120


def is_private_target(hostname: str) -> bool:
    """Best-effort SSRF guard: resolve the hostname and reject anything
    pointing at loopback/private/link-local/reserved address space.
    This does NOT fully eliminate SSRF/DNS-rebinding risk, just blocks
    the obvious cases of someone pointing the scanner at internal infra."""
    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        return False  # let the request fail naturally later
    for info in infos:
        ip = info[4][0]
        try:
            addr = ipaddress.ip_address(ip)
        except ValueError:
            continue
        if (
            addr.is_private
            or addr.is_loopback
            or addr.is_link_local
            or addr.is_reserved
            or addr.is_multicast
        ):
            return True
    return False


def run_nuclei_scan(target: str):
    """Run the real ProjectDiscovery Nuclei scanner against target and
    return a list of parsed JSON findings (possibly empty), plus an error
    string if something went wrong."""
    nuclei_path = shutil.which("nuclei")
    if not nuclei_path:
        return None, "Nuclei binary not found on this server. See setup notes below."

    cmd = [
        nuclei_path,
        "-u", target,
        "-jsonl",          # one JSON object per line
        "-silent",
        "-severity", DEFAULT_SEVERITIES,
        "-timeout", "10",       # per-request timeout (seconds)
        "-rate-limit", "50",    # requests/sec cap
        "-c", "10",              # concurrency
        "-no-color",
    ]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=NUCLEI_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return None, f"Nuclei scan timed out after {NUCLEI_TIMEOUT_SECONDS}s."
    except Exception as e:
        return None, f"Failed to run nuclei: {e}"

    findings = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            findings.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    # Surface stderr only if nuclei produced nothing at all and exited oddly,
    # so genuine "no vulnerabilities found" runs don't look like errors.
    if not findings and proc.returncode != 0 and proc.stderr.strip():
        return [], proc.stderr.strip()[-2000:]

    return findings, None


def format_findings(target: str, findings: list, stderr_note: str | None) -> str:
    lines = []
    lines.append("===== NUCLEI SCAN RESULT =====")
    lines.append(f"Target URL: {target}")
    lines.append(f"Severities checked: {DEFAULT_SEVERITIES}")
    lines.append("")

    if not findings:
        lines.append("No findings reported by Nuclei for the selected severities.")
        if stderr_note:
            lines.append("")
            lines.append("===== NUCLEI STDERR (tail) =====")
            lines.append(stderr_note)
        return "\n".join(lines)

    lines.append(f"Total findings: {len(findings)}")
    lines.append("")
    lines.append("===== FINDINGS =====")
    for f in findings:
        info = f.get("info", {})
        name = info.get("name", "Unknown")
        severity = info.get("severity", "unknown").upper()
        template_id = f.get("template-id", "unknown-template")
        matched_at = f.get("matched-at", target)
        description = info.get("description", "").strip()
        lines.append(f"[{severity}] {name} ({template_id})")
        lines.append(f"  Matched at: {matched_at}")
        if description:
            lines.append(f"  {description}")
        lines.append("")

    return "\n".join(lines).rstrip()


@app.route("/")
def home():
    return HTML.format(result="")


@app.route("/health")
def health():
    return "ok", 200


@app.route("/scan", methods=["POST"])
def scan():
    target = request.form.get("target", "").strip()

    if not target.startswith(("http://", "https://")):
        output = "Error: URL must start with http:// or https://"
        return HTML.format(result=f"<pre>{html.escape(output)}</pre>")

    parsed = urlparse(target)
    if not parsed.netloc:
        output = "Error: Invalid URL."
        return HTML.format(result=f"<pre>{html.escape(output)}</pre>")

    hostname = parsed.hostname or ""
    if is_private_target(hostname):
        output = "Error: Scanning private, loopback, or link-local addresses is not allowed."
        return HTML.format(result=f"<pre>{html.escape(output)}</pre>")

    findings, error = run_nuclei_scan(target)

    if findings is None:
        setup_note = (
            "\n\n===== SETUP NEEDED =====\n"
            "The 'nuclei' binary was not found on PATH. Install it and templates, "
            "then redeploy. See the Dockerfile / setup notes provided alongside this file."
        )
        output = f"Error: {error}{setup_note if 'not found' in (error or '') else ''}"
        return HTML.format(result=f"<pre>{html.escape(output)}</pre>")

    output = format_findings(target, findings, error)
    return HTML.format(result=f"<pre>{html.escape(output)}</pre>")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
