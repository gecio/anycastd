FROM ubuntu:noble
ARG VERSION

LABEL org.opencontainers.image.title="anycastd"
LABEL org.opencontainers.image.description="Manage anycasted services based on health checks."
LABEL org.opencontainers.image.version=${VERSION}
LABEL org.opencontainers.image.vendor="WIIT AG <openstack@wiit.cloud>"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.documentation=${GITHUB_SERVER_URL}/${GITHUB_REPOSITORY}
LABEL org.opencontainers.image.source=${GITHUB_SERVER_URL}/${GITHUB_REPOSITORY}
LABEL org.opencontainers.image.url=${GITHUB_SERVER_URL}/${GITHUB_REPOSITORY}

ENV TZ=Europe/Berlin
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install --no-install-recommends -y \
  python3 \
  python3-venv \
  frr \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY anycastd-${VERSION}-py3-none-any.whl .
RUN python3 -m venv venv \
  && venv/bin/python3 -m pip install anycastd-${VERSION}-py3-none-any.whl

ENV LOG_LEVEL=info
ENV LOG_FORMAT=json

ENTRYPOINT ["venv/bin/python3", "-m", "anycastd", "run"]

