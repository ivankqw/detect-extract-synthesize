FROM amd64/python:3.11.8-slim-bullseye

RUN apt-get update \
    && apt-get -y install libpq-dev gcc \
    && apt-get install -y htop libgl1 libglib2.0-0 libpython3-dev gnupg g++ libusb-1.0-0 \
    && pip install psycopg2

WORKDIR /app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]