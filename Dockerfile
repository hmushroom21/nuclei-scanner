FROM projectdiscovery/nuclei:latest

RUN apk add --no-cache python3 py3-pip

WORKDIR /app

COPY . .

RUN python3 -m venv /app/venv
RUN /app/venv/bin/pip install --upgrade pip
RUN /app/venv/bin/pip install -r requirements.txt

EXPOSE 10000

ENTRYPOINT []

CMD ["/app/venv/bin/gunicorn", "app:app", "--bind", "0.0.0.0:10000"]
