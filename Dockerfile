FROM python:3.9-slim AS builder

RUN pip install -U pip
RUN pip install pdm

COPY pyproject.toml pdm.lock /

RUN pdm install --prod --no-self --no-lock --no-editable

FROM python:3.9-slim

WORKDIR /

COPY --from=builder /.venv .venv

# Copy data directory
COPY data data

# Copy function code
COPY src/python app

ENV PATH=.venv/bin:$PATH
ENV PYTHONPATH=app

CMD uvicorn app.api.main:app --host 0.0.0.0 --port 8080