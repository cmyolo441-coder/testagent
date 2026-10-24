# Cline (headless) with the gwarden.su gateway — cloud-ready image
#
# Build:  docker build -t cline-gwarden cloud
# Run:    docker run --rm -e GWARDEN_API_KEY=... -e CLINE_TASK="..." \
#           -v "$PWD:/workspace" cline-gwarden
FROM node:22-slim

RUN apt-get update \
  && apt-get install -y --no-install-recommends git ca-certificates curl jq \
  && rm -rf /var/lib/apt/lists/*

# Cline CLI = the same agent that runs in the cloud / IDE
RUN npm install -g cline@3.0.73

COPY run-cline-cloud.sh /usr/local/bin/run-cline-cloud.sh
RUN chmod +x /usr/local/bin/run-cline-cloud.sh

ENV CLINE_BASE_URL=https://gwarden.su/v1 \
    CLINE_MODEL=gemini-4-argon \
    CLINE_TIMEOUT=1800 \
    CLINE_AUTO_APPROVE=true \
    CLINE_CWD=/workspace

WORKDIR /workspace
ENTRYPOINT ["/usr/local/bin/run-cline-cloud.sh"]
