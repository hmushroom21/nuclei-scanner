from flask import Flask, request, render_template
import subprocess
import os

app = Flask(__name__)

# Ensure results dir exists at startup
os.makedirs("results", exist_ok=True)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/scan", methods=["POST"])
def scan():
    target = request.form.get("target", "").strip()

    if not target:
        return "Error: No target provided.", 400

    # Basic validation — must start with http:// or https://
    if not target.startswith(("http://", "https://")):
        return "Error: Target must start with http:// or https://", 400

    cmd = [
        "nuclei",
        "-u", target,
        "-json-export", "results/output.json",
        "-c", "5",          # max 5 concurrent templates (low CPU)
        "-rl", "10",        # rate limit: 10 requests/sec
        "-timeout", "5",    # 5s per request timeout
        "-silent",          # suppress banner output
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=240  # kill after 4 min to stay under gunicorn's 300s
        )
        output = result.stdout or "Scan completed with no output."
        if result.returncode != 0:
            output += f"\n[stderr]: {result.stderr}"
    except subprocess.TimeoutExpired:
        output = "Scan timed out. Try a more specific target or fewer templates."
    except Exception as e:
        output = f"Scan error: {str(e)}"

    return f"<pre>{output}</pre><br><a href='/'>← Back</a>"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
