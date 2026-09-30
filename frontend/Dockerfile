# syntax=docker/dockerfile:1
FROM node:22-alpine@sha256:0a7108bf6c7bf5de370ffb1a3ed6be93d405b43ff159f681a8d18c0e2bc2e402 AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:1.27-alpine@sha256:65645c7bb6a0661892a8b03b89d0743208a18dd2f3f17a54ef4b76fb8e2f2a10
# Remove default config
RUN rm /etc/nginx/conf.d/default.conf
# Create non-root user setup
RUN touch /run/nginx.pid && \
    chown -R nginx:nginx /var/cache/nginx /var/run /var/log/nginx /run/nginx.pid && \
    sed -i 's/listen       80;/listen       8080;/' /etc/nginx/conf.d/*.conf 2>/dev/null || true
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
RUN chown -R nginx:nginx /usr/share/nginx/html

USER nginx
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD ["wget", "--no-verbose", "--tries=1", "--spider", "http://127.0.0.1:8080/"] || exit 1

CMD ["nginx", "-g", "daemon off;"]
