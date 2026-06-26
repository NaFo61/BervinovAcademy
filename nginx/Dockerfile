FROM nginx:alpine

ARG NGINX_CONF=nginx.conf
COPY ${NGINX_CONF} /etc/nginx/nginx.conf

RUN mkdir -p /usr/share/nginx/html

EXPOSE 80 18080

CMD ["nginx", "-g", "daemon off;"]
