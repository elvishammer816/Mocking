FROM python:3.11-slim

# Install Chromium and dependencies
RUN apt-get update && \
    apt-get install -y chromium chromium-driver && \
    rm -rf /var/lib/apt/lists/*

# Environment variables for Chromium
ENV CHROME_BINARY=/usr/bin/chromium

WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

CMD ["python", "main.py"]
