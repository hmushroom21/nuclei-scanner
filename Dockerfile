FROM projectdiscovery/nuclei:latest

USER root

RUN apk add --no-cache python3 py3-pip

WORKDIR /app

COPY app.py .

RUN pip install flask gunicorn --break-system-packages --quiet --root-user-action=ignore

RUN mkdir -p results

# Download templates at build time only — no dummy scan
RUN nuclei -update-templates -silent

EXPOSE 10000

CMD gunicorn app:app --bind 0.0.0.0:10000 --workers 1 --threads 1 --timeout 300
