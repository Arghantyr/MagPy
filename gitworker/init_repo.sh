#!/bin/bash

eval "$(ssh-agent -s)"
ssh-add /home/test_user/.ssh/id_rsa

cd /var/repo/WorldAnvil-repo
git init
git remote add origin https://github.com/Arghantyr/WorldAnvil-repo.git
git pull
git checkout main -f
git branch --set-upstream-to origin/main
