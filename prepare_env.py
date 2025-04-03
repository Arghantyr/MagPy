import yaml

with open('./secret.yaml', mode='r') as file:
    secret_yaml=yaml.load(file, yaml.Loader)

REMOTE_REPO_SSH_URL=secret_yaml['remote_repo']['remote_repository_url']
REMOTE_REPO_NAME=REMOTE_REPO_SSH_URL.rstrip('.git').split('/')[-1]

env_list=[
        f"REMOTE_REPO_SSH_URL='{REMOTE_REPO_SSH_URL}'",
        f"REMOTE_REPO_NAME='{REMOTE_REPO_NAME}'"
        ]

with open('./.env', mode='a') as env_file:
    env_file.write('\n'.join(env_list))
