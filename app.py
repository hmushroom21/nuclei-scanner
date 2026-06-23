from flask import Flask, request
import requests
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
    <small>This app is deployed using GitHub and Render.</small>

    {result}
  </div>
</body>
</html>"""


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

    try:
        response = requests.get(
            target,
            timeout=10,
            allow_redirects=True,
            headers={"User-Agent": "StudentWebsiteScanner/1.0"}
        )

        headers = response.headers
        body = response.text.lower()

        result = []
        result.append("===== WEBSITE SCAN RESULT =====")
        result.append(f"Target URL: {target}")
        result.append(f"Final URL: {response.url}")
        result.append(f"Status Code: {response.status_code}")
        result.append(f"Server: {headers.get('Server', 'Not shown')}")
        result.append(f"Content-Type: {headers.get('Content-Type', 'Not shown')}")
        result.append("")

        result.append("===== SECURITY HEADER CHECK =====")

        security_headers = [
            "Strict-Transport-Security",
            "Content-Security-Policy",
            "X-Frame-Options",
            "X-Content-Type-Options",
            "Referrer-Policy",
            "Permissions-Policy"
        ]

        for header in security_headers:
            if header in headers:
                result.append(f"[OK] {header}: {headers.get(header)}")
            else:
                result.append(f"[MISSING] {header}")

        result.append("")
        result.append("===== COOKIE CHECK =====")

        if not response.cookies:
            result.append("No cookies found.")
        else:
            for cookie in response.cookies:
                result.append(f"Cookie: {cookie.name}")

                if cookie.secure:
                    result.append("  [OK] Secure flag enabled")
                else:
                    result.append("  [WARNING] Secure flag missing")

                if "HttpOnly" in cookie._rest or "httponly" in cookie._rest:
                    result.append("  [OK] HttpOnly flag enabled")
                else:
                    result.append("  [WARNING] HttpOnly flag missing")

        result.append("")
        result.append("===== BASIC TECHNOLOGY DETECTION =====")

        tech_checks = {
            "WordPress": "wp-content",
            "React": "react",
            "Vue.js": "vue",
            "Bootstrap": "bootstrap",
            "jQuery": "jquery",
            "Cloudflare": "cloudflare",
            "Google Analytics": "google-analytics"
        }

        found = []

        for tech, keyword in tech_checks.items():
            if keyword.lower() in body or keyword.lower() in str(headers).lower():
                found.append(tech)

        if found:
            for tech in found:
                result.append(f"Detected: {tech}")
        else:
            result.append("No common technologies detected.")

        result.append("")
        result.append("===== NOTE =====")
        result.append("This is a lightweight scanner made for Render free plan.")
        result.append("It checks status code, headers, cookies, and simple technologies.")

        output = "\n".join(result)

    except requests.exceptions.Timeout:
        output = "Error: Request timed out."

    except requests.exceptions.ConnectionError:
        output = "Error: Could not connect to the website."

    except Exception as e:
        output = f"Error: {e}"

    return HTML.format(result=f"<pre>{html.escape(output)}</pre>")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
