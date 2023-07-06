FROM python:3.10-slim-bullseye as base

# ----- builder -----
FROM base as builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install package dependenices
RUN apt-get update && apt-get install --no-install-recommends -y \
  libpq-dev

# install project dependencies
RUN pip install --upgrade pip

RUN pip install poetry
COPY ./pyproject.toml .
COPY ./poetry.lock .
RUN poetry export --output requirements.txt

RUN pip wheel --no-cache-dir --no-deps --wheel-dir /wheels -r requirements.txt
RUN pip install -r requirements.txt


# ----- final -----
FROM base

WORKDIR /app

# netcat to check for postgres readiness
RUN apt-get update && apt-get install --no-install-recommends -y \
  netcat

# copy dependencies
COPY --from=builder /wheels /wheels
RUN pip install --no-cache /wheels/*

# copy project
COPY . .

# run entrypoint.sh
RUN chmod +x ./entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]