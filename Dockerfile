FROM ubuntu:noble

LABEL org.opencontainers.image.title="anycastd"
LABEL org.opencontainers.image.vendor="WIIT AG <openstack@wiit.cloud>"

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install --no-install-recommends -y \
  python3 \
  python3-venv \
  frr \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY anycastd-*.whl .
RUN python3 -m venv venv \
  && venv/bin/python3 -m pip install anycastd-*.whl

ENV LOG_LEVEL=info
ENV LOG_FORMAT=json

ENTRYPOINT ["venv/bin/python3", "-m", "anycastd", "run"]
