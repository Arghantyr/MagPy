import os
import json
import time
from datetime import datetime
from  pywaclient.api import BoromirApiClient
import git
from hashlib import sha1

SCRIPT_NAME='MAUG-stack-test'
REPO_URL=''
VERSION='0.1'
GRANULARITY=0
DEV_PLAYGROUND_WORLD_ID='6a05ed1a-412b-4cf2-88d4-c86736ee5d67'
REMOTE_REPO_URL='git@github.com:Arghantyr/WorldAnvil-repo.git'
SSH_ID_FILE='/home/test_user/.ssh/id_rsa'
REPO_PATH='/home/test_user/repo'
QUIT_AT='2025-03-18 21:00'
APIKEY_PATH='/home/test_user/api_key'
APITOKEN_PATH='/home/test_user/api_token'


remote_repo_name=REMOTE_REPO_URL.split('/')[-1].split('.')[0]



# TODO
# if the remote repository does not exist within the /repo directory
# add it to the directory. This should be the default directory that all future
# changes will be committed and pushed to as UUID-named objects
#
#
# Be sure to:
# - generate the ssh key pair through ssh-keygen
# - add the public key, e.g., id_rsa.pub to the GitHub SSH keys (use a descriptive name)
# - start the ssh-agent (eval "$(ssh-agent -s)")
# - add the ssh private key to the agent, e.g., ssh-add .ssh/id_rsa
#
# Deal with all the changes in the remote repository (which one has the fullest track of changes?)
# save changes to the remote repo by using 'git push'
#
# Remember to target the specific branch of the repository.
# Remember to set the commit/push users/Authors correctly, e.g., MAUG-gh-worker


def create_new_repo():
    print("===========\nFUNC: create_new_repo")
    if remote_repo_name not in [i for i in os.listdir(f'{REPO_PATH}/') if os.path.isdir(f'{REPO_PATH}/{i}')]:
        #with open('/repo/hash_reg', mode='wt') as file:
        #    json.dumps('{}', file)
        return git.Repo.init(f'{REPO_PATH}/{remote_repo_name}')
    else:
        return git.Repo(f'{REPO_PATH}/{remote_repo_name}')

def link_to_remote_repo(repo):
    print("===========\nFUNC: link_to_remote_repo")
    try:
        if not repo.remote("github-repo").exists():
            repo.create_remote("github-repo", f"{REMOTE_REPO_URL}")
    except ValueError:
        repo.create_remote("github-repo", f"{REMOTE_REPO_URL}")
    except Exception as e:
        raise Exception(f'{e}')

def get_most_recent_head(repo):
    print("===========\nFUNC: get_most_recent_head")
    try:
        git_cmd = repo.git()
        print(f"{git_cmd}")
        for_each_ref = git_cmd.for_each_ref("--sort=-committerdate", "refs/heads/", "--format='%(refname:short)'")
        print(f"{for_each_ref}")
        return for_each_ref
    except Exception as e:
        raise Exception(f"{e}")

def get_uuid_objhash(uuid, content):
    print("===========\nFUNC: get_uuid_objhash")
    obj_hash=sha1(json.dumps(content, ensure_ascii=False).encode('utf-8')).hexdigest()
    return uuid, obj_hash

# TODO
# Replace the initial empty hash_reg and its checks
# with an initialized hash_reg with entry for empty object:
# '00000000-0000-0000-0000-000000000000': sha1('{}')
# All problems with checks vanish with that single addition.
def init_hashreg(uuid:str, content):
    print("FUNC: init_hashreg")
    uuid, obj_hash = get_uuid_objhash(uuid, content)
    if 'hash_reg' not in [i for i in os.listdir(f'{REPO_PATH}/{remote_repo_name}') if os.path.isfile(f'{REPO_PATH}/{remote_repo_name}/{i}')]:
        print(f"hash_reg not found. Creating new one.")
        hash_reg={uuid: obj_hash}
        with open(f'{REPO_PATH}/{remote_repo_name}/hash_reg', mode='wt') as file:
            json.dump(hash_reg, file)
    else:
        if os.path.getsize(f'{REPO_PATH}/{remote_repo_name}/hash_reg') == 0:
            print(f"hash_reg found but with size 0: {os.path.getsize('{REPO_PATH}/{remote_repo_name}/hash_reg')}. Updating...")
            hash_reg={uuid: obj_hash}
            with open(f'{REPO_PATH}/{remote_repo_name}/hash_reg', mode='wt') as file:
                json.dump(hash_reg, file)
        else:
            print(f"hash_reg found but with file size != 0. Proceeding forward...")

def addcommit_changes(uuid, repo, msg):
    print("FUNC: addcommit_changes")
    try:
        repo.index.add([uuid])
        repo.index.commit(msg)
        return 0
    except Exception as e:
        raise Exception(f'{e}')

def update_file(uuid, content, repo, msg):
    print("FUNC: update_file")
    try:
        with open(f'{REPO_PATH}/{remote_repo_name}/hash_reg', mode='rt') as file:
            hash_reg=json.load(file)
        _, obj_hash=get_uuid_objhash(uuid, content)
        cond=( obj_hash != hash_reg.get(uuid) )
        if cond:
            print(f"Condition met: {cond}.\nobj_hash: {obj_hash}\nstored_hash: {hash_reg.get(uuid)}")
            with open(f'{REPO_PATH}/{remote_repo_name}/{uuid}', mode='wt') as file:
                json.dump(content, file)
            hash_reg[uuid]=obj_hash
            with open(f'{REPO_PATH}/{remote_repo_name}/hash_reg', mode='wt') as file:
                json.dump(hash_reg, file)
            addcommit_changes(uuid, repo, msg)
        else:
            print(f"No change detected for object {uuid}")
    except Exception as e:
        raise Exception(f'{e}')
# TODO
# Cannot authenticate through SSH
def push_to_remote_repo(repo):
    print("===========\nFUNC: push_to_remote_repo")
    remote=repo.remote('github-repo')
#    try:
#        # Set up a local tracking branch of a remote branch.
#        repo.create_head("master", remote.refs.master)  # Create local branch "master" from remote "master".
#    except AttributeError:
#        raise Exception(f"github-repo/master branch not found")
#    repo.heads.master.set_tracking_branch(remote.refs.master)  # Set local "master" to track remote "master.
    head_name=get_most_recent_head(repo)
    repo.heads[head_name].checkout()  # Check out local "main" to working tree.
    with repo.git.custom_environment(GIT_SSH_COMMAND=f'ssh -i {SSH_ID_FILE}'):
        remote.push()

# TODO
#
# Podmienić na wykorzystanie secret.yaml do wyciągnięcia pary key/token
with open(APIKEY_PATH, mode='r') as apikey:
    WA_APPLICATION_KEY=apikey.read().rstrip('\n')

with open(APITOKEN_PATH, mode='r') as apitoken:
    WA_AUTH_TOKEN=apitoken.read().rstrip('\n')

client = BoromirApiClient(
    SCRIPT_NAME,
    REPO_URL,
    VERSION,
    WA_APPLICATION_KEY,
    WA_AUTH_TOKEN
)

# get your own user id. It is not possible to discover the user ids of other users via the API.
authenticated_user = client.user.identity()

# get the references to all the worlds on your account.
worlds = [world['id'] for world in client.user.worlds(authenticated_user['id'])]
"""
for world in worlds:
    print(f'Fetching world with ID: {world}')
    world_object=client.world.get(world, GRANULARITY)
    print(f'world: {json.dumps(world_object, indent=2)}')
    time.sleep(5)
"""
repo=create_new_repo()
link_to_remote_repo(repo)

while datetime.now() < datetime.strptime(QUIT_AT, '%Y-%m-%d %H:%M'):
    dev_playground_world=client.world.get(DEV_PLAYGROUND_WORLD_ID, GRANULARITY)
    #print(f'Fetching world with id: {DEV_PLAYGROUND_WORLD_ID}\n\n{json.dumps(dev_playground_world, indent=2)}')
    
    uuid=DEV_PLAYGROUND_WORLD_ID
    content=dev_playground_world
    init_hashreg(uuid, content)

    update_file(uuid, content, repo, msg="World update")
    push_to_remote_repo(repo)

    time.sleep(60)

if __name__=='__main__':
    print("End of script.")
