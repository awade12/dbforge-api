FROM python:3.9-slim

# Install system dependencies and Docker client
RUN apt-get update && \
    apt-get install -y curl && \
    curl -fsSL https://get.docker.com -o get-docker.sh && \
    sh get-docker.sh && \
    rm get-docker.sh && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose the port
EXPOSE 3943

CMD ["python", "run.py"]


### docker build -t fastapi-docker-app .
### docker run -p 3943:3943 fastapi-docker-app
## --privileged