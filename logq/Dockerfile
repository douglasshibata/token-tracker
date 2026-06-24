FROM golang:1.24-alpine AS builder
WORKDIR /app

# Install corporate CA certificate for SSL inspection proxy (Netskope)
COPY netskope-ca.crt /tmp/netskope-ca.crt
RUN cat /tmp/netskope-ca.crt >> /etc/ssl/certs/ca-certificates.crt

COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN go build -o logq main.go

FROM alpine:latest
WORKDIR /app
COPY --from=builder /app/logq .
ENTRYPOINT ["./logq"]
