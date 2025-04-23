from gitworker.scripts.Secrets import WorldAnvilSecrets

wa_secrets=WorldAnvilSecrets('./secret.yaml')

REMOTE_REPO_SSH_URL=wa_secrets.repo_ssh_url
REMOTE_REPO_NAME=REMOTE_REPO_SSH_URL.rstrip('.git').split('/')[-1]

env_list=[
        f"REMOTE_REPO_SSH_URL='{REMOTE_REPO_SSH_URL}'",
        f"REMOTE_REPO_NAME='{REMOTE_REPO_NAME}'"
        ]

with open('./.env', mode='a') as env_file:
    env_file.write('\n'.join(env_list))
