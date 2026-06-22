from flask import Flask, request, render_template
import subprocess
import os

app = Flask(__name__)

os.makedirs("results", exist_ok=True)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/scan", methods=["POST"])
def scan():
    target = request.form.get("target", "").strip()

    if not target:
        return "Error: No target provided.", 400

    if not target.startswith(("http://", "https://")):
        return "Error: Target must start with http:// or https://", 400

    cmd = [
        "nuclei",
        "-u", target,
        "-json-export", "results/output.json",
        "-c", "3",           # only 3 concurrent templates (very low CPU)
        "-rl", "5",          # 5 requests/sec rate limit
        "-timeout", "5",     # 5s per request
        "-silent",           # no banner
        "-no-update-check",  # skip version check (saves memory + network)
        "-disable-update-check",
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=240
        )
        output = result.stdout.strip() or "Scan completed — no findings."
        if result.returncode != 0 and result.stderr:
            output += f"\n[stderr]: {result.stderr.strip()}"
    except subprocess.TimeoutExpired:
        output = "Scan timed out. Try a more specific target or fewer templates."
    except Exception as e:
        output = f"Scan error: {str(e)}"

    return f"<pre style='white-space:pre-wrap'>{output}</pre><br><a href='/'>← Back</a>"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
