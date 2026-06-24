FROM node:23-alpine AS build

WORKDIR /app

# Install corporate CA certificate for SSL inspection proxy (Netskope)
COPY netskope-ca.crt /usr/local/share/ca-certificates/netskope-ca.crt
RUN cat /usr/local/share/ca-certificates/netskope-ca.crt >> /etc/ssl/certs/ca-certificates.crt
ENV NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt

COPY package.json package-lock.json ./
RUN npm ci --legacy-peer-deps

COPY . .
RUN npm run build

FROM nginx:alpine
# Angular build output directory
COPY --from=build /app/dist/token-tracker-frontend /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
