FROM node:23-alpine as build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --legacy-peer-deps

COPY . .
RUN npm run build

FROM nginx:alpine
# Angular 19 build output is in dist/token-tracker-frontend/browser
COPY --from=build /app/dist/token-tracker-frontend/browser /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
