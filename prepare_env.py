import yaml

#echo UID="$(id -u)" > ./.env
#echo GID="$(id -g)" >> ./.env
#echo USERNAME=gitworker >> ./.env
#echo REMOTE_REPO_USERNAME=Arghantyr >> .env
#echo REMOTE_REPO_NAME=WorldAnvil-repo >> .env
#echo REMOTE_REPO_SSH_URL='git@github.com:Arghantyr/WorldAnvil-repo.git' >> .env
#cat ./.env

with open('./secret.yaml', mode='r') as file:
    secret_yaml=yaml.load(file, yaml.Loader)

USERNAME='gitworker'
REMOTE_REPO_SSH_URL=secret_yaml['remote_repo']['remote_repository_url']
REMOTE_REPO_NAME=REMOTE_REPO_SSH_URL.rstrip('.git').split('/')[-1]

env_list=[
        f"USERNAME='{USERNAME}'",
        f"REMOTE_REPO_SSH_URL='{REMOTE_REPO_SSH_URL}'",
        f"REMOTE_REPO_NAME='{REMOTE_REPO_NAME}'"
        ]

with open('./.env', mode='a') as env_file:
    env_file.write('\n'.join(env_list))
