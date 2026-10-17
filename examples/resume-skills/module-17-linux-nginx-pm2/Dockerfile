ARG NODE_IMAGE=node:22-bookworm-slim
FROM ${NODE_IMAGE}
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx openssl python3 procps iproute2 ca-certificates \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /opt/fixture
COPY package.json package-lock.json ./
RUN npm ci --omit=dev --ignore-scripts
ENV PATH="/opt/fixture/node_modules/.bin:${PATH}"
COPY app.cjs ecosystem.config.cjs nginx.conf verify_linux.py ./
RUN mkdir -p /run/m17 /run/m17/tls /run/m17/static /run/m17/logs /run/m17/pm2 \
    && printf 'm17-static-ok\n' > /run/m17/static/index.txt \
    && chown -R node:node /run/m17/logs /run/m17/pm2
# A test harness shares one Linux network namespace to model a single VM.
# This is not a production multi-service container entrypoint.
CMD ["sleep", "infinity"]
