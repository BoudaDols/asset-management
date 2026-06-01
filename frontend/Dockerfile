# Municipal Asset Management System - Frontend Dockerfile
# Multi-stage build: development target uses Vite dev server, production serves static files via Nginx

# --- Base stage ---
FROM node:20-alpine AS base

WORKDIR /app

COPY package.json package-lock.json ./

RUN npm ci

COPY . .

# --- Development stage ---
FROM base AS development

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# --- Build stage ---
FROM base AS build

RUN npm run build

# --- Production stage ---
FROM nginx:alpine AS production

COPY --from=build /app/dist /usr/share/nginx/html

# SPA routing: redirect all requests to index.html
RUN echo 'server { \
    listen 80; \
    root /usr/share/nginx/html; \
    index index.html; \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
