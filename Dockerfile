FROM projectdiscovery/nuclei:latest

USER root

RUN apk add --no-cache python3 py3-pip

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt --break-system-packages

RUN mkdir -p results templates

EXPOSE 10000

# 1 worker, 1 thread, long timeout for slow CPU
CMD gunicorn app:app --bind 0.0.0.0:10000 --workers 1 --threads 1 --timeout 300
