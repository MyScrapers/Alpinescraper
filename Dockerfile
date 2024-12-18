# Ensure consistent casing for `FROM` and `as` keywords
FROM python:3.11 AS base

ENV PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100

# need to be root in order to install packages
USER 0

RUN apt-get update && apt-get upgrade -y && \
    apt-get clean

# install necessary system dependencies here using `apt-get install -y`
# for installable packages, see: https://hub.docker.com/_/python

FROM base AS builder

ENV VENV_PATH="poetry_venv" \
    POETRY_VERSION="1.8.0" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    PATH="/root/.local/bin:$PATH"

RUN curl -sSL https://install.python-poetry.org | python -

WORKDIR /app

# Initialize environment with packages
COPY README.md pyproject.toml poetry.lock ./
RUN poetry env use 3.11 && \
    poetry install --without dev --no-interaction --no-ansi --no-root

# Add project source code
COPY src/ ./src/
RUN poetry build -f wheel
RUN poetry run pip install dist/*.whl

FROM base AS final

# switch back to a non-root user for executing
USER 1001

ENV PATH="/app/.venv/bin:$PATH"
COPY --from=builder /app/.venv /app/.venv

# Default command. Can be overridden using docker run <image> <command>
CMD entrypoint
