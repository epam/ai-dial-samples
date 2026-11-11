FROM alpine:3.20

# Installed at build time, so later starts work offline.
RUN apk add --no-cache curl jq

COPY apply-config.sh /usr/local/bin/apply-config.sh
COPY model-provider-migration.jq /usr/local/share/model-provider-migration.jq

# Compose mounts the repository's core/ and core-data/ folders here.
WORKDIR /dial
ENTRYPOINT ["sh", "/usr/local/bin/apply-config.sh"]
