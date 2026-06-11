FROM python:3.10

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
 && rm -rf /var/lib/apt/lists/*

# Install DVC with S3 support
RUN pip install --no-cache-dir "dvc[s3]"

# Install MinIO Client (mc) explicitly
RUN curl -fsSL https://dl.min.io/client/mc/release/linux-amd64/mc \
    -o /usr/local/bin/mc \
 && chmod +x /usr/local/bin/mc

WORKDIR /workspace