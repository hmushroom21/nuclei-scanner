FROM projectdiscovery/nuclei:latest

USER root

# Install Python
RUN apk add --no-cache python3 py3-pip

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt --break-system-packages --quiet \
    --root-user-action=ignore

# Pre-download nuclei templates at BUILD time so they are baked into the image.
# This avoids the ~200MB download at runtime which OOMs the 512MB free tier.
RUN nuclei -update-templates -silent || true

RUN mkdir -p results templates

EXPOSE 10000

# 1 worker, 1 thread, long timeout for slow 0.1 CPU
CMD gunicorn app:app --bind 0.0.0.0:10000 --workers 1 --threads 1 --timeout 300
