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

CMD ["python", "app.py"]
