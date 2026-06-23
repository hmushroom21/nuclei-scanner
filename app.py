from flask import Flask, request
import subprocess, os
import html

app = Flask(__name__)
os.makedirs("results", exist_ok=True)

HTML = """<!DOCTYPE html>
<html>
<head>
  <title>Nuclei Scanner</title>
  <style>
    body {{ font-family: sans-serif; max-width: 520px; margin: 60px auto; }}
    input {{ width: 100%; padding: 8px; margin-bottom: 10px; box-sizing: border-box; }}
    button {{ padding: 8px 20px; }}
    pre {{ background: #111; color: #0f0; padding: 12px; border-radius: 6px;
          white-space: pre-wrap; font-size: 0.85em; }}
    small {{ color: #888; }}
  </style>
</head>
<body>
  <h1>Nuclei Scanner</h1>
  <form method="post" action="/scan">
    <input name="target" placeholder="https://example.com" required>
    <button type="submit">Scan</button>
  </form>
  <small>⚠️ Scans may take a few minutes.</small>
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
        return HTML.format(result="<pre>Error: Target must start with http:// or https://</pre>")

    cmd = [
        "nuclei",
        "-u", target,
        "-tags", "tech-detect",
        "-c", "3",
        "-rl", "5",
        "-timeout", "5",
        "-silent",
        "-duc",
        "-json-export", "results/output.json",
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=240)

        output = result.stdout.strip()

        if not output:
            output = result.stderr.strip()

        if not output:
            output = "Scan completed — no findings."

    except subprocess.TimeoutExpired:
        output = "Scan timed out because it took more than 4 minutes."
    except Exception as e:
        output = f"Error: {e}"

    safe_output = html.escape(output)
    return HTML.format(result=f"<pre>{safe_output}</pre>")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
