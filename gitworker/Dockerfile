FROM ubuntu:24.10
RUN touch /var/mail/ubuntu && chown ubuntu /var/mail/ubuntu && userdel -r ubuntu

SHELL ["/bin/bash", "-c"]

ARG USERID
ARG GROUPID
ARG USERNAME
ARG REMOTE_REPOSITORY_USERNAME
ARG RMEOTE_REPOSITORY_NAME
#ARG REPOGROUP=repousers
ARG VENV=test_venv
#RUN /noexisting


#RUN echo $USERID
#RUN echo $GROUPID

RUN apt-get update && \
    apt-get install -y python3.12 python3-pip && apt-get update && \
    apt-get install -y python3-venv git python3-yaml && apt-get update

#RUN groupadd sshusers
#RUN groupadd --gid $GROUPID $REPOGROUP

# removed sshusers (the user added has the same UID:GID as user executing docker-compose)
# removed -G $REPOGROUP to make all files belong to the $USERNAME
RUN useradd --uid $USERID --shell /bin/bash -U -m --home-dir /home/$USERNAME $USERNAME

#RUN mkdir /home/test_user/repo
# TODO
#
# Trzeba będzie przemyśleć, bo domyślnie uprawnienia są nadawane jak dla uruchamiającego Daemona, czyli root
# Jedna z opcji to ustawienie UID:GID takiego jak na hoście, tj.:
# https://stackoverflow.com/questions/40462189/docker-compose-set-user-and-group-on-mounted-volume
#RUN mkdir /home/$USERNAME/repo
#RUN chgrp -R $REPOGROUP /home/$USERNAME/repo

USER $USERNAME

# TODO
#
# Uporządkować poniższe skrypty do wspólnego folderu
# /tmp/scripts:
# - prepare_sh_arg_scripts.py
# - entrypoint.sh
#
# /opt/gitworker/scripts:
#  - new_test.py
#
# /opt/gitworker/config
# - secret.yaml

# Nadać kopiowanym plikom odpowiednie uprawnienia przez --chown=$USERNAME
WORKDIR /home/$USERNAME
RUN python3 -m venv $VENV
COPY --chown=$USERNAME ./requirements.txt ./$VENV/requirements.txt
RUN source ./$VENV/bin/activate && \
    ./$VENV/bin/pip3 install -r ./$VENV/requirements.txt

COPY --chown=$USERNAME ./secret.yaml ./secret.yaml
#COPY --chown=test_user:repousers ./hash_reg /var/repo/hash_reg
COPY --chown=$USERNAME ./prepare_sh_arg_scripts.py /tmp/prepare_sh_arg_scripts.py
COPY --chown=$USERNAME ./new_test.py ./new_test.py
COPY --chown=$USERNAME ./entrypoint.sh /tmp/entrypoint.sh
RUN chmod +x /tmp/entrypoint.sh && /tmp/entrypoint.sh

#TODO
# Należałoby zrobić inny skrypt niż entrypoint.sh albo dodać nna jego końcu skasowanie plików z hosta po tym
# jak dokonał wszystkich niezbędnych zmian.
RUN rm -r /tmp/*
