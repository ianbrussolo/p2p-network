FROM python:3.8-slim

WORKDIR /app
COPY . /app

CMD ["python", "p2p.py", "127.0.0.1:3000"]
