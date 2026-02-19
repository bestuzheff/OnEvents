FROM python:3.14-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

# Копируем нужные файлы
COPY create_web.py /app/create_web.py
RUN mkdir -p /app/utils
COPY utils/ /app/utils/
RUN mkdir -p /app/web
COPY web/index.html /app/web/index.html
RUN mkdir -p /app/img
COPY img/ /app/img/
RUN mkdir -p /app/events
COPY events/ /app/events/
RUN mkdir -p /app/webinars
COPY webinars/ /app/webinars/
RUN mkdir -p /app/icons
COPY icons/ /app/icons/

# Собираем сайт
RUN python create_web.py

FROM nginx:alpine AS runtime

# Чистим дефолт и кладём наш сайт
RUN rm -rf /usr/share/nginx/html/*
COPY --from=builder /app/site/ /usr/share/nginx/html/

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
