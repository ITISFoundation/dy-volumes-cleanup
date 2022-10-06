FROM python:3.10.7-slim-bullseye

ENV R_CLONE_VERSION="1.58.0"
RUN apt-get update && \
    apt-get install -y curl && \
    apt-get clean
RUN curl --silent --location --remote-name "https://downloads.rclone.org/v${R_CLONE_VERSION}/rclone-v${R_CLONE_VERSION}-linux-amd64.deb" && \
    dpkg --install "rclone-v${R_CLONE_VERSION}-linux-amd64.deb" && \
    rm "rclone-v${R_CLONE_VERSION}-linux-amd64.deb" && \
    rclone --version

COPY . /install

RUN cd /install && pip install . && \
    rm -rf /install && \
    dyvc --help
