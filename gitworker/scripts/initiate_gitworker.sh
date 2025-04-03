#!/bin/bash

pkill ssh-agent; rm agent.env
touch agent.env
chmod u=rwx,go=-rwx agent.env
ssh-agent -s | tee agent.env
eval "$(cat agent.env)"

source agent.env
ssh-add /home/gitworker/.ssh/id_rsa

cd /home/gitworker/gitworker-venv
source ./bin/activate

./bin/python3 /opt/gitworker/scripts/gitworker.py

echo "Gitworker initiated..."
