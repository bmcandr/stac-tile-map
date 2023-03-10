FROM python:3.9-slim as requirements-stage

WORKDIR /tmp

RUN pip install poetry

COPY ./pyproject.toml ./poetry.lock* /tmp/

RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

FROM python:3.9-slim as install

WORKDIR /

COPY --from=requirements-stage /tmp/requirements.txt requirements.txt

RUN  pip3 install --no-cache-dir --upgrade -r requirements.txt

# Copy data directory
COPY data data

# Copy function code
COPY src/python app

ENV PYTHONPATH=app

CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8080"]