#!/bin/bash

pkill ssh-agent; rm agent.env
touch agent.env
chmod u=rwx,go=-rwx agent.env
ssh-agent -s | tee agent.env
eval "$(cat agent.env)"

source agent.env
ssh-add /home/$USERNAME/.ssh/id_rsa

cd /home/$USERNAME/gitworker-venv
source ./bin/activate

./bin/python3 /opt/$USERNAME/scripts/gitworker.py

echo "Gitworker initiated..."
