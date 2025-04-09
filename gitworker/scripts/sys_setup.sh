#!/bin/bash

echo 'Initiating sys_setup.sh'
cd /home/gitworker/repo

echo "Preparing for cloning of $REMOTE_REPO_SSH_URL to $REMOTE_REPOSITORY_NAME"
git clone $REMOTE_REPO_SSH_URL
cd $REMOTE_REPOSITORY_NAME

if [ ! -f ./track_hash_reg ]; then
	cp ../hash_reg ./track_hash_reg
fi

if [ ! -f ./beacon_hash_reg ]; then
	cp ../hash_reg ./beacon_hash_reg
fi

if [ ! -f ./file_index ]; then
	cp ../file_index ./file_index
fi




git remote add github-repo $REMOTE_REPO_SSH_URL
git branch -M main
git push -u github-repo main

echo "System setup completed successfully..."
