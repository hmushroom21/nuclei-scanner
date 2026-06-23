FROM projectdiscovery/nuclei:latest

WORKDIR /app

USER root

RUN apk add --no-cache python3 py3-pip

COPY requirements.txt .
RUN pip3 install --break-system-packages -r requirements.txt

COPY . .

EXPOSE 10000

CMD ["python3", "app.py"]
