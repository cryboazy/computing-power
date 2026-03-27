FROM node:20-alpine AS builder

WORKDIR /app

RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories \
    && npm config set registry https://registry.npmmirror.com

ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

COPY package*.json ./

RUN npm ci

COPY . .

RUN npm run build

FROM nginx:alpine

WORKDIR /app

RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories \
    && addgroup -g 1001 -S nginxGroup \
    && adduser -S nginxUser -u 1001 -G nginxGroup

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

RUN chown -R nginxUser:nginxGroup /usr/share/nginx/html \
    && chown -R nginxUser:nginxGroup /var/cache/nginx \
    && chown -R nginxUser:nginxGroup /var/log/nginx \
    && chown -R nginxUser:nginxGroup /etc/nginx/conf.d \
    && touch /var/run/nginx.pid \
    && chown nginxUser:nginxGroup /var/run/nginx.pid

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

USER nginxUser

CMD ["nginx", "-g", "daemon off;"]
