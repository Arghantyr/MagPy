#!/bin/bash


chmod u=rwx,go=rx /opt/gitworker/scripts/sys_setup.sh
/bin/bash /opt/gitworker/scripts/sys_setup.sh


chmod u=rwx,go=rx /opt/gitworker/scripts/initiate_gitworker.sh
/bin/bash /opt/gitworker/scripts/initiate_gitworker.sh
