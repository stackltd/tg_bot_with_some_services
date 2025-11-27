FROM python:latest

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install -r requirements.txt

RUN apt-get update
RUN apt-get -y install python3-brotli

COPY . .

CMD ["python", "main.py"]
