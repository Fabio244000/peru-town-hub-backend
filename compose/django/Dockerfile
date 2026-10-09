FROM python:3.12-slim-bookworm AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENTRYPOINT ["/app/compose/django/entrypoint.sh"]


FROM base AS local

COPY requirements/ /app/requirements/
RUN pip install -r requirements/local.txt

COPY . /app/


FROM base AS stage

RUN useradd --create-home --uid 1000 app

COPY requirements/ /app/requirements/
RUN pip install -r requirements/stage.txt

COPY --chown=app:app . /app/

# collectstatic only imports settings; these placeholders never reach runtime.
RUN DJANGO_SETTINGS_MODULE=config.settings.stage \
    DJANGO_SECRET_KEY=collectstatic-placeholder \
    POSTGRES_DB=placeholder POSTGRES_USER=placeholder \
    POSTGRES_PASSWORD=placeholder POSTGRES_HOST=placeholder \
    POSTGRES_PORT=5432 \
    python manage.py collectstatic --noinput \
    && chown -R app:app /app/staticfiles

USER app

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--access-logfile", "-"]
