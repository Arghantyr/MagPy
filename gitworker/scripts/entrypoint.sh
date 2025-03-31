#!/bin/bash


chmod u=rwx,go=rx /opt/$USERNAME/scripts/sys_setup.sh
/bin/bash /opt/$USERNAME/scripts/sys_setup.sh


chmod u=rwx,go=rx /opt/$USERNAME/scripts/initiate_gitworker.sh
/bin/bash /opt/$USERNAME/scripts/initiate_gitworker.sh
