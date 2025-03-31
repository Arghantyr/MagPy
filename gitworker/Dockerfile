FROM ubuntu:24.10
RUN touch /var/mail/ubuntu && chown ubuntu /var/mail/ubuntu && userdel -r ubuntu

SHELL ["/bin/bash", "-c"]

ARG USERID
ARG GROUPID
ARG USERNAME
ARG REMOTE_REPOSITORY_USERNAME
ARG REMOTE_REPOSITORY_NAME
ARG REMOTE_REPO_SSH_URL

ENV REMOTE_REPOSITORY_NAME=$REMOTE_REPOSITORY_NAME
ENV REMOTE_REPO_SSH_URL=$REMOTE_REPO_SSH_URL
ENV USERNAME=$USERNAME

RUN useradd --uid $USERID --shell /bin/bash -U -m --home-dir /home/$USERNAME $USERNAME && \
    apt-get update && \
    apt-get install -y python3.12 python3-pip && apt-get update && \
    apt-get install -y python3-venv git python3-yaml && apt-get update && \
    mkdir /opt/$USERNAME && chown $USERNAME /opt/$USERNAME


USER $USERNAME

COPY --chown=$USERNAME ./hash_reg /home/$USERNAME/repo/hash_reg

WORKDIR /home/$USERNAME
RUN python3 -m venv gitworker-venv
COPY --chown=$USERNAME ./requirements.txt ./gitworker-venv/requirements.txt
RUN source ./gitworker-venv/bin/activate && \
    ./gitworker-venv/bin/pip3 install -r ./gitworker-venv/requirements.txt

COPY --chown=$USERNAME ./scripts/sys_setup.sh /opt/$USERNAME/scripts/sys_setup.sh
COPY --chown=$USERNAME ./scripts/gitworker.py /opt/$USERNAME/scripts/gitworker.py
COPY --chown=$USERNAME ./scripts/initiate_gitworker.sh /opt/$USERNAME/scripts/initiate_gitworker.sh
COPY --chown=$USERNAME ./scripts/entrypoint.sh /opt/$USERNAME/scripts/entrypoint.sh

WORKDIR /opt/$USERNAME/scripts
RUN chmod +x ./entrypoint.sh
ENTRYPOINT ./entrypoint.sh
