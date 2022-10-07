FROM python:3.10.7-slim-bullseye

RUN apt-get update && \
    apt-get install -y curl && \
    apt-get clean

COPY . /install
RUN cd /install && \
    # install package
    pip install . && \
    # install rclone
    cd ci/ && \
    ./install_rclone.bash && \
    # clenup
    rm -rf /install && \
    # test install
    dyvc --help
