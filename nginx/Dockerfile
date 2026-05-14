FROM nginx:alpine

# Копируем кастомную конфигурацию nginx
COPY nginx.conf /etc/nginx/nginx.conf

# Создаем директорию для статики
RUN mkdir -p /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
