import yaml
import string
import random

#COPY test.py ./test.py 
# prepares ./{test_venv} directory for COPY of reqiurements.txt in the user home directory
#COPY requirements.txt ./{test_venv}/requirements.txt

SECRET_PATH='/home/test_user/secret.yaml'
APIKEY_PATH='/home/test_user/api_key'
APITOKEN_PATH='/home/test_user/api_token'
USERSSH_PATH='/home/test_user/.ssh'

# TODO
#
# usunąć niepotrzebne pola z secret i zastąpić je stałymi wartościami


def generate_password(length:int=40):
    return ''.join(random.choices(string.ascii_letters+string.digits, k=length))


class ScriptBuilder:
    def __init__(self, secret:dict=None):
        self.secret=secret
        self.load()
    def load(self):
        self.api_key:str=self.secret['credentials']['api_key']
        self.api_token:str=self.secret['credentials']['api_token']
        with open(APIKEY_PATH, mode='w') as file:
            file.write(self.api_key)
        with open(APITOKEN_PATH, mode='w') as file:
            file.write(self.api_token)

        self.remote_repository_name:str=self.secret["remote_repo"]["remote_repository_name"]
        self.remote_repository_username:str=self.secret["remote_repo"]["remote_repository_username"]
        self.username:str=self.secret["internal_settings"]["username"]
        self.UID:int=self.secret["internal_settings"]["user_id"]
        #self.gitworker_password:str=self.secret["internal_settings"]["user_password"]
        self.test_venv:str=self.secret["internal_settings"]["virtual_environment_name"]
        del self.secret
    def get_sys_setup_script(self):
        remote_repository_name=self.remote_repository_name
        remote_repository_username=self.remote_repository_username
        #username=self.username
        #UID=self.UID
        gitworker_password=generate_password(length=20)
        #test_venv=self.test_venv

        system_setup_script_template=f"""
        #!/bin/bash
        
        # Dodane do DOCKERFILE
        #groupadd sshusers
        #groupadd repousers

        #chown -R test_user /home/test_user/.ssh
        #chgrp -R sshusers /home/test_user/.ssh

        cd /home/test_user/repo
        if [ ! -d ./{remote_repository_name} ]; then \
            mkdir ./{remote_repository_name} \
                #&& chgrp -R repousers ./{remote_repository_name} \
                #&& chmod ug=rw,o=- ./{remote_repository_name}; \
        fi
        
        # THIS SHOULD GO TO THE ORIGINAL DOCKERFILE - dodane
        # add user with groups sshusers (permits the use of ssh-agent via agent.env),
        # repousers (gives recursive read/write access to /var/repo)

        #useradd --uid 1000 -G sshusers,repousers --shell /bin/bash -U -m --home-dir /home/test_user test_user
        #chpasswd test_user:test123


        cp /home/test_user/repo/hash_reg /home/test_user/repo/{remote_repository_name}/hash_reg

        # add hash_reg to the .gitignore
        cd /home/test_user/repo/{remote_repository_name}
        echo "/home/test_user/repo/{remote_repository_name}/hash_reg" >> ./.gitignore
        
        # THIS SHOULD GO THE ORIGINAL DOCKERFILE - dodane
        # prepare the virtual environment in the user directory
        #cd /home/test_user
        #python3 -m venv test_venv

        # THIS SHOULD GO TO THE ORIGINAL DOCKERFILE
        # copy requirements to new test_venv directory
        # mv /tmp/requirements.txt /home/test_user/test_venv/requirements.txt
        # mv /tmp/new_test.py /home/test_user/new_test.py 

        # środowisko wirtualne utworzone na etapie BUILD w DOCKERFILE
        # cd /home/test_user/test_venv
        # source ./bin/activate
        # ./bin/pip3 install -r requirements.txt
        
        cd /home/test_user/repo/{remote_repository_name}
        git clone https://github.com/{remote_repository_username}/{remote_repository_name}.git

        # Nie ma sensu tworzyć agenta na etapie BUILD, bo zaraz zostanie zniszczony
        #eval "$(ssh-agent -s)" | tee agent.env
        #chgrp sshusers agent.env
        #chmod ug=rx agent.env

        echo "System setup completed successfully..."
        """

        with open("/tmp/sys_setup.sh", mode='w') as file:
            file.write(system_setup_script_template)

    def get_gitworker_script(self):
        #test_venv=self.test_venv
        #username=self.username
        
        git_worker_script_template=f"""
        #!/bin/bash
        
        pkill ssh-agent
        ssh-agent -s | tee agent.env
        eval "$(cat agent.env)"
        #chgrp sshusers agent.env
        chmod u=rwx,go-rwx agent.env
        
        source agent.env
        ssh-add {USERSSH_PATH}/id_rsa

        cd /home/test_user/test_venv
        source ./bin/activate
        #./bin/bash tail -F /dev/null &
        ./bin/python3 ../new_test.py
        echo "Gitworker initiated..."
        """

        with open("/home/test_user/initiate_gitworker.sh", mode='w') as file:
            file.write(git_worker_script_template)


with open(SECRET_PATH, mode='rt') as fp:
    secret=yaml.load(fp, yaml.Loader)


s=ScriptBuilder(secret)
#s.prepare_export_script()

# Creates a shell script for preparation of the entire system
s.get_sys_setup_script()

# Creates a shell script for initiating the gitworker
s.get_gitworker_script()


if __name__=='__main__':
    print("End of script!")
