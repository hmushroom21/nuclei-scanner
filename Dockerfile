FROM projectdiscovery/nuclei:latest

WORKDIR /app

USER root

RUN apk add --no-cache python3 py3-pip git

COPY requirements.txt .
RUN pip3 install --break-system-packages -r requirements.txt

# Download nuclei templates during build
RUN nuclei -update-templates || true

COPY . .

EXPOSE 10000

CMD ["python3", "app.py"]
