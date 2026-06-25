# Build stage
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies (postgresql-client for wait-for-db)
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install corporate CA certificate
COPY netskope-ca.crt /usr/local/share/ca-certificates/netskope-ca.crt
RUN cat /usr/local/share/ca-certificates/netskope-ca.crt >> /etc/ssl/certs/ca-certificates.crt
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt

# Copy application code
COPY . .

# Fix Windows line endings and set permissions
RUN sed -i 's/\r$//' entrypoint.sh && chmod +x entrypoint.sh

# Create non-root user
RUN useradd -m tracker && chown -R tracker:tracker /app
USER tracker

ENTRYPOINT ["./entrypoint.sh"]
