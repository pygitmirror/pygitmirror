# syntax=docker/dockerfile:1

# The image of the page: Alpine with Python, git and the SSH client, and the
# package. Nothing else: no pip, no compiler, no shell tools beyond BusyBox.
ARG ALPINE=3.22

# Installs the package into a folder, with the tools which that needs.
FROM alpine:${ALPINE} AS build
RUN apk add --no-cache python3 py3-pip
WORKDIR /src
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
# The version comes from the git tag, which is not in the build context.
ARG VERSION=0.0.0
RUN SETUPTOOLS_SCM_PRETEND_VERSION="${VERSION}" \
    pip install --no-cache-dir --no-compile --break-system-packages --target /install .

FROM alpine:${ALPINE}
ARG VERSION=0.0.0
LABEL org.opencontainers.image.title="git-mirror" \
      org.opencontainers.image.description="Clone, sync and migrate git repositories between servers" \
      org.opencontainers.image.source="https://github.com/pygitmirror/pygitmirror" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.version="${VERSION}"
# The parts of the standard library which only serve development are removed
# in the same step, so that they never reach a layer.
RUN apk add --no-cache python3 git openssh-client-default ca-certificates \
    && cd /usr/lib/python3.* \
    && rm -rf ensurepip lib2to3 pydoc_data idlelib tkinter turtledemo \
    && adduser -D -H -u 10001 mirror \
    && mkdir /data \
    && chown mirror:mirror /data
COPY --from=build /install /opt/git-mirror
# git and ssh look for their settings in HOME, which must exist and may be empty.
ENV PYTHONPATH=/opt/git-mirror \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOME=/tmp
USER 10001
# The local copies of the repositories. Mount a volume here to keep them.
VOLUME /data
EXPOSE 47417
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
    CMD wget -q -O /dev/null http://127.0.0.1:47417/healthz || exit 1
ENTRYPOINT ["python3", "-m", "pygitmirror"]
# Inside a container the page listens on every address; publish the port to
# the local machine only, as the documentation shows.
CMD ["serve", "--host", "0.0.0.0", "--sync-path", "/data"]
