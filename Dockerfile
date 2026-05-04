FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire doctor package + entrypoint
COPY doctor/ doctor/
COPY main.py .

EXPOSE 8080

CMD ["python", "-u", "main.py"]
