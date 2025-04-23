FROM ubuntu:24.10
RUN touch /var/mail/ubuntu && chown ubuntu /var/mail/ubuntu && userdel -r ubuntu

SHELL ["/bin/bash", "-c"]

ARG USERID
ARG GROUPID
ARG REMOTE_REPOSITORY_USERNAME
ARG REMOTE_REPOSITORY_NAME
ARG REMOTE_REPO_SSH_URL

ENV REMOTE_REPOSITORY_NAME=$REMOTE_REPOSITORY_NAME
ENV REMOTE_REPO_SSH_URL=$REMOTE_REPO_SSH_URL

RUN useradd --uid $USERID --shell /bin/bash -U -m --home-dir /home/gitworker gitworker && \
    apt-get update && \
    apt-get install -y python3.12 python3-pip && apt-get update && \
    apt-get install -y python3-venv git python3-yaml && apt-get update && \
    mkdir /opt/gitworker && chown gitworker /opt/gitworker


USER gitworker

COPY --chown=gitworker ./hash_reg /home/gitworker/repo/hash_reg

WORKDIR /home/gitworker
RUN python3 -m venv gitworker-venv
COPY --chown=gitworker ./requirements.txt ./gitworker-venv/requirements.txt
RUN source ./gitworker-venv/bin/activate && \
    ./gitworker-venv/bin/pip3 install -r ./gitworker-venv/requirements.txt

COPY --chown=gitworker ./scripts/sys_setup.sh /opt/gitworker/scripts/sys_setup.sh
COPY --chown=gitworker ./scripts/Utils.py /opt/gitworker/scripts/Utils.py
COPY --chown=gitworker ./scripts/Schemas.py /opt/gitworker/scripts/Schemas.py
COPY --chown=gitworker ./scripts/Secrets.py /opt/gitworker/scripts/Secrets.py
COPY --chown=gitworker ./scripts/BackendUtils.py /opt/gitworker/scripts/BackendUtils.py
COPY --chown=gitworker ./scripts/APIClients.py /opt/gitworker/scripts/APIClients.py
COPY --chown=gitworker ./scripts/APIUtils.py /opt/gitworker/scripts/APIUtils.py
COPY --chown=gitworker ./scripts/gitworker.py /opt/gitworker/scripts/gitworker.py
COPY --chown=gitworker ./scripts/initiate_gitworker.sh /opt/gitworker/scripts/initiate_gitworker.sh
COPY --chown=gitworker ./scripts/entrypoint.sh /opt/gitworker/scripts/entrypoint.sh

WORKDIR /opt/gitworker/scripts
RUN chmod +x ./entrypoint.sh
ENTRYPOINT ./entrypoint.sh
