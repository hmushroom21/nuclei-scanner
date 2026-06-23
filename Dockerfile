FROM projectdiscovery/nuclei:latest

WORKDIR /app

USER root

RUN apk add --no-cache python3 py3-pip

COPY requirements.txt .
RUN pip3 install --break-system-packages -r requirements.txt

COPY . .

ENV GOMEMLIMIT=256MiB
ENV GOGC=50

EXPOSE 10000

CMD ["python3", "app.py"]
