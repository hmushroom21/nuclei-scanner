from flask import Flask, request, render_template
import subprocess
import os

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/scan", methods=["POST"])
def scan():
    target = request.form.get("target", "").strip()

    if not target:
        return "Please enter a target URL."

    os.makedirs("results", exist_ok=True)

    cmd = [
        "nuclei",
        "-u",
        target,
        "-json-export",
        "results/output.json"
    ]

    try:
        subprocess.run(cmd, check=True, timeout=120)
        return "Scan completed. Results saved to results/output.json"
    except subprocess.TimeoutExpired:
        return "Scan took too long and was stopped."
    except subprocess.CalledProcessError as e:
        return f"Scan failed: {e}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
