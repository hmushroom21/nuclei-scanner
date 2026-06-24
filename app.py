from flask import Flask, request, render_template
import subprocess, os, time, json
from collections import Counter

app = Flask(__name__)

SEVERITY_ORDER = ["critical", "high", "medium", "low", "info", "unknown"]
SEVERITY_COLORS = {
    "critical": "#8b0000",
    "high": "#e74c3c",
    "medium": "#f39c12",
    "low": "#3498db",
    "info": "#95a5a6",
    "unknown": "#7f8c8d",
}


def severity_chart_data(findings):
    """Build (severity, count, color, pct) rows for a simple bar chart,
    scaled relative to the largest bucket. No JS/CDN required."""
    counts = Counter(
        (f.get("info", {}).get("severity") or "unknown") for f in findings
    )
    ordered = [(sev, counts[sev]) for sev in SEVERITY_ORDER if counts.get(sev)]
    if not ordered:
        return []
    max_count = max(c for _, c in ordered)
    return [
        {
            "severity": sev,
            "count": count,
            "color": SEVERITY_COLORS.get(sev, "#999"),
            "pct": round(count / max_count * 100),
        }
        for sev, count in ordered
    ]


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/scan", methods=["POST"])
def scan():
    target = request.form["target"]

    os.makedirs("results", exist_ok=True)
    output = f"results/output_{int(time.time())}.jsonl"

    cmd = [
    "nuclei",
    "-u", target,
    "-t", "/root/nuclei-templates/http/misconfiguration/http-missing-security-headers.yaml",
    "-jsonl",
    "-o", output,
    "-c", "1",
    "-rl", "1",
    "-timeout", "10",
    "-retries", "0",
    "-silent",
    "-duc"
]

    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=40)
    except Exception as e:
        return f"Scan error: {e}"

    findings = []

    if os.path.exists(output):
        with open(output) as f:
            for line in f:
                if line.strip():
                    findings.append(json.loads(line))

    return render_template(
        "index.html",
        target=target,
        findings=findings,
        stderr=r.stderr,
        severity_chart=severity_chart_data(findings)
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
