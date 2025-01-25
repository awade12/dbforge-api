FROM docker:dind

# Install Python and required system dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    gcc \
    python3-dev \
    musl-dev \
    linux-headers

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Create and activate virtual environment, then install dependencies
RUN python3 -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose the port the app runs on
EXPOSE 3943

# Use the virtual environment's Python
ENV PATH="/opt/venv/bin:$PATH"

ENTRYPOINT ["dockerd-entrypoint.sh"]
CMD ["python3", "run.py"]


### docker build -t fastapi-docker-app .
### docker run -p 3943:3943 fastapi-docker-app
## --privileged