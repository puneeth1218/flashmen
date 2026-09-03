FROM node:18-alpine AS build

WORKDIR /app
COPY frontend/package*.json ./
COPY offline_packages/npm ./offline_packages/npm

# Use npm ci with offline cache
RUN npm ci --cache ./offline_packages/npm --prefer-offline

COPY frontend/ ./
RUN npm run build

FROM nginx:1.25-alpine
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
