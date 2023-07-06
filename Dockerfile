FROM python:3.10-slim-bullseye as base

# ----- сборщик -----
FROM base as builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# установка системных зависимостей
RUN apt-get update && apt-get install --no-install-recommends -y \
  libpq-dev

# установка зависимостей проекта
RUN pip install --upgrade pip

RUN pip install poetry
COPY ./pyproject.toml .
COPY ./poetry.lock .
RUN poetry export --output requirements.txt

RUN pip wheel --no-cache-dir --no-deps --wheel-dir /wheels -r requirements.txt
RUN pip install -r requirements.txt


# ----- финальный образ -----
FROM base

WORKDIR /app

# netcat для проверки готовности postgresql
RUN apt-get update && apt-get install --no-install-recommends -y \
  netcat

# копируем зависимости
COPY --from=builder /wheels /wheels
RUN pip install --no-cache /wheels/*

# копируем код проекта
COPY . .

# запускаем entrypoint.sh
RUN chmod +x ./entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]