FROM python:3.12-slim

WORKDIR /app

# Install corporate CA certificate for SSL inspection proxy (Netskope)
COPY netskope-ca.crt /usr/local/share/ca-certificates/netskope-ca.crt
RUN cat /usr/local/share/ca-certificates/netskope-ca.crt >> /etc/ssl/certs/ca-certificates.crt
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install psql for wait-for-db
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

COPY . .

# Fix Windows line endings in entrypoint script
RUN sed -i 's/\r$//' entrypoint.sh && chmod +x entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]
