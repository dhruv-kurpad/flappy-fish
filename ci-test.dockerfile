# Local GitHub Actions test environment (mimics ubuntu-latest + az + docker)
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl git jq bash \
    && rm -rf /var/lib/apt/lists/*

# Azure CLI
RUN curl -sL https://aka.ms/InstallAzureCLIDeb | bash

# Docker CLI + buildx (uses host Docker via /var/run/docker.sock)
RUN install -m 0755 -d /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc \
    && chmod a+r /etc/apt/keyrings/docker.asc \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu noble stable" > /etc/apt/sources.list.d/docker.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends docker-ce-cli docker-buildx-plugin \
    && rm -rf /var/lib/apt/lists/*

# Use buildx as default builder
ENV DOCKER_CLI_EXPERIMENTAL=enabled

WORKDIR /workspace

COPY scripts/test-github-deploy.sh /usr/local/bin/test-github-deploy.sh
RUN chmod +x /usr/local/bin/test-github-deploy.sh

CMD ["bash"]
