#!/bin/bash


#apt-get update
#apt-get install -y python3.12 python3-pip && apt-get update
#apt-get install -y python3-venv git python3-yaml && apt-get update

# TODO
#
# use chroot to jail the user in /home/user once the are created

# initiate prepare_shell_scripts_py to create the scripts: sys_setup.sh and initiate_gitworker.sh

chmod u=rwx,go=rx /tmp/prepare_sh_arg_scripts.py
python3 /tmp/prepare_sh_arg_scripts.py
#ls -la /tmp
# copy files to the proper directories
#cd /home/test_user
chmod u=rwx,go=rx /tmp/sys_setup.sh
/tmp/sys_setup.sh

# execute initiate_gitworker.sh
#mv /tmp/initiate_gitworker.sh /home/test_user/initiate_gitworker.sh
chmod u=rwx,go=rx /home/test_user/initiate_gitworker.sh
#/bin/bash /home/test_user/initiate_gitworker.sh
