# Render's free plan only runs Docker-deployed services or buildpacks that
# can't install arbitrary Go binaries, so we build nuclei from its official
# release here rather than relying on pip.

FROM python:3.11-slim AS base

# --- Install the real ProjectDiscovery Nuclei binary -----------------------
ARG NUCLEI_VERSION=3.3.7
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl unzip ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sSL -o /tmp/nuclei.zip \
        "https://github.com/projectdiscovery/nuclei/releases/download/v${NUCLEI_VERSION}/nuclei_${NUCLEI_VERSION}_linux_amd64.zip" \
    && unzip /tmp/nuclei.zip -d /usr/local/bin nuclei \
    && chmod +x /usr/local/bin/nuclei \
    && rm /tmp/nuclei.zip

# Download the official nuclei-templates repo at build time so scans don't
# need network access to GitHub at request time.
RUN nuclei -update-templates -silent || true

# --- App ---------------------------------------------------------------
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

ENV PORT=10000
EXPOSE 10000

# GOGC=20 makes Go's garbage collector run more often in exchange for a
# lower peak heap — worth it on a RAM-capped (e.g. 512MB) host. This applies
# to the nuclei subprocess too since it inherits the container environment.
ENV GOGC=20

# One gunicorn worker keeps the baseline Python footprint to a single
# process. Threads (not extra workers) handle concurrent requests, and the
# in-app semaphore (MAX_CONCURRENT_SCANS) makes sure only one nuclei process
# runs at a time regardless of how many requests come in. Timeout is set
# above NUCLEI_TIMEOUT_SECONDS so gunicorn doesn't kill a worker mid-scan.
CMD gunicorn --bind 0.0.0.0:${PORT:-10000} --workers 1 --threads 4 --timeout 150 app:app
