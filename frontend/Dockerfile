FROM node:20-alpine AS builder

LABEL maintainer="Computing Power Monitor"
LABEL description="Frontend build stage for Computing Power Monitoring Platform"

WORKDIR /app

RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories

ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

COPY package*.json ./

RUN npm config set registry https://registry.npmmirror.com \
    && npm install

COPY . .

RUN npm run build

FROM nginx:alpine

LABEL maintainer="Computing Power Monitor"
LABEL description="Frontend service for Computing Power Monitoring Platform"

RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories

COPY --from=builder /app/dist /usr/share/nginx/html

COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
