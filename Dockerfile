FROM python:3.11-alpine

RUN apk add --no-cache curl unzip

RUN curl -sL https://github.com/projectdiscovery/nuclei/releases/download/v3.3.9/nuclei_3.3.9_linux_amd64.zip -o nuclei.zip \
    && unzip nuclei.zip nuclei \
    && mv nuclei /usr/local/bin/nuclei \
    && rm nuclei.zip

WORKDIR /app

COPY app.py .

RUN pip install flask gunicorn --quiet

RUN mkdir -p results

EXPOSE 10000

CMD ["gunicorn", "app:app", \
     "--bind", "0.0.0.0:10000", \
     "--workers", "1", \
     "--threads", "1", \
     "--timeout", "300", \
     "--graceful-timeout", "30", \
     "--keep-alive", "5", \
     "--worker-tmp-dir", "/dev/shm"]
