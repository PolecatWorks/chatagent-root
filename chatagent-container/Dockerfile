# Description: Dockerfile for building the k8s-python container

FROM python:3.13.0-slim-bookworm AS base

FROM base AS build

# Entrypoint is here in case we want to run the build layer as a standalone container
ENTRYPOINT ["/bin/sh"]

# Install some build tools for binary style packages
RUN apt-get update
RUN apt-get update --fix-missing && apt-get install -y --fix-missing \
    build-essential \
    gcc \
    g++ \
    cmake \
    autoconf && \
    rm -rf /var/lib/apt/lists/* && \
    mkdir /install

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY poetry.lock pyproject.toml README.md ./
# TODO:: Consider to make a build and stage system here that would allow to install dependencies ONLY so we can speed up the package installation.
# BUT not required for now. Just a nice to have.
COPY chatbot chatbot
RUN pip3 install .


# Test stage - building on top of the build stage to reuse the built application
FROM build AS test
RUN pip3 install poetry
RUN poetry install --with dev
COPY pyproject.toml poetry.lock ./
COPY tests ./tests
RUN poetry run pytest tests/ && touch /app/tests/.test_success

FROM base AS publish
LABEL org.opencontainers.image.title="Chatbot root"
LABEL org.opencontainers.image.description="Chatbot root for Azure chatbot integration"
LABEL org.opencontainers.image.authors="Ben Greene <BenJGreene@gmail.com>"
LABEL org.opencontainers.image.source="https://github.com/polecatworks/chatbot_root"
LABEL org.opencontainers.image.created="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
EXPOSE 8080 8079
COPY --from=test /app/tests/.test_success /app/tests/.test_success
COPY --from=build /opt/venv /opt/venv

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

ENTRYPOINT ["chatbot"]
