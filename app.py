from flask import Flask, request
import subprocess
import os
import html

app = Flask(__name__)

HTML = """<!DOCTYPE html>
<html>
<head>
  <title>Nuclei Scanner</title>
  <style>
    body {{
      font-family: sans-serif;
      max-width: 650px;
      margin: 60px auto;
      padding: 0 20px;
    }}

    h1 {{
      font-size: 42px;
      margin-bottom: 30px;
    }}

    input {{
      width: 100%;
      padding: 12px;
      margin-bottom: 15px;
      box-sizing: border-box;
      font-size: 16px;
    }}

    button {{
      padding: 10px 25px;
      font-size: 16px;
      cursor: pointer;
    }}

    pre {{
      background: #111;
      color: #0f0;
      padding: 15px;
      border-radius: 6px;
      white-space: pre-wrap;
      word-wrap: break-word;
      font-size: 0.9em;
      margin-top: 25px;
    }}

    .error {{
      color: #ff6b6b;
    }}

    small {{
      color: #888;
      display: block;
      margin-top: 10px;
    }}
  </style>
</head>
<body>
  <h1>Nuclei Scanner</h1>

  <form method="post" action="/scan">
    <input name="target" placeholder="https://example.com" required>
    <button type="submit">Scan</button>
  </form>

  <small>⚠️ Only scan websites you own or have permission to test.</small>
  <small>This Render version uses low memory settings.</small>

  {result}
</body>
</html>"""


@app.route("/health")
def health():
    return "ok", 200


@app.route("/")
def home():
    return HTML.format(result="")


@app.route("/scan", methods=["POST"])
def scan():
    target = request.form.get("target", "").strip()

    if not target.startswith(("http://", "https://")):
        output = "Error: Target must start with http:// or https://"
        return HTML.format(result=f"<pre class='error'>{html.escape(output)}</pre>")

    template_path = "templates/basic-detect.yaml"

    if not os.path.exists(template_path):
        output = "Error: Template file not found. Make sure templates/basic-detect.yaml exists."
        return HTML.format(result=f"<pre class='error'>{html.escape(output)}</pre>")

    cmd = [
        "nuclei",
        "-u", target,
        "-t", template_path,
        "-c", "1",
        "-rl", "1",
        "-timeout", "3",
        "-retries", "0",
        "-silent",
        "-duc",
        "-no-stdin",
    ]

    env = os.environ.copy()
    env["GOMEMLIMIT"] = "256MiB"
    env["GOGC"] = "50"

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180,
            env=env
        )

        output = result.stdout.strip()

        if not output:
            output = result.stderr.strip()

        if not output:
            output = "Scan completed — no findings."

    except subprocess.TimeoutExpired:
        output = "Scan timed out because it took more than 3 minutes."

    except Exception as e:
        output = f"Error: {e}"

    safe_output = html.escape(output)
    return HTML.format(result=f"<pre>{safe_output}</pre>")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
